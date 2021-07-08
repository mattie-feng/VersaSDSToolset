import time
import utils
import re


class IpService(object):
    def __init__(self, node):
        if node == utils.get_hostname():
            self.conn = None
        else:
            self.conn = utils.SSHConn(node)

    def set_ip(self, device, ip, gateway, netmask=24):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection add con-name {connection_name} type ethernet ifname {device} ipv4.addresses {ip}/{netmask} ipv4.gateway {gateway} ipv4.dns 114.114.114.114 ipv4.method manual"
        utils.exec_cmd(cmd, self.conn)

    def up_ip_service(self, device):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection up id {connection_name}"
        utils.exec_cmd(cmd, self.conn)

    def modify_ip(self, device, new_ip, gateway, netmask=24):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection modify {connection_name} ipv4.address {new_ip}/{netmask} ipv4.dns 114.114.114.114 ipv4.gateway {gateway}"
        utils.exec_cmd(cmd, self.conn)

    def set_bonding(self, device, type):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection add con-name {connection_name} type bond ifname {device} mode {type}"
        utils.exec_cmd(cmd, self.conn)

    def add_bond_slave(self, device):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection add type bond-slave ifname {device} master {connection_name}"
        utils.exec_cmd(cmd, self.conn)

    def down_connect(self, connection_name):
        cmd = f"nmcli connection down {connection_name}"
        utils.exec_cmd(cmd, self.conn)

    def del_connect(self, connection_name):
        # bond-slave-ens192
        cmd = f"nmcli connection delete {connection_name}"
        utils.exec_cmd(cmd, self.conn)
