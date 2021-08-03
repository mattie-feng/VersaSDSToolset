# -*- coding:utf-8 -*-
import utils


class InstallSoftware(object):
    def __init__(self, password):
        self.password = password

    def update_apt(self):
        """更新apt"""
        cmd = f"echo {self.password} | sudo -S apt update -y"
        result = utils.exec_cmd(cmd)
        if result["st"]:
            return True

    def install_software(self, name):
        """根据软件名安装对应软件"""
        cmd = f"echo {self.password} | sudo -S apt install {name} -y"
        result = utils.exec_cmd(cmd)
        if result["st"]:
            return True

    def set_nmcli_config(self):
        """设置使network-manager可用"""
        netplan_file = utils.get_file("/etc/netplan", "yaml")
        cmd_modify_config = f"echo {self.password} | sudo -S sed -i 's/^managed=false/#managed=false\\nmanaged=true/g' /etc/NetworkManager/NetworkManager.conf"
        cmd_modify_renderer = f"echo {self.password} | sudo -S sed -i 's/renderer: networkd/renderer: NetworkManager/g' /etc/netplan/{netplan_file[0]}"
        cmd_apply = f"echo {self.password} | sudo -S netplan apply"
        cmd_restart_service = f"echo {self.password} | sudo -S systemctl restart network-manager.service"
        result_modify_config = utils.exec_cmd(cmd_modify_config)
        if result_modify_config["st"]:
            result_modify_renderer = utils.exec_cmd(cmd_modify_renderer)
            if result_modify_renderer["st"]:
                result_apply = utils.exec_cmd(cmd_apply)
                if result_apply["st"]:
                    result_restart_service = utils.exec_cmd(cmd_restart_service)
                    if result_restart_service["st"]:
                        return True


class OpenSSHService(object):
    def __init__(self, password):
        self.password = password

    def oprt_ssh_service(self, status):
        """启动、停止、重启openssh服务"""
        cmd = f"echo {self.password} | sudo -S /etc/init.d/ssh {status}"
        result = utils.exec_cmd(cmd)
        if result["st"]:
            return True


class IpService(object):
    def __init__(self, password):
        self.password = password

    def set_local_ip(self, device, ip, gateway, netmask=24):
        """设置连接的IP地址"""
        connection_name = 'vtel_' + device
        cmd = f"echo {self.password} | sudo -S nmcli connection add con-name {connection_name} type ethernet ifname {device} ipv4.addresses {ip}/{netmask} ipv4.gateway {gateway} ipv4.dns 114.114.114.114 ipv4.method manual"
        result = utils.exec_cmd(cmd)
        if result["st"]:
            return True

    def up_local_ip_service(self, device):
        """启用设置的IP"""
        connection_name = 'vtel_' + device
        cmd = f"echo {self.password} | sudo -S nmcli connection up id {connection_name}"
        result = utils.exec_cmd(cmd)
        if result["st"]:
            return True


class RootConfig(object):
    def __init__(self, password):
        self.password = password

    def set_root_password(self, new_password):
        """设置root用户密码"""
        cmd = f"echo {self.password} | sudo -S su root | echo root:{new_password} | sudo -S chpasswd"
        result = utils.exec_cmd(cmd)
        if result["st"]:
            return True

    def set_root_permit_login(self):
        """允许以root用户登录"""
        cmd = f"echo {self.password} | sudo sed -i 's/PermitRootLogin prohibit-password/#PermitRootLogin prohibit-password\\nPermitRootLogin yes/g' /etc/ssh/sshd_config"
        result = utils.exec_cmd(cmd)
        if result["st"]:
            return True
