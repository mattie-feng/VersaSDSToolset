import utils
import subprocess
import time
import log


class RWData(object):
    def __init__(self, conn=None):
        self.conn = conn

    def dd_operation(self, device):
        logger = utils.get_logger()
        oprt_id = log.create_oprt_id()
        logger.write_to_log(self.conn, 'DATA', 'STR', "dd_operation", '', oprt_id)
        cmd = f"dd if=/dev/urandom of={device} oflag=direct status=progress"
        if self.conn is None:
            logger.write_to_log(self.conn, 'OPRT', 'CMD', "dd_operation", oprt_id, cmd)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True,
                                 encoding="utf-8")  # 使用管道
            while p.poll() is None:
                print(p.stdout.readline())
                time.sleep(1)
            # p.kill()
            print(f"{cmd} finished....")
            logger.write_to_log(self.conn, 'DATA', 'CMD', "dd_operation", oprt_id,
                                {"st": True, "rt": p.stdout.readline()})
        else:
            logger.write_to_log(self.conn, 'OPRT', 'CMD', "dd_operation", oprt_id, cmd)
            # result = conn.exec_cmd_and_print(cmd)
            result = self.conn.exec_cmd(cmd)
            # print(result['rt'])
            logger.write_to_log(self.conn, 'DATA', 'CMD', "dd_operation", oprt_id, result)
            # logger.write_to_log(conn, 'DATA', 'CMD', "dd_operation", oprt_id, {"st": True, "rt": result})


def test_print():
    while True:
        print("a")
        time.sleep(1)


def dd_operation(device, conn=None):
    logger = utils.get_logger()
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
        # p.kill()
        print(f"{cmd} finished....")
        logger.write_to_log(conn, 'DATA', 'CMD', "dd_operation", oprt_id, {"st": True, "rt": p.stdout.readline()})
    else:
        logger.write_to_log(conn, 'OPRT', 'CMD', "dd_operation", oprt_id, cmd)
        # result = conn.exec_cmd_and_print(cmd)
        result = conn.exec_cmd(cmd)
        # print(result['rt'])
        logger.write_to_log(conn, 'DATA', 'CMD', "dd_operation", oprt_id, result)
        # logger.write_to_log(conn, 'DATA', 'CMD', "dd_operation", oprt_id, {"st": True, "rt": result})


class IpService(object):
    def __init__(self, conn=None):
        self.conn = conn

    def down_device(self, device):
        cmd = f"ifconfig {device} down"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def up_device(self, device):
        cmd = f"ifconfig {device} up"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def netplan_apply(self):
        cmd = "netplan apply"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True


class DebugLog(object):
    def __init__(self, conn=None):
        self.conn = conn

    def get_crm_report_file(self, time, path):
        cmd = f'crm_report --from "{time}" {path}/crm_report_${{HOSTNAME}}_$(date +"%Y-%m-%d")_{utils.get_times()}.log'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def get_dmesg_file(self, path):
        # 显示内核缓冲日志
        cmd = f'dmesg -T | cat > {path}/dmesg_${{HOSTNAME}}_$(date +"%Y-%m-%d")_{utils.get_times()}.log'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def mkdir_dmesg_dir(self, path):
        cmd = f'mkdir -p {path}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def rm_dmesg_dir(self, path):
        cmd = f'rm -rf {path}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def clear_dmesg(self):
        # 清空内核缓存信息
        cmd = f'dmesg -C'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def download_log(self, remote, local):
        result = utils.download_file(remote, local, self.conn)
        if result["st"]:
            return True


class InstallSoftware(object):
    def __init__(self, conn=None):
        self.conn = conn

    def update_apt(self):
        """更新apt"""
        cmd = "apt update -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def install_spc(self):
        cmd1 = 'apt install -y software-properties-common'
        cmd2 = 'add-apt-repository -y ppa:linbit/linbit-drbd9-stack'
        result1 = utils.exec_cmd(cmd1, self.conn)
        result2 = utils.exec_cmd(cmd2, self.conn)

    def update_pip(self):
        cmd = "python3 -m pip install --upgrade pip"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def install_software(self, name):
        """根据软件名安装对应软件"""
        cmd = f"apt install {name} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def install_drbd(self):
        cmd = 'export DEBIAN_FRONTEND=noninteractive && apt install -y drbd-utils drbd-dkms'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def install_vplx(self):
        result = utils.upload_file("vplx", "/tmp", self.conn)
        if result["st"]:
            # cmd_pip = f'pip3 install -r /tmp/vplx/requirements.txt'
            # result_pip = utils.exec_cmd(cmd_pip, self.conn)
            # if not result_pip["st"]:
            #     print("Please install python module on /tmp/requirements.txt")
            return True


class Stor(object):
    def __init__(self, conn=None):
        self.conn = conn

    def get_drbd_status(self, resource):
        cmd = f'drbdadm status {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        re_string = f'{resource}\s*role:(\w+).*\s*disk:(\w+)'
        # re_peer_string = '\S+\s*role:(\w+).*\s*peer-disk:(\w+)'
        if result["st"]:
            re_result = utils.re_search(re_string, result["rt"], "groups")
            # re_peer_result = utils.re_findall( re_peer_string, result["rt"])
            # return re_result, re_peer_result
            return re_result

    def check_drbd_quorum(self, resource):
        cmd = f'drbdsetup show {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        re_string = 'quorum\s+majority.*\s*on\s*-\s*no\s*-\s*quorum\s+io\s*-\s*error'
        if result["st"]:
            re_result = utils.re_search(re_string, result["rt"], "bool")
            return re_result

    def primary_drbd(self, resource):
        cmd = f'drbdadm primary {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def secondary_drbd(self, resource):
        cmd = f'drbdadm secondary {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def create_node(self, node, ip):
        cmd = f'python3 /tmp/vplx/vtel.py stor n c {node} -ip {ip}  -nt Combined'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return self.check_vtel_result(result["rt"])

    def create_sp(self, node, sp, lvm_device):
        cmd = f'python3 /tmp/vplx/vtel.py stor sp c {sp}  -n {node} -lvm {lvm_device}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return self.check_vtel_result(result["rt"])

    def create_diskful_resource(self, node_list, sp, size, resource):
        node = " ".join(node_list)
        cmd = f'python3 /tmp/vplx/vtel.py stor r c {resource} -s {size} -n {node} -sp {sp}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return self.check_vtel_result(result["rt"])

    def create_diskless_resource(self, node, resource):
        cmd = f'python3 /tmp/vplx/vtel.py stor r c {resource} -diskless -n {node}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return self.check_vtel_result(result["rt"])

    def delete_resource(self, resource):
        cmd = f'python3 /tmp/vplx/vtel.py stor r d {resource} -y'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return self.check_vtel_result(result["rt"])

    def delete_sp(self, node, sp):
        cmd = f'python3 /tmp/vplx/vtel.py stor sp d {sp} -n {node} -y'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return self.check_vtel_result(result["rt"])

    def delete_node(self, node):
        cmd = f'python3 /tmp/vplx/vtel.py stor n d {node} -y'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return self.check_vtel_result(result["rt"])

    def get_device_name(self, resource):
        cmd = f'linstor r lv -r {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        re_string = '/dev/drbd\d+'
        if result["st"]:
            re_result = utils.re_search(re_string, result["rt"], "group")
            return re_result

    def check_vtel_result(self, result):
        re_string = f'SUCCESS|successfully created'
        re_result = utils.re_search(re_string, result, "bool")
        return re_result


class Iscsi(object):
    def __init__(self, conn=None):
        self.conn = conn

    def ref_res(self):
        cmd = f'crm res ref'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def move_res(self, resource, node):
        cmd = f'crm res move {resource} {node}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def get_res_status(self, resource):
        cmd = f'crm res show {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def get_crm_status(self):
        cmd = f'crm st'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def unmove_res(self, resource):
        cmd = f'crm res unmove {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
