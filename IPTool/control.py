# -*- coding: utf-8 -*-
import sys
import re
import utils
import action


class Bonding(object):
    def __init__(self):
        self.modify_mode = False

    def configure_bonding_by_file(self, file):
        """create or modify bonding via yaml config file"""
        config = utils.ConfFile(file)
        host_config = config.get_config()
        self.modify_mode = True
        for host in host_config:
            node = host[0]
            bonding_name = host[1]
            mode = host[2]
            device_list = host[3]
            new_ip = host[4]
            print('-' * 15, node, '-' * 15)
            bonding = action.IpService(node)
            lc_device_date = bonding.get_device_status()
            if not self.check_device(device_list, lc_device_date):
                continue
            connection = bonding.get_connection()
            if self.check_bonding_exist(f'vtel_{bonding_name}', connection):
                print(f"Modify {bonding_name}.")
                self.modify_bonding_slave(node, bonding_name, device_list)
                self.modify_bonding_mode(node, bonding_name, mode)
                self.modify_bonding_ip(node, bonding_name, new_ip)
            else:
                print(f"Create {bonding_name}.")
                self.create_bonding(node, bonding_name, mode, device_list, new_ip)

    def create_bonding(self, node, bonding_name, mode, device_list, new_ip):
        bonding = action.IpService(node)
        if not self.modify_mode:
            connection = bonding.get_connection()
            if self.check_bonding_exist(f'vtel_{bonding_name}', connection):
                print(f"{bonding_name} already exists.")
                sys.exit()
            if not utils.check_ip(new_ip):
                sys.exit()
            lc_device_date = bonding.get_device_status()
            if not self.check_device(device_list, lc_device_date):
                sys.exit()
        if bonding.set_bonding(bonding_name, mode):
            gateway = f"{'.'.join(new_ip.split('.')[:3])}.1"
            bonding.modify_ip(bonding_name, new_ip, gateway)
            if mode == "802.3ad":
                bonding.add_bond_options(bonding_name, "xmit_hash_policy=layer3+4")
                bonding.add_bond_options(bonding_name, "miimon=100")
                bonding.add_bond_options(bonding_name, "lacp_rate=fast")
        for device in device_list:
            bonding_slave = bonding.add_bond_slave(bonding_name, device)
            if bonding_slave:
                bonding.up_ip_service(bonding_slave)
            else:
                print(f'Failed to add bond slave about {device}')
        bonding.up_ip_service(f'vtel_{bonding_name}')

    def modify_bonding_mode(self, node, device, mode):
        bonding = action.IpService(node)
        if not self.modify_mode:
            connection = bonding.get_connection()
            if not self.check_bonding_exist(f'vtel_{device}', connection):
                print(f"{device} does not exist. Do nothing.")
                sys.exit()
        lc_mode = bonding.get_mode(device)
        if not self.check_mode(lc_mode, mode):
            print("Change bonding mode.")
            if self.check_mode(lc_mode, "802.3ad"):
                bonding.delete_bond_options(device, "lacp_rate")
                bonding.delete_bond_options(device, "xmit_hash_policy")
                bonding.delete_bond_options(device, "miimon")
            bonding.modify_bonding_mode(device, mode)
            if mode == "802.3ad":
                bonding.add_bond_options(device, "xmit_hash_policy=layer3+4")
                bonding.add_bond_options(device, "miimon=100")
                bonding.add_bond_options(device, "lacp_rate=fast")
            bonding.up_ip_service(f'vtel_{device}')
        else:
            if not self.modify_mode:
                print("Same bonding mode. Do nothing.")

    def modify_bonding_ip(self, node, device, ip):
        bonding = action.IpService(node)
        if not self.modify_mode:
            if not utils.check_ip(ip):
                sys.exit()
            connection = bonding.get_connection()
            if not self.check_bonding_exist(f'vtel_{device}', connection):
                print(f"{device} does not exist. Do nothing.")
                sys.exit()
        lc_ip_data = bonding.get_bond_ip(device)
        if not self.check_bond_ip(ip, lc_ip_data):
            print("Change bonding IP.")
            gateway = f"{'.'.join(ip.split('.')[:3])}.1"
            bonding.modify_ip(device, ip, gateway)
            bonding.up_ip_service(f'vtel_{device}')
        else:
            if not self.modify_mode:
                print("Same bonding IP. Do nothing.")

    def modify_bonding_slave(self, node, bonding_name, device_list):
        bonding = action.IpService(node)
        if not self.modify_mode:
            connection = bonding.get_connection()
            if not self.check_bonding_exist(f'vtel_{bonding_name}', connection):
                print(f"{bonding_name} does not exist. Do nothing.")
                sys.exit()
            lc_device_date = bonding.get_device_status()
            if not self.check_device(device_list, lc_device_date):
                sys.exit()
        connection = bonding.get_connection()
        slave_list = self.get_slave_via_bonding_name(bonding_name, connection)
        device_slave_list = [f'vtel_{bonding_name}-slave-{i}' for i in device_list]
        # list_retain = [i for i in device_list if i in slave_list]
        list_create = [i for i in device_list if f'vtel_{bonding_name}-slave-{i}' not in slave_list]
        list_delete = [i for i in slave_list if i not in device_slave_list]
        if list_create or list_delete:
            print("Change bonding salve device.")
            for device in list_create:
                bonding_slave = bonding.add_bond_slave(bonding_name, device)
                bonding.up_ip_service(bonding_slave)
            for delete_salve in list_delete:
                bonding.down_connect(delete_salve)
                bonding.del_connect(delete_salve)
            bonding.up_ip_service(f'vtel_{bonding_name}')
        else:
            if not self.modify_mode:
                print("Same Device. Do nothing.")

    def del_bonding(self, node, device):
        bonding_name = f'vtel_{device}'
        bonding = action.IpService(node)
        connection = bonding.get_connection()
        if connection:
            slave_list = self.get_slave_via_bonding_name(device, connection)
            if slave_list:
                print("Started to delete bonding slave")
                for slave in slave_list:
                    bonding.down_connect(slave)
                    if bonding.del_connect(slave):
                        print(f" Success in deleting {slave}")
                    else:
                        print(f" Failed to delete {slave}")
            if self.check_bonding_exist(bonding_name, connection):
                bonding.down_connect(bonding_name)
                print(f"Started to delete {bonding_name}")
                if bonding.del_connect(bonding_name):
                    print(f" Success in deleting {bonding_name}")
                else:
                    print(f" Failed to delete {bonding_name}")
            else:
                print(f"There is no configuration to delete for {device}.")
        else:
            print("Can't get any configuration")

    def get_slave_via_bonding_name(self, bonding_name, string):
        slave_list = re.findall(f'(vtel_{bonding_name}-slave-\S*)\s+\S+\s+\S+\s+\S+', string)
        return slave_list

    def check_bonding_exist(self, bonding_name, string):
        bonding_obj = re.search(f'({bonding_name})\s+\S+\s+bond\s+\S+', string)
        if bonding_obj:
            return True

    def check_mode(self, local_mode, conf_mode):
        if conf_mode == 'balance-rr':
            conf_mode = "load balancing (round-robin)"
        if conf_mode in local_mode:
            return True

    def check_bond_ip(self, tg_ip, lc_ip_data):
        "Eg. lc_ip_data: IP4.ADDRESS[1]:                         10.203.1.76/24"
        ip_obj = re.search(r'\d+\.\d+\.\d+\.\d+', lc_ip_data)
        if ip_obj:
            if ip_obj.group() == tg_ip:
                return True

    def check_device(self, device_list, lc_device_data):
        flag = True
        for device in device_list:
            if device not in lc_device_data:
                print(f"没有{device}, 不能进行bond配置.")
                flag = False
        return flag
