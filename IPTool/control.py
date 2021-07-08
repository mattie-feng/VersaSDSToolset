import gevent
from gevent import monkey
import time
import sys
import re

import utils
import action


class Bonding():
    def __init__(self):
        pass

    def create_bonding_by_file(self, file):
        config = utils.ConfFile(file)
        host_config = config.get_config()
        for host in host_config:
            print('-' * 15, host[0], '-' * 15)
            self.create_bonding(host[0], host[1], host[2], host[3], host[4])

    def create_bonding(self, node, bonding_name, mode, device_list, new_ip):
        if not utils.check_ip(new_ip):
            sys.exit()
        bonding = action.IpService(node)
        if bonding.set_bonding(bonding_name, mode):
            gateway = f"{'.'.join(new_ip.split('.')[:3])}.1"
            bonding.modify_ip(bonding_name, new_ip, gateway)
        for device in device_list:
            bonding_slave = bonding.add_bond_slave(f"vtel_{bonding_name}", device)
            if bonding_slave:
                bonding.up_ip_service(bonding_slave)
            else:
                print(f'Failed to add bond slave at {device}')
        bonding.up_ip_service(f'vtel_{bonding_name}')

    def del_bonding(self, node, device):
        bonding_name = f'vtel_{device}'
        bonding = action.IpService(node)
        connection = bonding.get_connection()
        if connection:
            slave_list = re.findall(f'({bonding_name}-slave-\S*)\s+\S+\s+\S+\s+\S+', connection)
            bonding_list = re.findall(f'({bonding_name}\S*)\s+\S+\s+bond\s+\S+', connection)
            if slave_list:
                for slave in slave_list:
                    bonding.down_connect(slave)
                    if bonding.del_connect(slave):
                        print(f"Success in deleting {slave}")
                    else:
                        print(f"Failed to delete {slave}")
            if bonding_list:
                for bonding_name in bonding_list:
                    bonding.down_connect(bonding_name)
                    if bonding.del_connect(bonding_name):
                        print(f"Success in deleting {bonding_name}")
                    else:
                        print(f"Failed to delete {bonding_name}")
            else:
                print(f"{device} have no config to delete.")
        else:
            print("Can't get any connection")

    def modify_bonding_mode(self, node, device, mode):
        bonding = action.IpService(node)
        bonding.modify_bonding_mode(device, mode)
        bonding.up_ip_service(f'vtel_{device}')
        bonding.print_mode(device)
        # if bonding.down_connect(f'vtel_{device}'):
        #     if bonding.modify_bonding_mode(device, mode):
        #         print(f'Success in modify {device} mode of {mode}')
        # else:
        #     print(f"Failed to modify {device} mode of {mode}")
