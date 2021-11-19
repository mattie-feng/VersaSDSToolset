import utils
import subprocess
import time
import log


def dd_operation(logger, device, conn=None):
    oprt_id = log.create_oprt_id()
    logger.write_to_log(conn, 'DATA', 'STR', "dd_operation", '', oprt_id)
    cmd = f"dd if=/dev/urandom of={device} oflag=direct status=progress"
    if conn is None:
        logger.write_to_log(conn, 'OPRT', 'CMD', "dd_operation", oprt_id, cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                             encoding="utf-8")  # 使用管道
        while p.poll() is None:
            print(p.stdout.readline())
            time.sleep(1)
        # print(p.pid)
        # time.sleep(10)
        # p.kill()
        # print("killed....")
        print(f"{cmd} finished....")
        logger.write_to_log(conn, 'DATA', 'CMD', "dd_operation", oprt_id, {"st": True, "rt": p.stdout.readline()})
    else:
        logger.write_to_log(conn, 'OPRT', 'CMD', "dd_operation", oprt_id, cmd)
        result = conn.exec_cmd_and_print(cmd)
        logger.write_to_log(conn, 'DATA', 'CMD', "dd_operation", oprt_id, {"st": True, "rt": result})


class IpService(object):
    def __init__(self, logger, conn=None):
        self.conn = conn
        self.logger = logger

    def down_device(self, device):
        cmd = f"ifconfig {device} down"
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def up_device(self, device):
        cmd = f"ifconfig {device} up"
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def netplan_apply(self):
        cmd = "netplan apply"
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True


class DebugLog(object):
    def __init__(self, logger, conn=None):
        self.conn = conn
        self.logger = logger

    def get_crm_report_file(self, time, path):
        cmd = f'crm_report --from "{time}" {path}/crm_report_${{HOSTNAME}}_$(date +"%Y-%m-%d")_{utils.get_times()}.log'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def get_dmesg_file(self, path):
        # 显示内核缓冲日志
        cmd = f'dmesg -T | cat > {path}/dmesg.log'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def clear_dmesg(self, path):
        # 清空内核缓存信息
        cmd = f'dmesg -C'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True


class InstallSoftware(object):
    def __init__(self, logger, conn=None):
        self.conn = conn
        self.logger = logger

    def update_apt(self):
        """更新apt"""
        cmd = "apt update -y"
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def install_spc(self):
        cmd1 = 'apt install -y software-properties-common'
        cmd2 = 'add-apt-repository -y ppa:linbit/linbit-drbd9-stack'
        result1 = utils.exec_cmd(cmd1, self.logger, self.conn)
        result2 = utils.exec_cmd(cmd2, self.logger, self.conn)

    def update_pip(self):
        cmd = "python3 -m pip install --upgrade pip"
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def install_software(self, name):
        """根据软件名安装对应软件"""
        cmd = f"apt install {name} -y"
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def install_drbd(self):
        cmd = 'export DEBIAN_FRONTEND=noninteractive && apt install -y drbd-utils drbd-dkms'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def install_vplx(self):
        result = utils.upload_file(self.logger, "vplx", "/tmp", self.conn)
        if result["st"]:
            cmd_pip = f'pip3 install -r /tmp/vplx/requirements.txt'
            result_pip = utils.exec_cmd(cmd_pip, self.logger, self.conn)
            # if not result_pip["st"]:
            #     print("Please install python module on /tmp/requirements.txt")
        # if self.conn:
        #     cmd = f'scp -r vplx root@{utils.get_global_dict_value(self.conn)}:/tmp'
        #     result = utils.exec_cmd(cmd, self.logger)
        # else:
        #     cmd = f'cp -r vplx /tmp'
        #     result = utils.exec_cmd(cmd, self.logger)
        # if result["st"]:
        #     cmd_pip = f'pip3 install -r /tmp/vplx/requirements.txt'
        #     result_pip = utils.exec_cmd(cmd_pip, self.logger, self.conn)
        #     # if not result_pip["st"]:
        #     #     print("Please install python module on /tmp/requirements.txt")

    def get_log(self):
        result = utils.download_file(self.logger, "/root/VersaSDSToolset/AutomatedTesting/crm_report_test1_2021-11-16_1.log.tar.bz2", "./", self.conn)
        if result["st"]:
            return True


class Stor(object):
    def __init__(self, logger, conn=None):
        self.conn = conn
        self.logger = logger

    def get_drbd_status(self, resource):
        cmd = f'drbdadm status {resource}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        re_string = f'{resource}\s*role:(\w+).*\s*disk:(\w+)'
        re_peer_string = '\S+\s*role:(\w+).*\s*peer-disk:(\w+)'
        if result["st"]:
            re_result = utils.re_search(self.logger, re_string, result["rt"], "groups")
            re_peer_result = utils.re_findall(self.logger, re_peer_string, result["rt"])
            return re_result, re_peer_result

    def check_drbd_quorum(self, resource):
        cmd = f'drbdsetup show {resource}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        re_string = 'quorum\s+majority.*\s*on\s*-\s*no\s*-\s*quorum\s+io\s*-\s*error'
        if result["st"]:
            re_result = utils.re_search(self.logger, re_string, result["rt"], "bool")
            return re_result

    def primary_drbd(self, resource):
        cmd = f'drbdadm primary {resource}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def secondary_drbd(self, resource):
        cmd = f'drbdadm secondary {resource}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def create_node(self, node, ip):
        cmd = f'python3 /tmp/vplx/vtel.py stor n c {node} -ip {ip}  -nt Combined'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def create_sp(self, node, sp, lvm_device):
        cmd = f'python3 /tmp/vplx/vtel.py stor sp c {sp}  -n {node} -lvm {lvm_device}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def create_diskful_resource(self, node_list, sp, size, resource):
        node = " ".join(node_list)
        cmd = f'python3 /tmp/vplx/vtel.py stor r c {resource} -s {size} -n {node} -sp {sp}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def create_diskless_resource(self, node, resource):
        cmd = f'python3 /tmp/vplx/vtel.py stor r c {resource} -diskless -n {node}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def delete_resource(self, resource):
        cmd = f'python3 /tmp/vplx/vtel.py stor r d {resource} -y'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def delete_sp(self, node, sp):
        cmd = f'python3 /tmp/vplx/vtel.py stor r d {sp} -n {node} -y'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def delete_node(self, node):
        cmd = f'python3 /tmp/vplx/vtel.py stor n d {node} -y'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def get_device_name(self, resource):
        cmd = f'linstor r lv -r {resource}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        re_string = '/dev/drbd\d+'
        if result["st"]:
            re_result = utils.re_search(self.logger, re_string, result["rt"], "group")
            return re_result


class Iscsi(object):
    def __init__(self, logger, conn=None):
        self.conn = conn
        self.logger = logger

    def ref_res(self):
        cmd = f'crm res ref'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def move_res(self, resource, node):
        cmd = f'crm res move {resource} {node}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True

    def get_res_status(self, resource):
        cmd = f'crm res show {resource}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return result["rt"]

    def get_crm_status(self):
        cmd = f'crm st'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return result["rt"]

    def unmove_res(self, resource):
        cmd = f'crm res unmove {resource}'
        result = utils.exec_cmd(cmd, self.logger, self.conn)
        if result["st"]:
            return True
