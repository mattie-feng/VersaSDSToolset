# -*- coding:utf-8 -*-
# import time
# import re
import subprocess
import os


def exec_cmd(cmd):
    """subprocess执行命令"""
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if p.returncode == 0:
        result = p.stdout
        result = result.decode() if isinstance(result, bytes) else result
        # print("result", result)
        return {"st": True, "rt": result}
    else:
        print(f"  Failed to execute command: {cmd}")
        print("  Error", p.stderr)
        return {"st": False, "rt": p.stderr}


def get_file(path, type=None):
    """通过路径获取路径下的文件名"""
    file_list = []
    if type:
        for file in os.listdir(path):
            if os.path.splitext(file)[1] == f".{type}":
                file_list.append(file)
    else:
        return os.listdir(path)
    return file_list


class InstallSoftware(object):
    def __init__(self, password):
        self.password = password

    def update_apt(self):
        """更新apt"""
        cmd = f"echo {self.password} | sudo -S apt update -y"
        result = exec_cmd(cmd)
        if result["st"]:
            return True

    def install_network_manager(self):
        """安装network-manager"""
        cmd = f"echo {self.password} | sudo -S apt install network-manager -y"
        result = exec_cmd(cmd)
        if result["st"]:
            return True

    def set_nmcli_config(self):
        """设置使network-manager可用"""
        netplan_file = get_file("/etc/netplan", "yaml")
        cmd_modify_config = f"echo {self.password} | sudo -S sed -i 's/^managed=false/#managed=false\\nmanaged=true/g' /etc/NetworkManager/NetworkManager.conf"
        cmd_modify_renderer = f"echo {self.password} | sudo -S sed -i 's/renderer: networkd/renderer: NetworkManager/g' /etc/netplan/{netplan_file[0]}"
        cmd_apply = f"echo {self.password} | sudo -S netplan apply"
        cmd_restart_service = f"echo {self.password} | sudo -S systemctl restart network-manager.service"
        result_modify_config = exec_cmd(cmd_modify_config)
        if result_modify_config["st"]:
            result_modify_renderer = exec_cmd(cmd_modify_renderer)
            if result_modify_renderer["st"]:
                result_apply = exec_cmd(cmd_apply)
                if result_apply["st"]:
                    result_restart_service = exec_cmd(cmd_restart_service)
                    if result_restart_service["st"]:
                        return True

    def install_openssh_server(self):
        """安装openssh-server"""
        cmd = f"echo {self.password} | sudo -S apt install openssh-server -y"
        result = exec_cmd(cmd)
        if result["st"]:
            if self.start_openssh_service():
                return True

    def start_openssh_service(self):
        """启动openssh服务"""
        cmd = f"echo {self.password} | sudo -S /etc/init.d/ssh start"
        result = exec_cmd(cmd)
        if result["st"]:
            return True


class IpService(object):
    def __init__(self, password):
        self.password = password

    def set_local_ip(self, device, ip, gateway, netmask=24):
        """在对应的设备上设置IP地址"""
        connection_name = 'vtel_' + device
        cmd = f"echo {self.password} | sudo -S nmcli connection add con-name {connection_name} type ethernet ifname {device} ipv4.addresses {ip}/{netmask} ipv4.gateway {gateway} ipv4.method manual"
        result = exec_cmd(cmd)
        if result["st"]:
            return True

    def up_local_ip_service(self, device):
        """启用设置的IP"""
        connection_name = 'vtel_' + device
        cmd = f"echo {self.password} | sudo -S nmcli connection up id {connection_name}"
        result = exec_cmd(cmd)
        if result["st"]:
            return True


class RootConfig(object):
    def __init__(self, password):
        self.password = password

    def set_root_password(self, new_password):
        """设置root用户密码"""
        cmd = f"echo {self.password} | sudo -S su root | echo root:{new_password} | sudo -S chpasswd"
        result = exec_cmd(cmd)
        if result["st"]:
            return True

    def set_root_permit_login(self):
        """允许以root用户登录"""
        cmd = f"echo {self.password} | sudo sed -i 's/PermitRootLogin prohibit-password/#PermitRootLogin prohibit-password\\nPermitRootLogin yes/g' /etc/ssh/sshd_config"
        result = exec_cmd(cmd)
        if result["st"]:
            return True

    def restart_openssh_service(self):
        """启动openssh服务"""
        cmd = f"echo {self.password} | sudo -S /etc/init.d/ssh restart"
        result = exec_cmd(cmd)
        if result["st"]:
            return True
