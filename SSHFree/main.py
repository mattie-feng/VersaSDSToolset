import sys
import time
import operation
import utils
import argparse

class argparse_operator:
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='argparse')
        self.setup_parse()

    def setup_parse(self):
        sub_parser = self.parser.add_subparsers()

        self.parser.add_argument('-v',
                                 '--version',
                                 dest='version',
                                 help='Show current version',
                                 action='store_true')

        self.parser.set_defaults(func=self.main_usage)

        parser_free = sub_parser.add_parser("free",aliases=['fe'],help='free_login')

        parser_re_free = sub_parser.add_parser("re",aliases=['re'],help='re_free_login')

        parser_free.set_defaults(func=self.func_free_login)
        parser_re_free.set_defaults(func=self.func_re_free_login)

    def main_usage(self,args):
        if args.version:
            print(f'Version: ？')
            sys.exit()
        else:
            self.parser.print_help()

    def parser_init(self):
        args = self.parser.parse_args()
        args.func(args)

    def func_free_login(self,args):
        free_login()

    def func_re_free_login(self,args):
        re_free_login()


def free_login():
    config_info = operation.read_config('config.yaml')
    node_list = config_info['node']
    for z in node_list:
        name = z['name']
        ipaddr = z['ip']
        usname = z['username']
        passwd = z['password']
        ssh_obj = utils.SSHConn(host=ipaddr,username=usname,password=passwd)
        status0 = operation.revise_sshd_config(ssh_obj)
        status1 = operation.check_id_rsa_pub(ssh_obj)
        if status1 is False:
            print(f'{ipaddr}不存在公钥，开始创建公钥')
            status2 = operation.create_id_rsa_pub(ssh_obj)
            time.sleep(2)
            if status2 is False:
                print('公钥创建失败')
                sys.exit()
            else:
                print('公钥创建成功')
        else:
            print(f'{ipaddr}存在公钥')


    for i, z in enumerate(node_list):
        name = z['name']
        ipaddr = z['ip']
        usname = z['username']
        passwd = z['password']
        ssh_obj = utils.SSHConn(host=ipaddr,username=usname,password=passwd)
        exec(f'list{i} = {node_list}')
        exec(f'list{i}.remove({z})')
        print(f'现在开始进行{ipaddr}的公钥散发')
        try:
            exec(f'for y in list{i}:'
                 f'    ssh_obj.exec_copy_id_rsa_pub(y["ip"],y["password"])')
            print(f'{ipaddr}的公钥散发完成')
        except:
            print('公钥散发失败，程序自动退出')
            sys.exit()

def re_free_login():
    config_info = operation.read_config('config.yaml')
    node_list = config_info['node']
    for z in node_list:
        name = z['name']
        ipaddr = z['ip']
        usname = z['username']
        passwd = z['password']
        print(f'现在开始进行{ipaddr}的去免密操作')
        ssh_obj = utils.SSHConn(host=ipaddr,username=usname,password=passwd)
        status0 = operation.check_authorized_keys(ssh_obj)
        try:
            delete_cmd = "rm /root/.ssh/authorized_keys"
            utils.exec_cmd(delete_cmd, ssh_obj)
            print("去免密成功")
        except:
            print("去免密失败")


if __name__ == "__main__":
    cmd = argparse_operator()
    cmd.parser_init()
