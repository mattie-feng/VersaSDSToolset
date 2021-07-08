import argparse
import sys
import os

sys.path.append('../')
import utils
import consts
import control


class IPTool():
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='main')
        self.setup_parser()

    def setup_parser(self):
        subp = self.parser.add_subparsers(metavar='', dest='subargs_vtel')

        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')

        parser_bonding = subp.add_parser("bonding", help="bonding operation")
        parser_ip = subp.add_parser("ip", help="ip operation")

        subp_bonding = parser_bonding.add_subparsers()
        parser_apply = subp_bonding.add_parser('apply', help='apply config file')
        parser_apply.add_argument('file', metavar='FILE', action='store', help='YAML file with IP config')

        # Bonding function
        parser_apply.set_defaults(func=self.apply_file)

        self.parser.set_defaults(func=self.main_usage)

    def print_help(self, args):
        self.parser.print_help()

    def main_usage(self, args):
        if args.version:
            print(f'Version: {consts.VERSION}')
        else:
            self.print_help(self.parser)

    def parse(self):  # 调用入口
        args = self.parser.parse_args()
        args.func(args)

    def apply_file(self, args):
        print(args.file)
        bonding = control.Bonding(args.file)
        bonding.create_bonding()


def main():
    if os.geteuid() != 0:
        print('This program must be run as root. Aborting.')
        sys.exit()
    try:
        cmd = IPTool()
        cmd.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")
    except PermissionError:
        sys.stderr.write("\nPermission denied (log file or other)\n")


if __name__ == '__main__':
    main()
