import sys

import control



class DeleteCommands():
    def __init__(self,sub_parser):
        self.subp = sub_parser
        self.setup_parser()


    def setup_parser(self):
        parser_del = self.subp.add_parser(
            'delete',
            aliases=['d'],
            help='delete'
        )

        subp_del = parser_del.add_subparsers()
        p_linstordb = subp_del.add_parser('linstordb', aliases=['ldb'], help='delete linstordb')

        # Binding function
        p_linstordb.set_defaults(func=self.delete_linstordb)


    def backup_linstor(self, args):
        controller = control.LinstorConsole()
        print('*start*')
        if controller.backup_linstordb():
            print('Success')
        else:
            print('Fail，exit')
            sys.exit()
        print('*success*')


    def delete_linstordb(self,args):
        controller = control.LinstorConsole()
        controller.destroy_linstordb()

