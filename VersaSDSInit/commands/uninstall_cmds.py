import control


class UninstallCommands():
    def __init__(self, sub_parser):
        self.subp = sub_parser
        self.parser = self.setup_parser()

    def setup_parser(self):
        parser_install = self.subp.add_parser(
            'uninstall',
            help='Uninstall VersaSDS software'
        )
        subp_install = parser_install.add_subparsers(dest='subargs_uninstall')

        p_linbit = subp_install.add_parser('linbit', help = 'uninstall software of linbit')
        p_linbit.set_defaults(func=self.uninstall_linbit)

        p_lvm2 = subp_install.add_parser('lvm2', help = 'uninstall lvm2')
        p_lvm2.set_defaults(func=self.uninstall_lvm2)

        p_pacemaker = subp_install.add_parser('pacemaker', help = 'uninstall pacemaker')
        p_pacemaker.set_defaults(func=self.uninstall_pacemaker)

        p_targetcli = subp_install.add_parser('targetcli', help = 'uninstall targetcli')
        p_targetcli.set_defaults(func=self.uninstall_targetcli)

        parser_install.set_defaults(func=self.uninstall_software)

    @classmethod
    def uninstall_linbit(self,args):
        sc = control.VersaSDSSoftConsole()
        print('卸载drbd相关软件')
        sc.uninstall_drbd()
        print('卸载linstor')
        sc.uninstall_linstor()

    @classmethod
    def uninstall_lvm2(self,args):
        sc = control.VersaSDSSoftConsole()
        print('卸载lvm')
        sc.uninstall_lvm2()

    @classmethod
    def uninstall_pacemaker(self,args):
        sc = control.VersaSDSSoftConsole()
        print('卸载pacemaker相关软件')
        sc.uninstall_pacemaker()

    @classmethod
    def uninstall_targetcli(self,args):
        sc = control.VersaSDSSoftConsole()
        print('卸载targetcli')
        sc.uninstall_targetcli()

    @classmethod
    def uninstall_software(self,args):
        print('*start*')
        self.uninstall_lvm2(args)
        self.uninstall_linbit(args)
        self.uninstall_pacemaker(args)
        self.uninstall_targetcli(args)
        print('*success*')