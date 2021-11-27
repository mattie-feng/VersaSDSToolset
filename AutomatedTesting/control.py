import sys
import re
import utils
import action
import gevent
import threading
import time
from ssh_authorized import SSHAuthorizeNoMGN
import ctypes
import inspect
import multiprocessing


def run_multiprocessing_test_quorum(stor_a, stor_b, ip_a, conn_list, device, device_name, resource):
    dd_a = action.RWData(conn_list[0])
    dd_b = action.RWData(conn_list[1])
    # mp1 = multiprocessing.Process(target=action.dd_operation,
    #                               args=(device_name, conn_list[0]))
    mp1 = multiprocessing.Process(target=dd_a.dd_operation,
                                  args=(device_name,))
    mp2 = multiprocessing.Process(target=ip_a.down_device, args=(device,))
    # mp3 = multiprocessing.Process(target=action.dd_operation,
    #                               args=(device_name, conn_list[1]))
    mp3 = multiprocessing.Process(target=dd_b.dd_operation,
                                  args=(device_name,))
    mp4 = multiprocessing.Process(target=stor_a.secondary_drbd, args=(resource,))
    print(multiprocessing.active_children())
    mp1.start()
    time.sleep(20)
    mp2.start()
    mp2.join()
    print(multiprocessing.active_children())
    time.sleep(3)
    stor_b.primary_drbd(resource)
    time.sleep(3)
    mp3.start()
    time.sleep(10)
    mp4.start()
    mp4.join()
    print(multiprocessing.active_children())
    mp1.join()
    print(multiprocessing.active_children())
    time.sleep(10)
    if mp3.is_alive():
        utils.prt_log(conn_list[1], f"Stop dd operation", 0)
        mp3.terminate()
        print(multiprocessing.active_children())
    else:
        print(multiprocessing.active_children())
        utils.prt_log(conn_list[1], f"dd operation had been finished", 1)
    mp3.join()
    print(multiprocessing.active_children())


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        print("invalid thread id")
        # raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        print("PyThreadState_SetAsyncExc failed")
        # raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def get_crm_status_by_type(result, resource, type):
    if result:
        if type in ['IPaddr2', 'iSCSITarget', 'portblock', 'iSCSILogicalUnit']:
            re_string = f'{resource}\s*\(ocf::heartbeat:{type}\):\s*(\w*)\s*(\w*)?'
            re_result = utils.re_search(re_string, result, "groups")
            return re_result
        if type == 'FailedActions':
            re_string = "Failed Actions:\s*.*\*\s\w*\son\s(\S*)\s'(.*)'\s.*exitreason='(.*)',\s*.*"
            re_result = utils.re_search(re_string, result, "group")
            return re_result


class Connect(object):
    """
    通过ssh连接节点，生成连接对象的列表
    """
    list_vplx_ssh = []

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            Connect._instance = super().__new__(cls)
            Connect._instance.config = args[0]
            Connect.get_ssh_conn(Connect._instance)
        return Connect._instance

    def get_ssh_conn(self):
        ssh = SSHAuthorizeNoMGN()
        local_ip = utils.get_host_ip()
        vplx_configs = self.config.get_vplx_configs()
        username = "root"
        for vplx_config in vplx_configs:
            if "username" in vplx_config.keys():
                if vplx_config['username'] is not None:
                    username = vplx_config['username']
            if local_ip == vplx_config['public_ip']:
                self.list_vplx_ssh.append(None)
                utils.set_global_dict_value(None, vplx_config['public_ip'])
            else:
                ssh_conn = ssh.make_connect(vplx_config['public_ip'], vplx_config['port'], username,
                                            vplx_config['password'])
                self.list_vplx_ssh.append(ssh_conn)
                utils.set_global_dict_value(ssh_conn, vplx_config['public_ip'])


class QuorumAutoTest(object):
    def __init__(self, config):
        self.config = config
        self.conn = Connect(self.config)
        self.vplx_configs = self.config.get_vplx_configs()
        self.node_list = [vplx_config["hostname"] for vplx_config in self.vplx_configs]

    def ssh_conn_build(self):
        print("Start to build ssh connect")
        ssh = SSHAuthorizeNoMGN()
        ssh.init_cluster_no_mgn('versaplx', self.vplx_configs, self.conn.list_vplx_ssh)

    def install_software(self):
        lst_update = []
        lst_install_spc = []
        lst_install_drbd = []
        lst_install_linstor = []
        for vplx_conn in self.conn.list_vplx_ssh:
            install_obj = action.InstallSoftware(vplx_conn)
            lst_update.append(gevent.spawn(install_obj.update_apt))
            lst_install_spc.append(gevent.spawn(install_obj.install_spc))
            lst_install_drbd.append(gevent.spawn(install_obj.install_drbd))
            lst_install_linstor.append(
                gevent.spawn(install_obj.install_software, "linstor-controller linstor-satellite linstor-client"))
        gevent.joinall(lst_update)
        gevent.joinall(lst_install_spc)
        gevent.joinall(lst_install_drbd)
        gevent.joinall(lst_install_linstor)

    def test_drbd_quorum(self):
        sp = "pool1"
        # sp = "sp_quorum"
        resource = "res_quorum"
        if len(self.conn.list_vplx_ssh) != 3:
            utils.prt_log(None, f"Please make sure there are three nodes for this test", 2)
        test_times = self.config.get_test_times()
        use_case = self.config.get_use_case()

        vtel_conn = None
        if None not in self.conn.list_vplx_ssh:
            vtel_conn = self.conn.list_vplx_ssh[0]
        self.clean_dmesg()
        # utils.prt_log(None, f"Start to install software ...", 0)
        # self.install_software()
        install_obj = action.InstallSoftware(vtel_conn)
        # install_obj.update_pip()
        install_obj.install_vplx()

        self.create_linstor_resource(vtel_conn, sp, resource)

        stor_obj = action.Stor(vtel_conn)

        if not stor_obj.check_drbd_quorum(resource):
            utils.prt_log(None, f"Abnormal quorum status of {resource}", 1)
            self.get_log()
            self.delete_linstor_resource(vtel_conn, sp, resource)
            return
        if not self.ckeck_drbd_status(resource):
            self.get_log()
            self.delete_linstor_resource(vtel_conn, sp, resource)
            return
        device_name = stor_obj.get_device_name(resource)
        device_list = [vplx_config["private_ip"]["device"] for vplx_config in self.vplx_configs]
        if use_case == 1:
            test_conn_list = zip(self.conn.list_vplx_ssh, self.conn.list_vplx_ssh[1:] + self.conn.list_vplx_ssh[:1])
        if use_case == 2:
            test_conn_list = [(self.conn.list_vplx_ssh[0], self.conn.list_vplx_ssh[1]),
                              (self.conn.list_vplx_ssh[2], self.conn.list_vplx_ssh[1])]
        for conn_list in test_conn_list:
            times = utils.get_times() + 1
            utils.set_times(times)
            for i in range(test_times):
                print(f"Number of test times --- {times}")
                stor_a = action.Stor(conn_list[0])
                stor_b = action.Stor(conn_list[1])
                ip_a = action.IpService(conn_list[0])
                stor_a.primary_drbd(resource)
                time.sleep(3)
                device = device_list.pop(0)

                thread1 = threading.Thread(target=action.dd_operation,
                                           args=(device_name, conn_list[0]), name="thread1")
                thread2 = threading.Thread(target=ip_a.down_device, args=(device,), name="thread2")
                thread3 = threading.Thread(target=action.dd_operation,
                                           args=(device_name, conn_list[1]), name="thread3")
                thread4 = threading.Thread(target=stor_a.secondary_drbd, args=(resource,), name="thread4")
                print(threading.enumerate())
                print(threading.activeCount())  # 4
                thread1.start()
                time.sleep(20)
                print(threading.enumerate())
                print(threading.activeCount())  # 5 thread1
                thread2.start()
                print(threading.enumerate())
                print(threading.activeCount())  # 6 thread1,thread2
                thread2.join()
                print(threading.enumerate())
                print(threading.activeCount())  # 5thread1,
                time.sleep(3)
                stor_b.primary_drbd(resource)
                time.sleep(3)
                thread3.start()
                print(threading.enumerate())
                print(threading.activeCount())  # 6 thread1,thread3
                time.sleep(10)
                thread4.start()
                print(threading.enumerate())
                print(threading.activeCount())  # 6 thread1,thread3
                thread4.join()
                print(threading.enumerate())
                print(threading.activeCount())  # 5 thread3
                thread1.join()
                print(threading.enumerate())
                print(threading.activeCount())  # 5 thread3
                time.sleep(10)
                if thread3.is_alive():
                    stop_thread(thread3)
                    time.sleep(5)
                    utils.prt_log(conn_list[1], f"Stop dd operation", 0)
                    print(threading.enumerate())
                    print(threading.activeCount())  # 4
                else:
                    print(threading.enumerate())
                    print(threading.activeCount())
                    utils.prt_log(conn_list[1], f"dd operation had been finished", 1)
                thread3.join()
                if thread3.is_alive():
                    utils.prt_log(conn_list[1], f"thread3.is_alive2", 0)
                    print(threading.activeCount())
                print(threading.enumerate())
                print(threading.activeCount())  # 4

                # run_multiprocessing_test_quorum(stor_a, stor_b, ip_a, conn_list, device, device_name, resource)

                ip_a.up_device(device)
                ip_a.netplan_apply()
                time.sleep(480)
                if not self.ckeck_drbd_status(resource):
                    self.get_log()
                    stor_b.secondary_drbd(resource)
                    self.delete_linstor_resource(vtel_conn, sp, resource)
                    return
                stor_b.secondary_drbd(resource)

        self.delete_linstor_resource(vtel_conn, sp, resource)

    def test_thread(self):
        thread1 = threading.Thread(target=action.test_print, name="threadtest")
        print(threading.enumerate())
        print(threading.activeCount())  # 4
        thread1.start()
        print(threading.enumerate())
        print(threading.activeCount())  # 5
        time.sleep(4)
        stop_thread(thread1)
        time.sleep(5)
        print(threading.enumerate())
        print(threading.activeCount())  # 5
        thread1.join()
        print(threading.enumerate())
        print(threading.activeCount())  # 4

    # def dd_test(self, test_times, conn_list, resource, device_name):
    #     device_list = [vplx_config["private_ip"]["device"] for vplx_config in self.vplx_configs]
    #     for i in range(test_times):
    #         stor_a = action.Stor(conn_list[0])
    #         stor_b = action.Stor( conn_list[1])
    #         ip_a = action.IpService( conn_list[0])
    #         stor_a.primary_drbd(resource)
    #         time.sleep(3)
    #         device = device_list.pop(0)
    #         thread1 = threading.Thread(target=action.dd_operation,
    #                                    args=( device_name, conn_list[0]))
    #         thread2 = threading.Thread(target=ip_a.down_device, args=(device,))
    #         thread3 = threading.Thread(target=action.dd_operation,
    #                                    args=( device_name, conn_list[1]))
    #         thread1.start()
    #         time.sleep(20)
    #         thread2.start()
    #         thread2.join()
    #         # thread1.join()
    #
    #         stor_b.primary_drbd(resource)
    #         thread3.start()
    #         time.sleep(10)
    #         stor_a.secondary_drbd(resource)
    #         time.sleep(10)
    #         stop_thread(thread3)
    #         ip_a.up_device(device)
    #         ip_a.netplan_apply()
    #
    #         stor_b.secondary_drbd(resource)

    def create_linstor_resource(self, conn, sp, resource):
        size = self.config.get_resource_size()
        use_case = self.config.get_use_case()

        stor_obj = action.Stor(conn)
        # utils.prt_log(conn, f"Start to create node ...", 0)
        # for vplx_config in self.vplx_configs:
        #     stor_obj.create_node(vplx_config["hostname"], vplx_config["private_ip"]["ip"])
        # utils.prt_log(conn, f"Start to create storagepool {sp} ...", 0)
        # for vplx_config in self.vplx_configs:
        #     stor_obj.create_sp(vplx_config["hostname"], sp, vplx_config["lvm_device"])
        diskful_node_list = self.node_list[:]
        utils.prt_log(conn, f"Start to create resource {resource} ...", 0)
        if use_case == 1:
            diskless_node = diskful_node_list.pop()
            stor_obj.create_diskful_resource(diskful_node_list, sp, size, resource)
            stor_obj.create_diskless_resource(diskless_node, resource)
        if use_case == 2:
            stor_obj.create_diskful_resource(diskful_node_list, sp, size, resource)
        time.sleep(180)

    def delete_linstor_resource(self, conn, sp, resource):
        stor_obj = action.Stor(conn)
        utils.prt_log(conn, f"Start to delete resource {resource} ...", 0)
        stor_obj.delete_resource(resource)
        time.sleep(3)
        # utils.prt_log(conn, f"Start to delete storagepool {sp} ...", 0)
        # for node in self.node_list:
        #     stor_obj.delete_sp(node, sp)
        # time.sleep(3)
        # utils.prt_log(conn, f"Start to delete node ...", 0)
        # for node in self.node_list:
        #     stor_obj.delete_node(node)
        # time.sleep(3)

    def get_log(self):
        tmp_path = "/tmp/dmesg"
        lst_get_log = []
        lst_mkdir = []
        lst_download = []
        lst_del_log = []
        log_path = self.config.get_log_path()
        utils.prt_log(None, f"Start to collect dmesg file ...", 0)
        for conn in self.conn.list_vplx_ssh:
            debug_log = action.DebugLog(conn)
            lst_mkdir.append(gevent.spawn(debug_log.mkdir_dmesg_dir, tmp_path))
            lst_get_log.append(gevent.spawn(debug_log.get_dmesg_file, tmp_path))
            lst_download.append(gevent.spawn(debug_log.download_log, tmp_path, log_path))
            lst_del_log.append(gevent.spawn(debug_log.rm_dmesg_dir, tmp_path))
        gevent.joinall(lst_get_log)
        gevent.joinall(lst_mkdir)
        gevent.joinall(lst_download)
        gevent.joinall(lst_mkdir)
        utils.prt_log(None, f"Finished to collect dmesg file ...", 0)

    def clean_dmesg(self):
        lst_clean_dmesg = []
        for conn in self.conn.list_vplx_ssh:
            debug_log = action.DebugLog(conn)
            lst_clean_dmesg.append(gevent.spawn(debug_log.clear_dmesg))
        gevent.joinall(lst_clean_dmesg)

    def ckeck_drbd_status(self, resource):
        # Primary Secondary
        for vplx_conn in self.conn.list_vplx_ssh:
            stor_obj = action.Stor(vplx_conn)
            resource_status = stor_obj.get_drbd_status(resource)
            if resource_status[1] != "UpToDate" and resource_status[1] != "Diskless":
                utils.prt_log(vplx_conn, f"Resource status is {resource_status[1]}", 1)
                return False
        return True

    def delete_res(self):
        self.delete_linstor_resource(self.conn.list_vplx_ssh[0], "sp_quorum", "res_quorum")

    def test_get_log(self):
        # test collect log
        self.get_log()

    def ptint_mes(self):
        while True:
            print("a")

    def test_multiprocessing(self):
        for i in range(3):
            print(i)
            mp1 = multiprocessing.Process(target=self.ptint_mes)
            mp1.start()
            time.sleep(1)
            mp1.terminate()
            mp1.join()


def ptint_mes():
    while True:
        print("a")


def test_multiprocessing():
    for i in range(3):
        print(i)
        mp1 = multiprocessing.Process(target=ptint_mes)
        mp1.start()
        time.sleep(1)
        mp1.terminate()
        mp1.join()


class IscsiTest(object):
    def __init__(self, config):
        self.config = config
        self.conn = Connect(self.config)
        self.vplx_configs = self.config.get_vplx_configs()
        self.node_list = [vplx_config["hostname"] for vplx_config in self.vplx_configs]

    def test_drbd_in_used(self):
        start_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        if len(self.conn.list_vplx_ssh) != 3:
            utils.prt_log(None, f"Please make sure there are three nodes for this test", 2)
        test_times = self.config.get_test_times()
        device = self.config.get_device()
        target = self.config.get_target()
        resource = self.config.get_resource()
        ip_obj = action.IpService(self.conn.list_vplx_ssh[0])
        for i in range(test_times):
            i = i + 1
            utils.set_times(i)
            print(f"Number of test times --- {i}")
            if not self.check_target_lun_status(target, resource,
                                                self.conn.list_vplx_ssh[0]):
                self.collect_crm_report_file(start_time, self.conn.list_vplx_ssh[0])
            if not self.ckeck_drbd_status(resource):
                self.collect_crm_report_file(start_time, self.conn.list_vplx_ssh[0])
            utils.prt_log(self.conn.list_vplx_ssh[0], f"Down {device} ...", 0)
            ip_obj.down_device(device)
            time.sleep(40)
            if not self.check_target_lun_status(target, resource, self.conn.list_vplx_ssh[1]):
                ip_obj.up_device(device)
                ip_obj.netplan_apply()
                time.sleep(30)
                self.collect_crm_report_file(start_time, self.conn.list_vplx_ssh[0])
            utils.prt_log(self.conn.list_vplx_ssh[0], f"Up {device} ...", 0)
            ip_obj.up_device(device)
            ip_obj.netplan_apply()
            time.sleep(30)
            self.restore_resource(resource)
            utils.prt_log(None, f"Wait 10 minutes to restore the original environment", 0)
            time.sleep(600)

    def check_target_lun_status(self, target, resource, conn):
        iscsi_obj = action.Iscsi(conn)
        crm_status = iscsi_obj.get_crm_status()
        error_message = get_crm_status_by_type(crm_status, None, "FailedActions")
        if error_message:
            print(error_message)
            return False
        init_resource_status = get_crm_status_by_type(crm_status, resource, "iSCSILogicalUnit")
        init_target_status = get_crm_status_by_type(crm_status, target, "iSCSITarget")
        if init_target_status:
            if init_target_status[0] != 'Started':
                utils.prt_log(conn, f"Target status is {init_target_status[0]}", 1)
                return False
        else:
            utils.prt_log(conn, f"Can't get status of target {target}", 1)
            return False
        if init_resource_status:
            if init_resource_status[0] != 'Started':
                utils.prt_log(conn, f"LUN status is {init_resource_status[0]}", 1)
                return False
        else:
            utils.prt_log(conn, f"Can't get status of resource {resource}", 1)
            return False
        if not init_target_status[1] == init_resource_status[1]:
            utils.prt_log(conn, f"Target and LUN is not started on the same node", 1)
            return False
        return True

    def ckeck_drbd_status(self, resource):
        for vplx_conn in self.conn.list_vplx_ssh:
            stor_obj = action.Stor(vplx_conn)
            resource_status = stor_obj.get_drbd_status(resource)
            if resource_status[1] != "UpToDate" and resource_status[1] != "Diskless":
                utils.prt_log(vplx_conn, f"Resource status is {resource_status[1]}", 1)
                return False
        return True

    def restore_resource(self, resource):
        conn = self.conn.list_vplx_ssh[1]
        init_start_node = self.node_list[0]
        iscsi_obj = action.Iscsi(conn)
        iscsi_obj.ref_res()
        time.sleep(10)
        utils.prt_log(conn, f"Move {resource} back to {init_start_node} ...", 0)
        iscsi_obj.move_res(resource, init_start_node)
        time.sleep(20)
        crm_status = iscsi_obj.get_crm_status()
        resource_status = get_crm_status_by_type(crm_status, resource, "iSCSILogicalUnit")
        if resource_status:
            if resource_status[0] != 'Started' or resource_status[1] != init_start_node:
                utils.prt_log(conn,
                              f"Failed to move {resource}, status:{resource_status[0]}", 1)
        else:
            utils.prt_log(conn, f"Can't get status of resource {resource}", 1)
        iscsi_obj.unmove_res(resource)

    def collect_crm_report_file(self, time, conn):
        crm_log_path = self.config.get_log_path()
        debug_log = action.DebugLog(conn)
        utils.prt_log(conn, f"Start to collect crm_report...", 0)
        debug_log.get_crm_report_file(time, crm_log_path)
        utils.prt_log(conn, f"Finished to collect crm_report and exit testing ...", 2)
