import argparse
import sys
import os

import control
import utils
import consts



class VersaSDSTools():
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='main')
        self.setup_parser()



    def setup_parser(self):
        subp = self.parser.add_subparsers(metavar='',dest='subargs_vtel')


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

        self.parser.set_defaults(func=self.print_help)


    def print_help(self, args):
        self.parser.print_help()

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


    def main_usage(self, args):
        if args.version:
            print(f'Pacemaker Init: {consts.VERSION}')
        else:
            self.print_help(self.parser)




    def parse(self):  # 调用入口
        args = self.parser.parse_args()
        args.func(args)


    def delete_linstordb(self,args):
        controller = control.Scheduler()
        controller.get_ssh_conn()
        controller.destroy_linstordb()




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
    # sc = control.Scheduler()
    # sc.get_ssh_conn()
    # # sc.build_ha_controller()
    # # sc.backup_linstordb()
    # sc.destroy_linstordb()
    main()

