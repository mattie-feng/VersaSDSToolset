import os
import subprocess
import utils
from utils import SSHConn
import time
import json
import sys


class SSHAuthorize:
    remove_flag = '# Domain name resolution processing of ssh connection\n'

    def __init__(self):
        self.connect_via_user = []
        self.cluster_info = self.read_config()
        self.keys_to_add = {}
        self.hosts_to_add = []

    def read_config(self):
        try:
            # cluster_info = open(sys.path[0] + "/config.json", encoding='utf-8')
            cluster_info = open("./config.json", encoding='utf-8')
            json_dict = json.load(cluster_info)
            cluster_info.close()
            return json_dict

        except FileNotFoundError:
            # with open(sys.path[0] + "/config.json", "w") as fw:
            with open("./config.json", "w") as fw:
                json_dict = {
                    "Cluster": {}}
                json.dump(json_dict, fw, indent=4, separators=(',', ': '))
                return json_dict
        except json.decoder.JSONDecodeError:
            print('Failed to read configuration file.')
            sys.exit()

    def commit_data(self):
        # with open(sys.path[0] + "/config.json", "w") as fw:
        with open("./config.json", "w") as fw:
            json.dump(self.cluster_info, fw, indent=4, separators=(',', ': '))
        return self.cluster_info

    # 更新配置文件"public_key"全部
    def update_public_key(self, first_key, cluster_name, kind, data_value):
        self.cluster_info[first_key].update({cluster_name: {kind: data_value}})
        return self.cluster_info[first_key]

    def update_public_key_member(self, first_key, cluster_name, kind, data_value):
        self.cluster_info[first_key][cluster_name][kind].update(data_value)
        return self.cluster_info[first_key]

    # data_value 是列表[[]]
    def updata_hosts(self, first_key, cluster_name, kind, data_value):
        self.cluster_info[first_key][cluster_name].update({kind: data_value})
        return self.cluster_info[first_key]

    # data_value 是列表[[]]
    def updata_hosts_member(self, first_key, cluster_name, kind, data_value):
        for value in data_value:
            self.cluster_info[first_key][cluster_name][kind].append(value)
        return self.cluster_info[first_key]

    # 移除整个集群
    # def delete_data(self, first_key, cluster_name):
    #     self.cluster_info[first_key].pop(cluster_name)
    #     return self.cluster_info[first_key]

    def delete_public_key_member(self, first_key, cluster_name, kind, member_key):
        self.cluster_info[first_key][cluster_name][kind].pop(member_key)
        return self.cluster_info[first_key]

    def delete_hosts_member(self, first_key, cluster_name, kind, member):
        hosts_info_list = self.cluster_info[first_key][cluster_name][kind]
        # host-[ip,hostname]
        new_hosts_info_list = [host for host in hosts_info_list if host[1] != member]
        self.cluster_info[first_key][cluster_name][kind] = new_hosts_info_list
        return self.cluster_info[first_key]

    def cluster_is_exist(self, key, target):
        if target in self.cluster_info[key]:
            return True
        else:
            return False

    def node_is_exist(self, key, member):
        # 循环的字典为空则不会开始循环
        for data in self.cluster_info[key].values():
            if member in data['public_key'].keys():
                return True
        return False

    def make_connect(self, ip, port, user, password):
        # update change self.connect_via_user or self.connect_via_key
        ssh = SSHConn(ip, port, user, password, timeout=100)
        # ssh.ssh_connect()
        self.connect_via_user.append(ssh)
        return ssh

    @staticmethod
    def get_public_key(ssh):
        # 已存在会提示是否覆盖，需要提前判断文件是否存在
        # 初始化节点ssh服务的（输入参数SSHClient连接对象，输出参数SSHClient连接对象）
        rsa_is_exist = bool(ssh.exec_cmd('[ -f /root/.ssh/id_rsa.pub ] && echo True'))
        # 执行生成密钥操作
        if not rsa_is_exist:
            ssh.exec_cmd('ssh-keygen -f /root/.ssh/id_rsa -N ""')
        # 要有停顿时间，不然public_key还未写入
        time.sleep(2)
        # 注意 /.ssh/config 文件
        config_is_exist = bool(ssh.exec_cmd('[ -f /root/.ssh/config ] && echo True'))
        if not config_is_exist:
            ssh.exec_cmd("echo -e 'StrictHostKeyChecking no\\nUserKnownHostsFile /dev/null' >> ~/.ssh/config ")
        public_key = ssh.exec_cmd('cat /root/.ssh/id_rsa.pub')
        return public_key

    @staticmethod
    def get_hostname(ssh):
        hostname = ssh.exec_cmd('hostname').strip()
        return hostname

    @staticmethod
    def init_manager_node():
        rsa_is_exist = bool(os.popen('[ -f /root/.ssh/id_rsa.pub ] && echo True').read())
        print('rsa_is_exist:', rsa_is_exist)
        if not rsa_is_exist:
            os.system('ssh-keygen -f /root/.ssh/id_rsa -N ""')
        time.sleep(2)
        config_is_exist = bool(os.popen('[ -f /root/.ssh/config ] && echo True').read())
        print('config_is_exist:', config_is_exist)
        # 这里不要输入 -e 参数,转不转义都可以
        if not config_is_exist:
            os.system("echo 'StrictHostKeyChecking no\nUserKnownHostsFile /dev/null' >> ~/.ssh/config ")
        public_key = os.popen('cat /root/.ssh/id_rsa.pub').read()
        return public_key

    def get_map_key_by_host(self, cluster_name, ip):
        if cluster_name not in self.cluster_info['Cluster'].keys():
            return
        if ip not in self.cluster_info['Cluster'][cluster_name].keys():
            return
        return self.cluster_info['Cluster'][cluster_name][ip]

    # @staticmethod
    # def get_host_ip():
    #     """
    #     查询本机ip地址
    #     :return: ip
    #     """
    #     try:
    #         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #         s.connect(('8.8.8.8', 80))
    #         ip = s.getsockname()[0]
    #     finally:
    #         s.close()
    #
    #     return ip
    #
    # def get_local_node_hosts_info(self):
    #     local_ipaddr = self.get_host_ip()
    #     local_hostname = os.popen('hostname').read()
    #     return f'{local_ipaddr} {local_hostname}'

    def set_all_public_keys_by_cluster(self, cluster_name, all_public_key):
        if not all_public_key:
            return
        self.update_public_key('Cluster', cluster_name, 'public_key', all_public_key)
        self.commit_data()

    def insert_new_public_keys_by_cluster(self, cluster_name):
        if not self.keys_to_add:
            return
        self.update_public_key_member('Cluster', cluster_name, 'public_key', self.keys_to_add)
        self.commit_data()

    def set_all_hosts_by_cluster(self, cluster_name, hosts_info):
        if not hosts_info:
            return
        self.updata_hosts('Cluster', cluster_name, 'hosts', hosts_info)
        self.commit_data()

    def insert_new_hosts_by_cluster(self, cluster_name):
        if not self.hosts_to_add:
            return
        self.updata_hosts_member('Cluster', cluster_name, 'hosts', self.hosts_to_add)
        self.commit_data()

    def get_list_key_node_for_cluster(self, cluster_name):
        if cluster_name not in self.cluster_info['Cluster'].keys():
            return
        return list(self.cluster_info['Cluster'][cluster_name]['public_key'].values())

    def get_list_hosts_for_cluster(self, cluster_name):
        if cluster_name not in self.cluster_info['Cluster'].keys():
            return
        return self.cluster_info['Cluster'][cluster_name]['hosts']

    def convert_all_keys_by_cluster_to_string(self, cluster_name):
        str = ""
        # 空不会进入循环，考虑 if 是否必要
        if self.get_list_key_node_for_cluster(cluster_name):
            for pb_key in self.get_list_key_node_for_cluster(cluster_name):
                str = str + pb_key
        return str

    def convert_all_hosts_by_cluster_to_string(self, cluster_name):
        str = self.remove_flag
        if self.get_list_hosts_for_cluster(cluster_name):
            for value in self.get_list_hosts_for_cluster(cluster_name):
                ip, hostname = value
                str += f'{ip} {hostname}\n'
            # 去掉最后一个\n可以使用 str = str[:-1]
        return str[:-1]

    def convert_new_keys_by_cluster_to_string(self):
        str = ""
        for pb_key in self.keys_to_add.values():
            str = str + pb_key
        return str

    def convert_new_hosts_by_cluster_to_string(self):
        str = ""
        for value in self.hosts_to_add:
            ip, hostname = value
            str = str + f'{ip} {hostname}\n'
        return str[:-1]

    # 管理节点 公钥 处理？！
    def distribute_all_keys_by_connect_via_user(self, cluster_name):
        all_public_keys = self.convert_all_keys_by_cluster_to_string(cluster_name)
        manager_node_pbk = self.init_manager_node()
        all_public_keys = all_public_keys + manager_node_pbk
        if not all_public_keys:
            return
        for obj_connection in self.connect_via_user:
            obj_connection.exec_cmd(f"echo -e \'{all_public_keys}\' >> /root/.ssh/authorized_keys")

    def distribute_new_keys_to_old_node_by_add(self, cluster_name):
        old_node = [node for node in self.cluster_info['Cluster'][cluster_name]['public_key'].keys() if
                    node not in self.keys_to_add.keys()]
        new_public_keys = self.convert_new_keys_by_cluster_to_string()
        # new_public_keys 初始值 "",当它是 "" 会 return
        if not new_public_keys:
            return
        # >> 表示不覆盖　继续在下一行编辑
        # &>> 表示为追加
        for node in old_node:
            subprocess.run(f'ssh root@{node} "echo -e \'{new_public_keys}\' &>> /root/.ssh/authorized_keys"',
                           shell=True)

    def distribute_new_hosts_to_old_node_by_add(self, cluster_name):
        old_node = [node for node in self.cluster_info['Cluster'][cluster_name]['public_key'].keys() if
                    node not in self.keys_to_add.keys()]
        new_hosts_info = self.convert_new_hosts_by_cluster_to_string()
        for node in old_node:
            subprocess.run(f'ssh root@{node} "echo -e \'{new_hosts_info}\' &>> /etc/hosts"',
                           shell=True)

    def distribute_new_hosts_to_local_node_by_add(self):
        new_hosts_info = self.convert_new_hosts_by_cluster_to_string()
        os.system(f"echo \'{new_hosts_info}\' >> /etc/hosts")

    # 读取旧的文件然后移除删除节点的公钥然后再次写入
    def distribute_new_keys_to_old_node_by_remove(self, cluster_name):
        old_node = [node for node in self.cluster_info['Cluster'][cluster_name]['public_key'].keys()]
        new_public_keys = self.convert_all_keys_by_cluster_to_string(cluster_name)
        manager_node_pbk = self.init_manager_node()
        new_public_keys = new_public_keys + manager_node_pbk
        if not new_public_keys:
            return
        # > 表示覆盖以前内容
        for node in old_node:
            subprocess.run(f'ssh root@{node} "echo -e \'{new_public_keys}\' > /root/.ssh/authorized_keys"',
                           shell=True)

    def distribute_all_hosts_by_connect_via_user(self, cluster_name):
        all_hosts_info = self.convert_all_hosts_by_cluster_to_string(cluster_name)
        # local_ipaddr = self.get_host_ip()
        # local_hostname = os.popen('hostname').read()
        # all_hosts_info = all_hosts_info + f'{local_ipaddr} {local_hostname}'
        for obj_connection in self.connect_via_user:
            obj_connection.exec_cmd(f"echo -e \'{all_hosts_info}\' >> /etc/hosts")

    def distribute_all_hosts_in_local(self, cluster_name):
        all_hosts_info = self.convert_all_hosts_by_cluster_to_string(cluster_name)
        os.system(f"echo \'{all_hosts_info}\' >> /etc/hosts")

    def distribute_new_hosts_to_old_node_by_remove(self, cluster_name):
        # 获取该集群现有节点列表 for 循环
        # 1.重新获取本地 hosts 信息
        # 2.获取该节点 hosts 文件的内容
        # 3.删除标识符以下行
        # 4.将新内容覆盖重新写入（针对每一个节点的 hosts 文件）
        old_node = [node for node in self.cluster_info['Cluster'][cluster_name]['public_key'].keys()]
        # 移除后的重新写入的 hosts 内容
        new_hosts_info = self.convert_all_hosts_by_cluster_to_string(cluster_name)
        # 先移除标识之后的的所有列，然后再写入
        for node in old_node:
            self.handle_hosts_file_by_remove_flag(node)
            # 等待文件写完再进行下一步
            time.sleep(2)
            subprocess.run(f'ssh root@{node} "echo -e \'{new_hosts_info}\' >> /etc/hosts"',
                           shell=True)

    def handle_hosts_file_by_remove_flag(self, hostname):
        # 以行读取，返回列表
        hosts_info = os.popen(f'ssh root@{hostname} "cat /etc/hosts"').readlines()
        before_remove_flag_str = ""
        for i in range(len(hosts_info)):
            if hosts_info[i] == SSHAuthorize.remove_flag:
                before_remove_flag_str = hosts_info[0:i]
        if before_remove_flag_str:
            write_string = "".join(before_remove_flag_str)
            # 等待文件读完再进行下一步
            time.sleep(2)
            os.popen(f'ssh root@{hostname} "echo \'{write_string}\' > /etc/hosts"')
            # print('/etc/hosts:\n', os.popen(f'ssh root@{hostname} "cat /etc/hosts"').read())
        else:
            print('something wrong happened')
            sys.exit()

    def handle_host_file_remove_by_hostname_in_local(self, hostname):
        hosts_info = os.popen(f'cat /etc/hosts').readlines()
        # 以空格开始，以换行符结束
        find_str = f' {hostname}\n'
        # 该行不包括该主机名
        lines = [line for line in hosts_info if find_str not in line]
        # 列表转字符串
        write_string = "".join(lines)
        os.system(f'echo \'{write_string}\' > /etc/hosts')

    def init_cluster(self, cluster_name, list_of_nodes):
        if self.cluster_is_exist('Cluster', cluster_name):
            print('this cluster name is exist')
            sys.exit()
        for node in list_of_nodes:
            # make connection 的时候存放 ssh 对象
            ssh = self.make_connect(node[0], node[1], node[2], node[3])
            public_key = self.get_public_key(ssh)
            hostname = self.get_hostname(ssh)
            # 逐个节点存放 ip-主机名 列表
            self.hosts_to_add.append([node[0], hostname])
            # 逐个节点存放 主机名-公钥 字典
            self.keys_to_add.update({hostname: public_key})

        # 公钥信息放进本地配置文件
        self.set_all_public_keys_by_cluster(cluster_name, self.keys_to_add)
        # hosts 信息放进本地配置文件
        self.set_all_hosts_by_cluster(cluster_name, self.hosts_to_add)
        # 分发该集群公钥信息通过 ssh 连接对象
        self.distribute_all_keys_by_connect_via_user(cluster_name)
        # 分发集群 hosts 信息到集群节点通过 ssh 连接对象
        self.distribute_all_hosts_by_connect_via_user(cluster_name)
        # 将集群 hosts 信息写入管理节点本地 hosts 文件
        self.distribute_all_hosts_in_local(cluster_name)

    def cluster_add(self, cluster_name, list_of_nodes):
        if not self.cluster_is_exist('Cluster', cluster_name):
            print('this cluster name is not exist')
            sys.exit()
        for node in list_of_nodes:
            ssh = self.make_connect(node[0], node[1], node[2], node[3])
            key = self.get_public_key(ssh)
            hostname = self.get_hostname(ssh)
            if self.node_is_exist('Cluster', hostname):
                print(f'this {hostname} is exist')
                continue
            # 逐个节点存放 ip-主机名 列表
            self.hosts_to_add.append([node[0], hostname])
            # 逐个节点存放 主机名-公钥 字典
            self.keys_to_add.update({hostname: key})
        # 新公钥信息插入本地配置文件
        self.insert_new_public_keys_by_cluster(cluster_name)
        # 新 hosts 信息插入本地配置文件
        self.insert_new_hosts_by_cluster(cluster_name)
        # 新增节点下发公钥
        self.distribute_all_keys_by_connect_via_user(cluster_name)
        # 新增节点下发 hosts
        self.distribute_all_hosts_by_connect_via_user(cluster_name)
        # 原有节点下发公钥
        self.distribute_new_keys_to_old_node_by_add(cluster_name)
        # 原有节点下发 hosts
        self.distribute_new_hosts_to_old_node_by_add(cluster_name)
        # 本地管理节点下发 hosts
        self.distribute_new_hosts_to_local_node_by_add()

    def remove_from_cluster(self, cluster_name, list_of_nodes_ip):
        if not self.cluster_is_exist('Cluster', cluster_name):
            print('this cluster name is not exist')
            sys.exit()
        for node in list_of_nodes_ip:
            if not self.node_is_exist('Cluster', node):
                print(f'this {node} is not exist')
                continue
            # 处理 hosts 文件
            self.handle_hosts_file_by_remove_flag(node)
            # rm authorized_keys file
            subprocess.run(f'ssh "root@{node}" "rm /root/.ssh/authorized_keys"', shell=True)
            # 处理本地 public_key 记录
            self.delete_public_key_member('Cluster', cluster_name, 'public_key', node)
            # 处理本地 hosts 记录
            self.delete_hosts_member('Cluster', cluster_name, 'hosts', node)
            # 处理管理节点 hosts 文件 （使用 os 模块本地执行)
            self.handle_host_file_remove_by_hostname_in_local(node)
        # 更新本地 json 配置文件
        self.commit_data()
        # 从本地获取新的总公钥信息+管理节点公钥下发到旧节点
        self.distribute_new_keys_to_old_node_by_remove(cluster_name)
        # 从本地获取新的 hosts 信息下发到旧节点
        self.distribute_new_hosts_to_old_node_by_remove(cluster_name)


class SSHAuthorizeNoMGN(SSHAuthorize):
    def __init__(self):
        super().__init__()

    def get_hostname(self, conn):
        # 这个可以直接使用util.exec_cmd来替换了
        hostname = utils.exec_cmd('hostname', conn).strip()
        return hostname

    @staticmethod
    def get_public_key(conn):
        # 已存在会提示是否覆盖，需要提前判断文件是否存在
        # 初始化节点ssh服务的（输入参数SSHClient连接对象，输出参数SSHClient连接对象）
        rsa_pub_is_exist = bool(utils.exec_cmd('[ -f /root/.ssh/id_rsa.pub ] && echo True', conn))
        rsa_is_exist = bool(utils.exec_cmd('[ -f /root/.ssh/id_rsa ] && echo True', conn))
        # 执行生成密钥操作
        if not rsa_pub_is_exist:
            if rsa_is_exist:
                print('id_rsa 存在, 请先进行处理')
                sys.exit()
            utils.exec_cmd('ssh-keygen -f /root/.ssh/id_rsa -N ""', conn)
        # 要有停顿时间，不然public_key还未写入
        time.sleep(2)
        # 注意 /.ssh/config 文件
        config_is_exist = bool(utils.exec_cmd('[ -f /root/.ssh/config ] && echo True', conn))
        if not config_is_exist:
            utils.exec_cmd("echo 'StrictHostKeyChecking no\nUserKnownHostsFile /dev/null' >> ~/.ssh/config ", conn)
        public_key = utils.exec_cmd('cat /root/.ssh/id_rsa.pub', conn)
        public_key = public_key if isinstance(public_key, bytes) else public_key
        return public_key.strip()

    def convert_all_keys_by_cluster_to_string(self, cluster_name):
        str = ""
        if self.get_list_key_node_for_cluster(cluster_name):
            for pb_key in self.get_list_key_node_for_cluster(cluster_name):
                str = str + pb_key + '\n'
        return str

    def distribute_all_keys_by_connect_via_user(self, cluster_name, list_ssh):
        all_public_keys = self.convert_all_keys_by_cluster_to_string(cluster_name)
        all_public_keys = all_public_keys
        if not all_public_keys:
            return
        for ssh in list_ssh:
            utils.exec_cmd(f"echo \'{all_public_keys}\' >> /root/.ssh/authorized_keys", ssh)  # -e

    def distribute_all_hosts_by_connect_via_user(self, cluster_name, list_ssh):
        all_hosts_info = self.convert_all_hosts_by_cluster_to_string(cluster_name)
        for ssh in list_ssh:
            utils.exec_cmd(f"echo \'{all_hosts_info}\' >> /etc/hosts", ssh)  # -e

    def init_cluster_no_mgn(self, cluster_name, cluster_data, list_ssh):
        """
        需要做的修改：
        1.没有管理节点的概念，集群所有节点都进行免密注册
        2.执行程序的这一节点不需要通过ssh去获取数据和执行命令，本地执行
        :param cluster_name:
        :param list_of_nodes:
        :return:
        """
        for node, ssh in zip(cluster_data, list_ssh):
            public_key = self.get_public_key(ssh)
            hostname = self.get_hostname(ssh)
            # 逐个节点存放 ip-主机名 列表
            self.hosts_to_add.append([node['public_ip'], hostname])
            # 逐个节点存放 主机名-公钥 字典
            self.keys_to_add.update({hostname: f'{public_key}'})

        # 公钥信息放进本地配置文件
        self.set_all_public_keys_by_cluster(cluster_name, self.keys_to_add)
        # hosts 信息放进本地配置文
        self.set_all_hosts_by_cluster(cluster_name, self.hosts_to_add)
        # 分发该集群公钥信息通过 ssh 连接对象
        self.distribute_all_keys_by_connect_via_user(cluster_name, list_ssh)
        # 分发集群 hosts 信息到集群节点通过 ssh 连接对象
        self.distribute_all_hosts_by_connect_via_user(cluster_name, list_ssh)

    def get_ssh(self, hostname):
        pass


if __name__ == '__main__':
    node_infos = [['47.99.219.219', 22, 'root', 'guitqil123A']]
    # ssh = paramiko.SSHClient()
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect('10.203.1.86',22)
    # print(ssh.exec_command('pwd')[1].read().decode())
    # # 初始化集群节点
    ssh1 = SSHAuthorize()
    ssh1.init_cluster('cluster1', node_infos)
    # # 移除节点
    # ssh3 = SSHAuthorize()
    # remove_list_node = ['ubuntu','vince2']
    # ssh1.remove_from_cluster('cluster1', remove_list_node)
    # 新增节点
    # ssh2 = SSHAuthorize()
    # new_node_list = [['10.203.1.155', 22, 'root', 'password'],['10.203.1.157', 22, 'root', 'password']]
    # ssh1.cluster_add('cluster1', new_node_list)
