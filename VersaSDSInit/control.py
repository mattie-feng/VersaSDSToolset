import gevent
from gevent import monkey
import time
import sys

from ssh_authorized import SSHAuthorizeNoMGN
import utils
import action


# 协程相关的补丁
monkey.patch_all()


timeout = gevent.Timeout(60)


class Connect():
    """
    通过ssh连接节点，生成连接对象的列表
    """
    list_ssh = []
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            Connect._instance = super().__new__(cls)
            Connect._instance.conf_file = utils.ConfFile()
            Connect._instance.cluster = Connect._instance.conf_file.cluster
            Connect.get_ssh_conn(Connect._instance)
        return Connect._instance

    def get_ssh_conn(self):
        ssh = SSHAuthorizeNoMGN()
        local_ip = utils.get_host_ip()
        for node in self.cluster['node']:
            if local_ip == node['public_ip']:
                self.list_ssh.append(None)
            else:
                self.list_ssh.append(ssh.make_connect(node['public_ip'],node['port'],'root',node['root_password']))    


class PacemakerConsole():
    def __init__(self):
        self.conn = Connect()

    def modify_hostname(self):
        lst = []
        hosts_file = []
        for node in self.conn.cluster['node']:
            hosts_file.append({'ip': node['public_ip'], 'hostname': node['hostname']})
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            executor = action.Host(ssh)
            lst.append(gevent.spawn(executor.modify_hostname, node['hostname']))
            lst.append(gevent.spawn(executor.modify_hostsfile, '127.0.1.1', node['hostname']))
            for host in hosts_file:
                lst.append(gevent.spawn(executor.modify_hostsfile, host['ip'], host['hostname']))

        gevent.joinall(lst)

    def ssh_conn_build(self):
        ssh = SSHAuthorizeNoMGN()
        ssh.init_cluster_no_mgn('cluster', self.conn.cluster['node'], self.conn.list_ssh)

    def check_hostname(self):
        lst = []
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            lst.append(gevent.spawn(action.Host(ssh).check_hostname, node['hostname']))
        gevent.joinall(lst)
        result = [job.value for job in lst]
        return result

    def check_ssh_authorized(self):
        lst = []
        cluster_hosts = [node['hostname'] for node in self.conn.cluster['node']]
        for ssh in self.conn.list_ssh:
            lst.append(gevent.spawn(action.Host(ssh).check_ssh, cluster_hosts))
        gevent.joinall(lst)
        result = [job.value for job in lst]
        return result

    def sync_time(self):
        lst = []
        for ssh in self.conn.list_ssh:
            lst.append(gevent.spawn(action.Corosync(ssh).sync_time))
        gevent.joinall(lst)

    def corosync_conf_change(self):
        lst = []
        single_interface = self.conn.cluster['single_heartbeat_line'] 
        cluster_name = self.conn.conf_file.get_cluster_name()
        if single_interface:
            bindnetaddr = self.conn.conf_file.get_bindnetaddr()[1]
        else:
            bindnetaddr = self.conn.conf_file.get_bindnetaddr()[0]

        interface = self.conn.conf_file.get_inferface()
        nodelist = self.conn.conf_file.get_nodelist(single_interface)

        for ssh in self.conn.list_ssh:
            lst.append(gevent.spawn(action.Corosync(ssh).change_corosync_conf,
                                    cluster_name,
                                    bindnetaddr,
                                    interface,
                                    nodelist,
                                    single_interface))

        gevent.joinall(lst)

    def restart_corosync(self):
        lst = []
        timeout.start()
        for ssh in self.conn.list_ssh:
            lst.append(gevent.spawn(action.Corosync(ssh).restart_corosync))
        try:
            gevent.joinall(lst)
        except gevent.Timeout:
            print('Restarting corosync service timed out')
        else:
            timeout.close()

    def check_corosync(self):
        nodes = [node['hostname'] for node in self.conn.cluster['node']]
        single_interface = self.conn.cluster['single_heartbeat_line']
        lst_ring_status = []
        lst_cluster_status = []
        for ssh,node in zip(self.conn.list_ssh,self.conn.cluster['node']):
            corosync = action.Corosync(ssh)
            lst_ring_status.append(gevent.spawn(corosync.check_ring_status,node,single_interface))
            lst_cluster_status.append(gevent.spawn(corosync.check_corosync_status,nodes))

        gevent.joinall(lst_ring_status)
        gevent.joinall(lst_cluster_status)

        lst = []
        for x,y in zip([i.value for i in lst_ring_status],[i.value for i in lst_cluster_status]):
            if x and y:
                lst.append(True)
            else:
                lst.append(False)
        return lst

    def packmaker_conf_change(self):
        cluster_name = self.conn.conf_file.get_cluster_name()
        packmaker = action.Pacemaker()

        lst = []
        lst.append(gevent.spawn(packmaker.modify_cluster_name,cluster_name))
        lst.append(gevent.spawn(packmaker.modify_policy))
        lst.append(gevent.spawn(packmaker.modify_stickiness))
        lst.append(gevent.spawn(packmaker.modify_stonith_enabled))

        gevent.joinall(lst)
        self.conn.conf_file.cluster['cluster'] = cluster_name
        self.conn.conf_file.update_yaml()

    def check_packmaker(self):
        cluster_name = self.conn.cluster['cluster']
        packmaker = action.Pacemaker()
        if packmaker.check_crm_conf(cluster_name):
            return [True] * len(self.conn.list_ssh)
        else:
            return [False] * len(self.conn.list_ssh)

    def targetcli_conf_change(self):
        lst = []
        for ssh in self.conn.list_ssh:
            targetcli = action.TargetCLI(ssh)
            lst.append(gevent.spawn(targetcli.set_auto_add_default_portal))
            lst.append(gevent.spawn(targetcli.set_auto_add_mapped_luns))
            lst.append(gevent.spawn(targetcli.set_auto_enable_tpgt))

        gevent.joinall(lst)

    def check_targetcli(self):
        lst = []
        for ssh in self.conn.list_ssh:
            targetcli = action.TargetCLI(ssh)
            lst.append(gevent.spawn(targetcli.check_targetcli_conf))

        gevent.joinall(lst)
        result = [job.value for job in lst]
        return result

    def service_set(self):
        lst = []
        for ssh in self.conn.list_ssh:
            executor = action.ServiceSet(ssh)
            lst.append(gevent.spawn(executor.set_disable_drbd))
            lst.append(gevent.spawn(executor.set_disable_linstor_controller))
            lst.append(gevent.spawn(executor.set_disable_targetctl))
            lst.append(gevent.spawn(executor.set_enable_linstor_satellite))
            lst.append(gevent.spawn(executor.set_enable_pacemaker))
            lst.append(gevent.spawn(executor.set_enable_corosync))

        gevent.joinall(lst)

    def check_service(self):
        lst = []
        for ssh in self.conn.list_ssh:
            check_result = []
            executor = action.ServiceSet(ssh)
            check_result.append(gevent.spawn(executor.check_drbd))
            check_result.append(gevent.spawn(executor.check_linstor_controller))
            check_result.append(gevent.spawn(executor.check_linstor_satellite))
            check_result.append(gevent.spawn(executor.check_pacemaker))
            check_result.append(gevent.spawn(executor.check_corosync))
            gevent.joinall(check_result)
            check_result = [job.value for job in check_result]
            if check_result == ['disable','disable','enable','enable','enable']:
                lst.append(True)
            else:
                lst.append(False)
        return lst

    def replace_ra(self):
        other_node = []
        for ssh,node in zip(self.conn.list_ssh,self.conn.cluster['node']):
            executor = action.RA(ssh)
            lst = []
            lst.append(gevent.spawn(executor.backup_iscsilogicalunit()))
            lst.append(gevent.spawn(executor.backup_iscsitarget()))
            if ssh:
                other_node.append(node['hostname'])

        executor = action.RA()
        executor.cp_ra()
        executor.rename_ra()
        for node in other_node:
            executor.scp_ra(node)

    def check_ra(self):
        lst = []

        for ssh in self.conn.list_ssh:
            check_result = []
            executor = action.RA(ssh)
            check_result.append(gevent.spawn(executor.check_ra_target))
            check_result.append(gevent.spawn(executor.check_ra_logicalunit))
            gevent.joinall(check_result)
            check_result = [job.value for job in check_result]
            if all(check_result):
                lst.append(True)
            else:
                lst.append(False)

        return lst

    def set_ip_on_device(self):
        lst_set = []

        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            ip_service = action.IpService(ssh)
            lst_set.append(gevent.spawn(ip_service.set_ip, node['private_ip']['device'], node['private_ip']['ip'], node['private_ip']['gateway']))
        gevent.joinall(lst_set)
        self.up_ip_service()
        print("Finish to set ip")

    def modify_ip_on_device(self):
        lst_modify = []

        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            ip_service = action.IpService(ssh)
            lst_modify.append(gevent.spawn(ip_service.modify_ip, node['private_ip']['device'], node['private_ip']['ip'], node['private_ip']['gateway']))
        gevent.joinall(lst_modify)
        self.up_ip_service()
        print("Finish to modify ip")

    def up_ip_service(self):
        lst_up = []
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            ip_service = action.IpService(ssh)
            lst_up.append(gevent.spawn(ip_service.up_ip_service, node['private_ip']['device']))
        gevent.joinall(lst_up)

    
class LinstorConsole():
    def __init__(self):
        self.conn = Connect()

    def create_conf_file(self):
        ips = ",".join([node['public_ip'] for node in self.conn.cluster['node']])
        coroutine_list = []
        for ssh in self.conn.list_ssh:
            linstor = action.Linstor(ssh)
            coroutine_list.append(gevent.spawn(linstor.create_conf(ips)))
        gevent.joinall(coroutine_list)

        if self.conn.list_ssh:
            action.Linstor(self.conn.list_ssh[0]).restart_controller()

    def create_nodes(self):
        coroutine_list = []
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            linstor = action.Linstor(ssh)
            coroutine_list.append(gevent.spawn(linstor.create_node,node['hostname'],node['public_ip']))
        gevent.joinall(coroutine_list)

    def create_pools(self):
        # 待测试 以及确定thinlv创建时用到的lvm资源的格式。
        coroutine_list = []
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            linstor = action.Linstor(ssh)
            vol = node['lvm_device'].split("/")
            if len(vol) == 1:
                coroutine_list.append(gevent.spawn(linstor.create_lvm_sp,node['hostname'],node['lvm_device']))
            elif len(vol) == 2:
                coroutine_list.append(gevent.spawn(linstor.create_lvmthin_sp,node['hostname'],node['lvm_device']))
        gevent.joinall(coroutine_list)

    # HA controller配置
    def build_ha_controller(self):
        backup_path = self.conn.cluster['backup_path']
        ha = action.HALinstorController()
        ha.create_rd('linstordb')
        ha.create_vd('linstordb', '250M')

        if not ha.linstor_is_conn():
            print('LINSTOR connection refused')
            sys.exit()

        node_list = [node['hostname'] for node in self.conn.cluster['node']]
        if not ha.pool0_is_exist(node_list):
            print('storage-pool：pool0 does not exist')
            sys.exit()

        lst_res_create = []
        for node in self.conn.cluster['node']:
            lst_res_create.append(gevent.spawn(ha.create_res,'linstordb',node['hostname'],'pool0'))

        gevent.joinall(lst_res_create)

        for ssh in self.conn.list_ssh:
            ha = action.HALinstorController(ssh)
            if ha.is_active_controller():
                ha.stop_controller()
                ha.backup_linstor(backup_path) # 要放置备份文件的路径（文件夹）
                ha.move_database(backup_path)
                ha.add_linstordb_to_pacemaker(len(self.conn.cluster['node']))
            ha.modify_satelite_service()  # linstor satellite systemd 配置
        


    def check_ha_controller(self,timeout=30):
        ha = action.HALinstorController()
        node_list = [node['hostname'] for node in self.conn.cluster['node']]
        t_beginning = time.time()
        while True:
            if ha.check_linstor_controller(node_list):
                return True
            seconds_passed = time.time() - t_beginning
            if timeout and seconds_passed > timeout:
                return False
            time.sleep(1)


    def backup_linstordb(self,timeout=30):
        linstordb_path = 'ls -l /var/lib/linstor'
        if self.conn.cluster['backup_path'].endswith('/'):
            backup_path = f"{self.conn.cluster['backup_path']}backup_{time.strftime('%Y%m%d%H%M')}"
        else:
            backup_path = f"{self.conn.cluster['backup_path']}/backup_{time.strftime('%Y%m%d%H%M')}"

        t_beginning = time.time()
        while True:
            for ssh in self.conn.list_ssh:
                ha = action.HALinstorController(ssh)
                if ha.is_active_controller():
                    if ha.check_linstor_file(linstordb_path):
                        ha.backup_linstor(backup_path)
                if ha.check_linstor_file(f'{backup_path}/linstor'):
                    return True
            seconds_passed = time.time() - t_beginning
            if timeout and seconds_passed > timeout:
                return False
            time.sleep(1)


    def destroy_linstordb(self):
        ha = action.HALinstorController()
        if not ha.linstor_is_conn():
            print('LINSTOR connection refused')
            sys.exit()

        for ssh in self.conn.list_ssh:
            ha = action.HALinstorController(ssh)
            list_lv = ha.get_linstordb_lv()
            ha.umount_lv(list_lv)
            ha.secondary_drbd('linstordb')
            ha.delete_rd('linstordb') # 一般只需在一个节点上执行一次
            ha.remove_lv(list_lv)
            

class VersaSDSSoftConsole():
    def __init__(self):
        self.conn = Connect()

    def apt_update(self):
        lst = []
        for ssh in self.conn.list_ssh:
            handler = action.DRBD(ssh)
            lst.append(gevent.spawn(handler.apt_update))
        gevent.joinall(lst)


    def install_spc(self):
        lst = []
        for ssh in self.conn.list_ssh:
            handler = action.DRBD(ssh)
            lst.append(gevent.spawn(handler.install_spc))        
        gevent.joinall(lst)
        result = [job.value for job in lst]
        return result


    def install_drbd(self):
        lst = []
        for ssh in self.conn.list_ssh:
            handler = action.DRBD(ssh)
            lst.append(gevent.spawn(handler.install_drbd))
        gevent.joinall(lst)


    def install_linstor(self):
        lst = []
        for ssh in self.conn.list_ssh:
            handler = action.Linstor(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)


    def install_lvm2(self):
        lst = []
        for ssh in self.conn.list_ssh:
            handler = action.LVM(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)


    def install_pacemaker(self):
        lst = []
        for ssh in self.conn.list_ssh:
            handler = action.Pacemaker(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)


    def install_targetcli(self):
        lst = []
        for ssh in self.conn.list_ssh:
            handler = action.TargetCLI(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)



    def get_all_service_status(self):
        lst = []
        for ssh in self.conn.list_ssh:
            service = action.ServiceSet(ssh)
            host = action.Host(ssh)
            lst.append(gevent.spawn(host.get_hostname))
            lst.append(gevent.spawn(service.check_pacemaker))
            lst.append(gevent.spawn(service.check_corosync))
            lst.append(gevent.spawn(service.check_linstor_satellite))
            lst.append(gevent.spawn(service.check_drbd))
            lst.append(gevent.spawn(service.check_linstor_controller))

        gevent.joinall(lst)
        result = [job.value for job in lst]
        for i in range(0,len(result),6):
            yield result[i:i+6]


    def get_version(self,*args):
        """
        参数输入要获取版本信息的软件，支持sysos，syskernel，drbd，linstor，targetcli，pacemaker，corosync
        返回数据的顺序与参数顺序一致
        :param args:
        :return:
        """
        coroutine_list = []
        for ssh in self.conn.list_ssh:
            host = action.Host(ssh)
            coroutine_list.append(gevent.spawn(host.get_hostname))
            for soft in args:
                if soft == 'sysos':
                    coroutine_list.append(gevent.spawn(host.get_sys_version))
                elif soft == 'syskernel':
                    coroutine_list.append(gevent.spawn(host.get_kernel_version))
                elif soft == 'drbd':
                    drbd = action.DRBD(ssh)
                    coroutine_list.append(gevent.spawn(drbd.get_version))
                elif soft == 'linstor':
                    linstor = action.Linstor(ssh)
                    coroutine_list.append(gevent.spawn(linstor.get_version))
                elif soft == 'targetcli':
                    targetcli = action.TargetCLI(ssh)
                    coroutine_list.append(gevent.spawn(targetcli.get_version))
                elif soft == 'pacemaker':
                    pacemaker = action.Pacemaker(ssh)
                    coroutine_list.append(gevent.spawn(pacemaker.get_version))
                elif soft == 'corosync':
                    corosync = action.Corosync(ssh)
                    coroutine_list.append(gevent.spawn(corosync.get_version))

        gevent.joinall(coroutine_list)
        result = [job.value for job in coroutine_list]
        for i in range(0,len(result),len(args)+1):
            yield result[i:i+len(args)+1]


class LVMConsole():
    def __init__(self):
        self.conn = Connect()

    def create_dirver_pool(self):
        pv_list = []
        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            lvm = action.LVM(ssh)
            pv_list.append(gevent.spawn(lvm.pv_create,node['pool_disk']))
        gevent.joinall(pv_list)
        pv_list = [job.value for job in pv_list]
        for r,node in zip(pv_list,self.conn.cluster['node']):
            if not r:
                print(f"{node['pool_disk']} is not on {node['hostname']}")
                sys.exit()

        for ssh, node in zip(self.conn.list_ssh, self.conn.cluster['node']):
            lvm = action.LVM(ssh)
            vol = node['lvm_device'].split("/")
            if len(vol) == 1:
                vg = vol[0]
                lvm.vg_create(vg,node['pool_disk'])
            elif len(vol) == 2:
                vg,lv = vol
                lvm.vg_create(vg,node['pool_disk'])
                lvm.thinpool_create(vg,lv)





