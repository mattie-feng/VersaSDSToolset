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

    def main_usage(self,args):
        if args.version:
            print(f'Version: ？')
            sys.exit()
        else:
            main()

    def parser_init(self):
        args = self.parser.parse_args()
        args.func(args)


def main():
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


if __name__ == "__main__":
    cmd = argparse_operator()
    cmd.parser_init()
