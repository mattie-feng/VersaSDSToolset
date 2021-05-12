import argparse
import sys
import os

import control
import utils



class VersaSDSInit():


    def __init__(self):
        self.parser = argparse.ArgumentParser(prog="init")
        self.setup_parser()

    def setup_parser(self):
        subp = self.parser.add_subparsers(metavar='',
                                     dest='subargs_vtel')


        self.parser.add_argument('-v',
                            '--version',
                            dest='version',
                            help='Show current version',
                            action='store_true')

        parser_run = subp.add_parser(
            'run',
            help='starting program',
        )

        # 可增加独项的
        parser_run.add_argument(
            '--corosync',
            help='Only do corosync work')


        parser_run.set_defaults(func=self.run)



        parser_show = subp.add_parser(
            'show',
            aliases='s',
            help='show configuration'
        )


        parser_show.set_defaults(func=self.show)
        self.parser.set_defaults(func=self.print_help)


    def run(self,args):
        controller = control.Scheduler()
        print('*start*')

        controller.get_ssh_conn()
        print('start to set private ip')
        control.set_ip_on_device()
        print('start to modify hostname')
        controller.modify_hostname()
        print('start to build ssh connect')
        controller.ssh_conn_build() # ssh免密授权
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

    def show(self,args):
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


    def print_help(self,*args):
        self.parser.print_help()

    def parse(self):  # 调用入口
        args = self.parser.parse_args()
        args.func(args)



def main():
    if os.geteuid() != 0:
        print('This program must be run as root. Aborting.')
        sys.exit()
    try:
        cmd = VersaSDSInit()
        cmd.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")
    except PermissionError:
        sys.stderr.write("\nPermission denied (log file or other)\n")



if __name__  == '__main__':
    # sc = control.Scheduler()
    # sc.get_ssh_conn()
    # sc.modify_hostname()
    # sc.ssh_conn_build()
    main()
