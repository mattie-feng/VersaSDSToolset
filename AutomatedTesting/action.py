import utils
import re


class RWData(object):
    def __init__(self, conn=None):
        self.conn = conn

    def dd_operation(self, device):
        cmd = f"dd if=/dev/urandom of={device} oflag=direct status=progress"
        utils.prt_log(self.conn, f"Start dd on {utils.get_global_dict_value(self.conn)}.", 0)
        utils.exec_cmd(cmd, self.conn)

    def get_dd(self):
        cmd = 'ps -ef | grep dd'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def kill_dd(self, pid):
        cmd = f'kill -9 {pid}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True


class IpService(object):
    def __init__(self, conn=None):
        self.conn = conn

    def down_device(self, device):
        cmd = f"ifconfig {device} down"
        # cmd = f"nmcli device disconnect {device}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def up_device(self, device):
        # cmd = f"ifconfig {device} up"
        cmd = f"nmcli device connect {device}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    # def netplan_apply(self):
    #     cmd = "netplan apply"
    #     result = utils.exec_cmd(cmd, self.conn)
    #     if result["st"]:
    #         return True


class DebugLog(object):
    def __init__(self, conn=None):
        self.conn = conn

    def get_crm_report_file(self, time, path):
        cmd = f'crm_report --from "{time}" {path}/crm_report_${{HOSTNAME}}_$(date +"%Y-%m-%d-%H-%M")_{utils.get_times()}.log'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def get_dmesg_file(self, path):
        # 显示内核缓冲日志
        cmd = f'dmesg -T | cat > {path}/dmesg_${{HOSTNAME}}_$(date +"%Y-%m-%d-%H-%M")_{utils.get_times()}.log'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def mkdir_log_dir(self, path):
        cmd = f'mkdir -p {path}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True

    def rm_log_dir(self, path):
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

    # def install_vplx(self):
    #     result = utils.upload_file("vplx", "/tmp", self.conn)
    #     if result["st"]:
    #         # cmd_pip = f'pip3 install -r /tmp/vplx/requirements.txt'
    #         # result_pip = utils.exec_cmd(cmd_pip, self.conn)
    #         # if not result_pip["st"]:
    #         #     print("Please install python module on /tmp/requirements.txt")
    #         return True


class Stor(object):
    def __init__(self, conn=None):
        self.conn = conn

    def get_drbd_status(self, resource):
        cmd = f'drbdadm status {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def check_drbd_quorum(self, resource):
        cmd = f'drbdsetup show {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        re_string = 'quorum\s+majority.*\s*on\s*-\s*no\s*-\s*quorum\s+io\s*-\s*error'
        if result["st"]:
            re_result = utils.re_search(self.conn, re_string, result["rt"], "bool")
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
        cmd = f'linstor n c {node} {ip} --node-type Combined'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def create_sp(self, node, sp, lvm_device):
        cmd = f'linstor sp c lvm {node} {sp} {lvm_device}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def create_rd(self,resource):
        cmd_rd = f'linstor rd c {resource}'
        utils.exec_cmd(cmd_rd, self.conn)

    def creare_vd(self,resource,size):
        cmd_vd = f'linstor vd c {resource} {size}'
        utils.exec_cmd(cmd_vd, self.conn)

    def create_diskful_resource(self, node_list, sp, resource):
        for node in node_list:
            cmd = f'linstor r c {node} {resource} --storage-pool {sp}'
            utils.exec_cmd(cmd, self.conn)

    def create_diskless_resource(self, node, resource):
        cmd = f'linstor r c {node} {resource} --diskless'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def create_crm_conf(self,crm_lincontrl_config):
        cmd = f'crm config load update {crm_lincontrl_config}'
        result = utils.exec_cmd(cmd, self.conn)
        cmd1 = f'crm res start vip p_iscsi_portblock_on p_iscsi_portblock_off t_test r0 g_linstor p_fs_linstordb p_linstor-controller  p_drbd_linstordb'
        utils.exec_cmd(cmd1,self.conn)

    def check_resource(self):
        cmd = "linstor r l"
        result = utils.exec_cmd(cmd,self.conn)
        a = re.findall(r'resourcetest01', result)
        b = re.findall(r'TieBreaker', result)
        if len(a) == 3 and b == []:
            print("Resource created successfully")
        else:
            print("Resource creation failed")

    def delete_resource(self, resource):
        cmd = f'linstor rd d {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def delete_sp(self, node, sp):
        cmd = f'linstor sp d {node} {sp}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def delete_node(self, node):
        cmd = f'linstor n d {node}'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    def get_device_name(self, resource):
        cmd = f'linstor r lv -r {resource}'
        result = utils.exec_cmd(cmd, self.conn)
        re_string = '/dev/drbd\d+'
        if result["st"]:
            re_result = utils.re_search(self.conn, re_string, result["rt"], "group")
            return re_result

    def get_linstor_res(self, resource):
        cmd = f'linstor r l -r {resource} -p'
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return result["rt"]

    # def check_vtel_result(self, result):
    #     re_string = f'SUCCESS|successfully created'
    #     re_result = utils.re_search(self.conn, re_string, result, "bool")
    #     return re_result


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
