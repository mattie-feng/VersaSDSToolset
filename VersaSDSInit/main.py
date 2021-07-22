import argparse
import sys
import os
import time

sys.path.append('../')
import control
import utils
import consts

from commands import (
    PacemakerCommands,
    LinstorCommands,
    CheckCommands,
    InstallCommands,
    BuildCommands
)



class VersaSDSTools():
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='main')
        self.subp = self.parser.add_subparsers(metavar='',dest='subargs_vtel')
        self._pacemaker_cmds = PacemakerCommands(self.subp)
        self._linstor_cmds = LinstorCommands(self.subp)
        self._check_cmds = CheckCommands(self.subp)
        self._install_cmds = InstallCommands(self.subp)
        self._build_cmds = BuildCommands(self.subp)
        self.setup_parser()

    def setup_parser(self):
        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')
        self.parser.set_defaults(func=self.main_usage)


        # cmd :build
        # parser_build = self.subp.add_parser("build",help="build all")
        # parser_build.set_defaults(func=self.build_all)


        # cmd: status
        parser_status = self.subp.add_parser(
            'status',
            aliases=['st'],
            help='Display the information of cluster/node system service and software'
        )
        parser_status.add_argument('node',nargs = '?',default = None)
        parser_status.set_defaults(func=self.show_status)

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

    def show_status(self,args):
        controller = control.VersaSDSSoftConsole()

        iter_service_status = controller.get_all_service_status()
        table_status = utils.Table()
        table_status.header = ['node', 'pacemaker', 'corosync', 'linstor-satellite', 'drbd', 'linstor-controller']
        for i in iter_service_status:
            if args.node:
                if args.node == i[0]:
                    table_status.add_data(i)
                    break
            else:
                table_status.add_data(i)


        iter_version = controller.get_version('sysos','syskernel','drbd','linstor','targetcli','pacemaker')
        table_version = utils.Table()
        table_version.header = ['node', 'os_system', 'kernel', 'drbd_kernel_version', 'linstor', 'targetcli', 'pacemaker']
        for i in iter_version:
            if args.node:
                if args.node == i[0]:
                    table_version.add_data(i)
                    break
            else:
                table_version.add_data(i)

        table_status.print_table()
        table_version.print_table()

    # def build_all(self,args):
    #     controller_lvm = control.LVMConsole()
    #     controller_linstor = control.LinstorConsole()
    #
    #     self._install_cmds.install_software(args)
    #     print("1. 安装软件完成")
    #     self._pacemaker_cmds.init_pacemaker_cluster(args)
    #     print("2. 配置pacemaker集群完成")
    #     controller_lvm.create_dirver_pool()
    #     print('创建PV/VG/LV成功')
    #     controller_linstor.create_conf_file()
    #     controller_linstor.create_nodes()
    #     print('创建节点成功')
    #     controller_linstor.create_pools()
    #     print('创建存储池pool0成功')
    #     self._pacemaker_cmds.conf_controller(args)
    #     print("3. HA Controller配置完成")


def main():
    if os.geteuid() != 0:
        print('This program must be run as root. Aborting.')
        sys.exit()
    try:
        cmd = VersaSDSTools()
        cmd.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")
    except PermissionError:
        sys.stderr.write("\nPermission denied (log file or other)\n")



if __name__  == '__main__':
    main()

