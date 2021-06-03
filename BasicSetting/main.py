# -*- coding:utf-8 -*-
import argparse
import sys
import action

sys.path.append('../')
import consts


class InputParser(object):

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

    def collect_args(self, args):
        conf_args = {}
        ip = args.ip if args.ip else self.guide_check("IP", "10.203.1.78")
        device = args.device if args.device else self.guide_check("Device", "ens160")
        default_gateway = f"{'.'.join(ip.split('.')[:3])}.1"
        gateway = args.gateway if args.gateway else self.guide_check("Gateway", default_gateway)
        passwword = args.password if args.password else self.guide_check("User password", "password")
        rootpwd = args.rootpwd if args.rootpwd else self.guide_check("Root password", "password")

        conf_args["IP"] = ip
        conf_args["Device"] = device
        conf_args["Gateway"] = gateway
        conf_args["User password"] = passwword
        conf_args["Root password"] = rootpwd
        print(conf_args)

        return conf_args

    def guide_check(self, target, default):
        for i in range(3):
            a = input(f"Input the value of '{target}' (default [{default}]): ")
            if a.strip() == "":
                return default
            elif a.strip() == "exit":
                sys.exit()
            else:
                if target in ["Gateway", "IP"]:
                    if action.check_ip(a):
                        return a
                    else:
                        print(f"Please check the format of {target}.Enter again or Press CTRL+C to quit")
                else:
                    return a

    def run_fun(self, args):
        if args.version:
            print(f'Version: {consts.VERSION}')
        else:
            if args.ip:
                if not action.check_ip(args.ip):
                    print("\nPlease check the format of IP...\n")
                    sys.exit()
            if args.gateway:
                if not action.check_ip(args.gateway):
                    print("\nPlease check the format of Gateway...\n")
                    sys.exit()
            conf_args = self.collect_args(args)
            install = action.InstallSoftware(conf_args["User password"])
            root_config = action.RootConfig(conf_args["User password"])
            ip_service = action.IpService(conf_args["User password"])
            ssh_service = action.OpenSSHService(conf_args["User password"])
            print("\nPrepare to install software...")
            if install.update_apt():
                print("Start to install openssh-server")
                if install.install_software("openssh-server"):
                    print(" Start openssh service")
                    if ssh_service.oprt_ssh_service("start"):
                        print("Set can be logged as root")
                        if root_config.set_root_permit_login():
                            print("Set root password")
                            root_config.set_root_password(conf_args["Root password"])
                            print(" Restart openssh service")
                            ssh_service.oprt_ssh_service("restart")
                print("Start to install network-manager")
                if install.install_software("network-manager"):
                    print(" Start to set network-manager config")
                    if install.set_nmcli_config():
                        print(f"Set {conf_args['IP']} on the {conf_args['Device']}")
                        if ip_service.set_local_ip(conf_args['Device'], conf_args['IP'], conf_args['Gateway']):
                            ip_service.up_local_ip_service(conf_args['Device'])
                print("\n")
            else:
                sys.exit()

    def parse(self):  # 调用入口
        args = self.parser.parse_args()
        args.func(args)


def main():
    try:
        run_program = InputParser()
        run_program.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")


if __name__ == '__main__':
    main()
