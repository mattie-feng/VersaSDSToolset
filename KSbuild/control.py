import gevent
from gevent import monkey
import os
import sys
import utils
import action


# 协程相关的补丁
monkey.patch_all()

timeout = gevent.Timeout(60)



class Connect():
    """
    通过ssh连接节点，生成连接对象的列表
    """
    list_master_ssh = []
    list_worker_ssh = []
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            Connect._instance = super().__new__(cls)
            Connect._instance.conf_file = utils.ConfFile()
            Connect._instance.data = Connect._instance.conf_file.data
            Connect.get_master_ssh(Connect._instance)
            Connect.get_worker_ssh(Connect._instance)

        return Connect._instance


    def get_master_ssh(self):
        local_ip = utils.get_host_ip()
        for node in self.conf_file.get_master_ssh_data():
            if local_ip == node[0]:
                self.list_master_ssh.append(None)
            else:
                ssh = utils.SSHConn(node[0],node[1],node[2],node[3])
                self.list_master_ssh.append(ssh)

    def get_worker_ssh(self):
        local_ip = utils.get_host_ip()
        for node in self.conf_file.get_worker_ssh_data():
            if local_ip == node[0]:
                self.list_worker_ssh.append(None)
            else:
                ssh = utils.SSHConn(node[0],node[1],node[2],node[3])
                self.list_worker_ssh.append(ssh)




class KSConsole():
    def __init__(self):
        self.conn = Connect()

    def install_HAproxy(self):
        lst = []
        for ssh in self.conn.list_master_ssh:
            handler = action.HAproxy(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)

    def install_Keeplived(self):
        lst = []
        for ssh in self.conn.list_master_ssh:
            handler = action.Keeplived(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)


    def modify_hx(self):
        lst = []
        if not os.path.exists("./haproxy.cfg"):
            print("haproxy.cfg 文件不存在，退出")
            sys.exit()
        data = ""
        haproxy = action.HAproxy()
        for server in self.conn.data['HAproxy']['server']:
            ip = self.conn.conf_file.get_ip(server['name'])
            data += haproxy.get_server(server['name'],ip,server['port'])

        for ssh in self.conn.list_master_ssh:
            handler = action.HAproxy(ssh)
            lst.append(gevent.spawn(handler.modify_cfg,"/etc/haproxy/haproxy.cfg",data))
        gevent.joinall(lst)

    def restart_hx(self):
        lst = []
        for ssh in self.conn.list_master_ssh:
            handler = action.HAproxy(ssh)
            lst.append(gevent.spawn(handler.restart))
        gevent.joinall(lst)
