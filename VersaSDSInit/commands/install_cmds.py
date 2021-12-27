import sys
import control


class InstallCommands():
    def __init__(self, sub_parser):
        self.subp = sub_parser
        self.parser = self.setup_parser()

    def setup_parser(self):
        parser_install = self.subp.add_parser(
            'install',
            help='Install VersaSDS software'
        )
        subp_install = parser_install.add_subparsers(dest='subargs_install')

        p_linbit = subp_install.add_parser('linbit', help = 'install software of linbit')
        p_linbit.set_defaults(func=self.install_linbit)

        p_lvm2 = subp_install.add_parser('lvm2', help = 'install lvm2')
        p_lvm2.set_defaults(func=self.install_lvm2)

        p_pacemaker = subp_install.add_parser('pacemaker', help = 'install pacemaker')
        p_pacemaker.set_defaults(func=self.install_pacemaker)

        p_targetcli = subp_install.add_parser('targetcli', help = 'install targetcli')
        p_targetcli.set_defaults(func=self.install_targetcli)

        parser_install.set_defaults(func=self.install_software)

    @classmethod
    def install_linbit(self,args):
        sc = control.VersaSDSSoftConsole()
        print('添加linbit-drbd库，并更新')
        result = sc.install_spc()
        if not all(result):
            print("添加linbit-drbd库失败，退出")
            sys.exit(1)
        sc.apt_update()
        print('开始安装drbd相关软件')
        sc.install_drbd()
        print('开始linstor安装')
        sc.install_linstor()

    @classmethod
    def install_lvm2(self,args):
        sc = control.VersaSDSSoftConsole()
        print('开始lvm安装')
        sc.install_lvm2()

    @classmethod
    def install_pacemaker(self,args):
        sc = control.VersaSDSSoftConsole()
        print('开始pacemaker相关软件安装')
        sc.install_pacemaker()

    @classmethod
    def install_targetcli(self,args):
        sc = control.VersaSDSSoftConsole()
        print('开始targetcli安装')
        sc.install_targetcli()

    @classmethod
    def install_software(self,args):
        print('*start*')
        self.install_linbit(args)
        self.install_lvm2(args)
        self.install_pacemaker(args)
        self.install_targetcli(args)
        print('*success*')