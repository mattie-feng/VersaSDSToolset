import sys
import re
import utils
import action


class Bonding():
    def __init__(self):
        pass

    def create_bonding_by_file(self, file):
        """create bonding via yaml config file"""
        config = utils.ConfFile(file)
        host_config = config.get_config()
        for host in host_config:
            print('-' * 15, host[0], '-' * 15)
            self.create_bonding(host[0], host[1], host[2], host[3], host[4])

    def create_bonding(self, node, bonding_name, mode, device_list, new_ip):
        if not utils.check_ip(new_ip):
            sys.exit()
        bonding = action.IpService(node)
        connection = bonding.get_connection()
        if self.check_bonding_exist(f'vtel_{bonding_name}', connection):
            print(f"{bonding_name} already exists.")
            sys.exit()
        if bonding.set_bonding(bonding_name, mode):
            gateway = f"{'.'.join(new_ip.split('.')[:3])}.1"
            bonding.modify_ip(bonding_name, new_ip, gateway)
        for device in device_list:
            bonding_slave = bonding.add_bond_slave(f"{bonding_name}", device)
            if bonding_slave:
                bonding.up_ip_service(bonding_slave)
            else:
                print(f'Failed to add bond slave about {device}')
        bonding.up_ip_service(f'vtel_{bonding_name}')

    def del_bonding(self, node, device):
        bonding_name = f'vtel_{device}'
        bonding = action.IpService(node)
        connection = bonding.get_connection()
        if connection:
            slave_list = self.get_slave_via_bonding_name(bonding_name, connection)
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
                print("Started to delete bonding")
                if bonding.del_connect(bonding_name):
                    print(f" Success in deleting {bonding_name}")
                else:
                    print(f" Failed to delete {bonding_name}")
            else:
                print(f"There is no configuration to delete for {device}.")
        else:
            print("Can't get any configuration")

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

    def get_slave_via_bonding_name(self, bonding_name, string):
        slave_list = re.findall(f'({bonding_name}-slave-\S*)\s+\S+\s+\S+\s+\S+', string)
        return slave_list

    def check_bonding_exist(self, bonding_name, string):
        bonding_obj = re.search(f'({bonding_name}\S*)\s+\S+\s+bond\s+\S+', string)
        return bonding_obj
