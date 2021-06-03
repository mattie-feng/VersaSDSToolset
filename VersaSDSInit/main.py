import argparse
import sys
import os

sys.path.append('../')
import control
import utils
import consts



class VersaSDSTools():
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='main')
        self.setup_parser()



    def setup_parser(self):
        subp = self.parser.add_subparsers(metavar='',dest='subargs_vtel')

        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')

        # cmd:parser
        parser_pc = subp.add_parser(
            'pacemaker',
            aliases=['pc'],
            help='Pacemaker cluster operation'
        )

        # Build command: pacemaker
        subp_pc = parser_pc.add_subparsers()
        parser_pc_init = subp_pc.add_parser('init',help='Initialize pacemaker cluster')

        parser_pc_controller = subp_pc.add_parser('controller',aliases=['con'],help='Configure HA linstor-controller')
        parser_pc_show = subp_pc.add_parser('show',help='View pacemaker cluster status')

        # Binding function
        parser_pc_init.set_defaults(func=self.init_pacemaker_cluster)
        parser_pc_controller.set_defaults(func=self.conf_controller)
        parser_pc_show.set_defaults(func=self.show_pacemaker_cluster)

        # Build command: linstor
        parser_ls = subp.add_parser(
            'linstor',
            aliases=['ls'],
            help='Linstor cluster operation'
        )


        subp_ls = parser_ls.add_subparsers()
        parser_ls_bk = subp_ls.add_parser('backup',aliases=['bk'],help='Backup linstor cluster')
        parser_ls_del = subp_ls.add_parser('del',aliases=['d'],help='Clear linstordb')

        # Binding function
        parser_ls_bk.set_defaults(func=self.backup_linstor)
        parser_ls_del.set_defaults(func=self.delete_linstordb)

        # Build command: install
        parser_install = subp.add_parser(
            'install',
            help='Install VersaSDS software'
        )
        parser_install.set_defaults(func=self.install_soft)


        # Build command: status
        parser_status = subp.add_parser(
            'status',
            aliases=['st'],
            help='Display the information of cluster/node system service and software'
        )
        parser_status.add_argument('node',nargs = '?',default = None)
        parser_status.set_defaults(func=self.show_status)


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


    def init_pacemaker_cluster(self, args):
        controller = control.Scheduler()
        print('*start*')

        controller.get_ssh_conn()
        print('start to set private ip')
        controller.set_ip_on_device()
        print('start to modify hostname')
        controller.modify_hostname()
        print('start to build ssh connect')
        controller.ssh_conn_build()  # ssh免密授权
        print('start to synchronised time')
        controller.sync_time()
        print('start to set up corosync')
        controller.corosync_conf_change()
        print('start to restart corosync')
        controller.restart_corosync()

        print('check corosync, please wait')
        if all(controller.check_corosync()):
            print('start to set up packmaker')
            controller.packmaker_conf_change()
        else:
            print('corosync configuration failed')
            sys.exit()

        if all(controller.check_packmaker()):
            print('start to set up targetcli')
            controller.targetcli_conf_change()
        else:
            print('pacemaker configuration failed')
            sys.exit()

        if all(controller.check_targetcli()):
            print('start to set up service')
            controller.service_set()
        else:
            print('service configuration failed')
            sys.exit()

        if all(controller.check_targetcli()):
            print('start to replace RA')
            controller.replace_ra()
        else:
            print('RA replace failed')
            sys.exit()

        print('*success*')

    def show_pacemaker_cluster(self, args):
        controller = control.Scheduler()
        controller.get_ssh_conn()

        conf = utils.ConfFile()
        l_node = [i['hostname'] for i in conf.cluster['node']]
        l_ssh = ['T' if i else 'F' for i in controller.check_ssh_authorized()]
        l_hostname = ['T' if i else 'F' for i in controller.check_hostname()]
        l_corosync = ['T' if i else 'F' for i in controller.check_corosync()]
        l_packmaker = ['T' if i else 'F' for i in controller.check_packmaker()]
        l_targetcli = ['T' if i else 'F' for i in controller.check_targetcli()]
        l_service = ['T' if i else 'F' for i in controller.check_service()]

        table = utils.Table()
        table.header = ['node', 'ssh', 'hostname', 'corosync', 'pacemaker', 'targetcli', 'service']
        for i in range(len(l_node)):
            table.add_data(
                [l_node[i], l_ssh[i], l_hostname[i], l_corosync[i], l_packmaker[i], l_targetcli[i], l_service[i]])

        table.print_table()

    def conf_controller(self, args):
        controller = control.Scheduler()
        controller.get_ssh_conn()
        print('*start*')
        controller.build_ha_controller()
        print('Finish configuration，checking')
        if not controller.check_ha_controller():
            print('Fail，exit')
            sys.exit()
        print('*success*')

    def backup_linstor(self, args):
        controller = control.Scheduler()
        controller.get_ssh_conn()
        print('*start*')
        if controller.backup_linstordb():
            print('Success')
        else:
            print('Fail，exit')
            sys.exit()
        print('*success*')

    def install_soft(self,args):
        sc = control.VersaSDSSoft()
        sc.get_ssh_conn()
        print('*start*')
        print('添加linbit-drbd库，并更新')
        sc.install_spc()
        sc.apt_update()
        print('开始安装drbd相关软件')
        sc.set_noninteractive()
        sc.install_drbd()
        print('开始linstor安装')
        sc.install_linstor()
        print('开始lvm安装')
        sc.install_lvm2()
        print('开始pacemaker相关软件安装')
        sc.install_pacemaker()
        print('开始targetcli安装')
        sc.install_targetcli()
        print('*success*')

    def delete_linstordb(self,args):
        controller = control.Scheduler()
        controller.get_ssh_conn()
        controller.destroy_linstordb()


    def show_status(self,args):
        controller = control.VersaSDSSoft()
        controller.get_ssh_conn()

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


        iter_version = controller.get_all_version()
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
    # sc = control.VersaSDSSoft()
    # sc.get_ssh_conn()
    # # # sc.build_ha_controller()
    # # # sc.backup_linstordb()
    # # sc.destroy_linstordb()
    main()

