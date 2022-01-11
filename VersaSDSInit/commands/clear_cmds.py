import control


class ClearCommands():
    def __init__(self, sub_parser):
        self.subp = sub_parser
        self.parser = self.setup_parser()

    def setup_parser(self):
        parser_clear = self.subp.add_parser(
            'clear',
            help='clear VersaSDS configuration'
        )
        parser_clear.add_argument('node',nargs = '?',default = None)
        subp_clear = parser_clear.add_subparsers(dest='subargs_clear')

        p_crm = subp_clear.add_parser('crm', help = 'clear crm cluster resource')
        p_crm.add_argument('node',nargs = '?',default = None)
        p_crm.set_defaults(func=self.clear_crm)

        p_vg = subp_clear.add_parser('vg', help = 'clear vg')
        p_vg.set_defaults(func=self.clear_vg)

        p_corosync = subp_clear.add_parser('corosync', help = 'clear corosync')
        p_corosync.set_defaults(func=self.clear_corosync)

        p_linstordb = subp_clear.add_parser('linstordb', aliases=['ldb'], help='clear linstordb')
        p_linstordb.set_defaults(func=self.clear_linstordb)

        parser_clear.set_defaults(func=self.clear_all)

    @classmethod
    def clear_crm(self,args):
        sc = control.PacemakerConsole()
        print('清除 crm 集群的相关资源')
        sc.clear_crm_res(args.node)

    @classmethod
    def clear_crm_node(self,args):
        sc = control.PacemakerConsole()
        print("清除 crm 节点")
        sc.clear_crm_node()


    @classmethod
    def clear_vg(self,args):
        sc = control.LVMConsole()
        print('清除 vg')
        sc.remove_vg()

    @classmethod
    def clear_linstordb(self,args):
        controller = control.LinstorConsole()
        controller.destroy_linstordb()


    @classmethod
    def clear_corosync(self,args):
        sc = control.PacemakerConsole()
        print('恢复 corosync 配置文件')
        sc.recover_corosync_conf()

    @classmethod
    def restart_linstor(self,args):
        sc = control.LinstorConsole()
        print('重启 linstor 集群的 controller 和 satellite')
        sc.restart_linstor()

    @classmethod
    def clear_all(self,args):
        print('*start*')
        self.clear_crm(args)
        self.clear_vg(args)
        self.clear_corosync(args)
        self.clear_crm_node(args)
        self.restart_linstor(args)
        print('*success*')