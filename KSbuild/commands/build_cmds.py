import control
import argparse
import sys

INSTALL_FLAG = False


class BuildCommands(object):
    def __init__(self, sub_parser):
        self.subp = sub_parser
        self.setup_parser()

    def setup_parser(self):
        parser_build = self.subp.add_parser("build", aliases=['b'],
                                            help="Configure the components of the pacemaker cluster")
        parser_build.set_defaults(func=self.build_all)
        parser_build.add_argument(
            '-test',
            dest='test',
            action='store_true',
            help=argparse.SUPPRESS,
            default=False)

        subp_build = parser_build.add_subparsers(dest='subargs_build')

        p_corosync = subp_build.add_parser('HA', aliases=['ha'], help='build corosync')
        p_corosync.set_defaults(func=self.build_ha)

        p_pacemaker = subp_build.add_parser('cluster', aliases=['c'], help='build pacemaker')
        p_pacemaker.set_defaults(func=self.build_cluster)

    def build_all(self, args):
        self.build_ha(args)
        self.build_cluster(args)

    def build_cluster(self, args):
        self.change_sources(args)
        controller = control.KSConsole()
        print("Build cluster")
        controller.set_swap()
        # if args.test:
        #     print('Add linbit-drbd ...')
        #     controller.install_drbd_spc()
        controller.install_docker(args.test)
        controller.install()
        controller.create_linstor_conf_file()
        controller.add_to_linstor_cluster()
        controller.modify_kk()
        controller.build_ks()
        controller.set_linstor_server()

    def build_ha(self, args):
        self.change_sources(args)
        controller = control.KSConsole()
        print("Configure HAproxy ...")
        controller.install_haproxy()
        controller.modify_haproxy()
        controller.restart_haproxy()

        print("Configure Keepalived ...")
        controller.install_keepalived()
        controller.modify_keepalived()
        controller.restart_keepalived()

    def change_sources(self, args):
        global INSTALL_FLAG
        controller = control.KSConsole()
        if not INSTALL_FLAG:
            if args.test:
                controller.replace_linbit_sources()
            else:
                controller.replace_sources()
            controller.bak_sources_files()
            print("Update apt ...")
            controller.apt_update()
        INSTALL_FLAG = True
