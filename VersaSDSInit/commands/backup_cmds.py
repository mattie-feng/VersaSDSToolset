import sys
import time

import control
import utils



class BackupCommands():
    def __init__(self,sub_parser):
        self.subp = sub_parser
        self.setup_parser()


    def setup_parser(self):
        parser_backup = self.subp.add_parser(
            'backup',
            aliases=['bu'],
            help='Backup specified files'
        )
        subp_build = parser_backup.add_subparsers(dest='subargs_backup')

        p_linstordb = subp_build.add_parser('linstordb',help='back linstordb')
        p_linstordb.set_defaults(func=self.backup_linstordb)


    def backup_linstordb(self, args):
        controller = control.LinstorConsole()
        print('*start*')
        if controller.backup_linstordb():
            print('Success')
        else:
            print('Fail，exit')
            sys.exit()
        print('*success*')
