import argparse
import sys

import action
import consts


class InputParser():

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Basic Setting of System")
        self.setup_parser()

    def setup_parser(self):

        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')

        self.parser.add_argument('-ip',
                                 '--ip',
                                 dest='ip',
                                 help='IP address',
                                 action='store')

        self.parser.add_argument('-d',
                                 '--device',
                                 dest='device',
                                 help='Device',
                                 action='store')

        self.parser.add_argument('-g',
                                 '--gateway',
                                 dest='gateway',
                                 help='Gateway',
                                 action='store')

        self.parser.add_argument('-p',
                                 '--password',
                                 dest='password',
                                 help='Password of current user',
                                 action='store')
        self.parser.add_argument('-r',
                                 '--rootpwd',
                                 dest='rootpwd',
                                 help='Password of root that you want to set',
                                 action='store')

        self.parser.set_defaults(func=self.run_fun)

    def run_fun(self, args):
        if args.version:
            print(f'Version: {consts.VERSION}')
        elif args.ip and args.device and args.gateway and args.password and args.rootpwd:
            install = action.InstallSoftware(args.password)
            root_config = action.RootConfig(args.password)
            ip_service = action.IpService(args.password)
            print("Prepare to install software")
            if install.update_apt():
                print(" Start to install network-manager")
                if install.install_network_manager():
                    if install.set_nmcli_config():
                        print("  Set IP on the device")
                        if ip_service.set_local_ip(args.device, args.ip, args.gateway):
                            ip_service.up_local_ip_service(args.device)
                print(" Start to install openssh-server")
                if install.install_openssh_server():
                    print("  Set can be logged as root")
                    if root_config.set_root_permit_login():
                        print("  Set root password")
                        root_config.set_root_password(args.rootpwd)
                        print("  Restart openssh service")
                        root_config.restart_openssh_service()
            else:
                sys.exit()
        else:
            self.parser.print_help()

    def parse(self):  # 调用入口
        args = self.parser.parse_args()
        args.func(args)


def main():
    try:
        run_program = InputParser()
        run_program.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")
    except PermissionError:
        sys.stderr.write("\nPermission denied (log file or other)\n")


if __name__ == '__main__':
    # sc = control.Scheduler()
    # sc.get_ssh_conn()
    # sc.modify_hostname()
    # sc.ssh_conn_build()
    # sc.check_corosync()
    # sc.packmaker_conf_change()
    main()
