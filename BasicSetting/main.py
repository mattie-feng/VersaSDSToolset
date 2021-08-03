# -*- coding:utf-8 -*-
import argparse
import sys
import control
import utils

sys.path.append('../')
import consts


class InputParser(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Basic Setting for operating system")
        self.setup_parser()
        self.conf_args = {}

    def setup_parser(self):

        subp = self.parser.add_subparsers(metavar='', dest='subargs_vtel')

        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')

        self.parser_build = subp.add_parser("build", aliases=['b'], help="Install software and set basic configuration")

        self.parser_build.add_argument('-ip',
                                       '--ip',
                                       dest='ip',
                                       help='IP address',
                                       action='store')

        self.parser_build.add_argument('-d',
                                       '--device',
                                       dest='device',
                                       help='Device',
                                       action='store')

        self.parser_build.add_argument('-g',
                                       '--gateway',
                                       dest='gateway',
                                       help='Gateway',
                                       action='store')

        self.parser_build.add_argument('-p',
                                       '--password',
                                       dest='password',
                                       help='Password of current user',
                                       action='store')
        self.parser_build.add_argument('-r',
                                       '--rootpwd',
                                       dest='rootpwd',
                                       help='Password of root that you want to set',
                                       action='store')

        self.parser_ip = subp.add_parser("ip", help="Connection IP settings (based on network-manager)")

        self.parser_ip.add_argument('-ip',
                                    '--ip',
                                    dest='ip',
                                    help='IP address',
                                    action='store')

        self.parser_ip.add_argument('-d',
                                    '--device',
                                    dest='device',
                                    help='Device',
                                    action='store')

        self.parser_ip.add_argument('-g',
                                    '--gateway',
                                    dest='gateway',
                                    help='Gateway',
                                    action='store')

        self.parser_ip.add_argument('-p',
                                    '--password',
                                    dest='password',
                                    help='Password of current user',
                                    action='store')

        self.parser_root = subp.add_parser("root", aliases=['r'],
                                           help="Set the root password and allow the root user to log in")

        self.parser_root.add_argument('-r',
                                      '--rootpwd',
                                      dest='rootpwd',
                                      help='Password of root that you want to set',
                                      action='store')
        self.parser_root.add_argument('-p',
                                      '--password',
                                      dest='password',
                                      help='Password of current user',
                                      action='store')

        self.parser_build.set_defaults(func=self.run_func)
        self.parser_ip.set_defaults(func=self.ip_func)
        self.parser_root.set_defaults(func=self.root_func)
        self.parser.set_defaults(func=self.help_usage)

    def collect_ip_args(self, args):
        ip = args.ip if args.ip else utils.guide_check("IP", "10.203.1.78")
        if ip:
            default_gateway = f"{'.'.join(ip.split('.')[:3])}.1"
            gateway = args.gateway if args.gateway else utils.guide_check("Gateway", default_gateway)
            if not gateway:
                sys.exit()
            device = args.device if args.device else utils.guide_check("Device", "ens160")
        else:
            sys.exit()

        self.conf_args["IP"] = ip
        self.conf_args["Gateway"] = gateway
        self.conf_args["Device"] = device

    def collect_root_args(self, args):
        rootpwd = args.rootpwd if args.rootpwd else utils.guide_check("Root password", "password")
        self.conf_args["Root password"] = rootpwd

    def collect_args(self, args, type):
        if type == "all":
            self.collect_ip_args(args)
            self.collect_root_args(args)
        if type == "ip":
            self.collect_ip_args(args)
        if type == "root":
            self.collect_root_args(args)
        password = args.password if args.password else utils.guide_check("User password", "password")
        self.conf_args["User password"] = password

        print(f"\nConfiguration: {self.conf_args}")

    def run_func(self, args):
        self.check_ip_and_gateway(args)
        self.collect_args(args, "all")
        control.all_deploy(self.conf_args)

    def ip_func(self, args):
        self.check_ip_and_gateway(args)
        self.collect_args(args, "ip")
        control.set_local_ip(self.conf_args)

    def root_func(self, args):
        self.collect_args(args, "root")
        control.set_root_pwd_permit_login(self.conf_args)

    def check_ip_and_gateway(self, args):
        if args.ip:
            if not utils.check_ip(args.ip):
                print("\nPlease check the format of IP...\n")
                sys.exit()
        if args.gateway:
            if not utils.check_ip(args.gateway):
                print("\nPlease check the format of Gateway...\n")
                sys.exit()

    def help_usage(self, args):
        if args.version:
            print(f'Version: {consts.VERSION}')
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


if __name__ == '__main__':
    main()
