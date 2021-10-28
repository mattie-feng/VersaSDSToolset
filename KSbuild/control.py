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

    def install_haproxy(self):
        lst = []
        for ssh in self.conn.list_master_ssh:
            handler = action.HAproxy(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)

    def install_keepalived(self):
        lst = []
        for ssh in self.conn.list_master_ssh:
            handler = action.Keepalived(ssh)
            lst.append(gevent.spawn(handler.install))
        gevent.joinall(lst)

    def install_docker(self):
        lst = []
        list_all_node  = []
        list_all_node.extend(self.conn.list_master_ssh)
        list_all_node.extend(self.conn.list_worker_ssh)

        for ssh in list_all_node:
            handler = action.KubeKey(ssh)
            lst.append(gevent.spawn(handler.install_docker))
        gevent.joinall(lst)

    def install_kk(self):
        handler = action.KubeKey()
        handler.install_kk()

    def modify_haproxy(self):
        lst = []
        if not os.path.exists("./sample-haproxy.cfg"):
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

    def modify_keepalived(self):
        lst = []
        if not os.path.exists("./sample-keepalived.conf"):
            print("keepalived.conf 文件不存在，退出")
            sys.exit()

        router_id = self.conn.data['Keepalived']['router_id']
        virtual_router_id = self.conn.data['Keepalived']['virtual_router_id']
        virtual_ipaddress = self.conn.data['Keepalived']['virtual_ipaddress']

        for ssh,master in zip(self.conn.list_master_ssh,self.conn.conf_file.master_list):
            unicast_peer_list = []
            interface = ""
            priority = ""
            unicast_src_ip = ""
            handler = action.Keepalived(ssh)
            for host in self.conn.data['Keepalived']['host']:
                if master == host['name']:
                    unicast_src_ip = self.conn.conf_file.get_ip(host['name'])
                    interface = host['interface']
                    priority = host['priority']
                else:
                    unicast_peer_list.append(self.conn.conf_file.get_ip(host['name']))

            if not all([interface,priority,unicast_src_ip]):
                print("配置文件master节点的数据不一致")
                sys.exit()

            lst.append(gevent.spawn(handler.modify_conf,
                                    "/etc/keepalived/keepalived.conf",
                                    router_id,
                                    interface,
                                    virtual_router_id,
                                    priority,
                                    unicast_src_ip,
                                    unicast_peer_list,
                                    virtual_ipaddress
                                    ))
        gevent.joinall(lst)


    def modify_kk(self):
        handler = action.KubeKey()
        confile = utils.ConfFile()
        hosts = confile.get_kk_hosts()
        etcd = confile.get_kk_etcd()
        master = confile.get_kk_masters()
        worker = confile.get_kk_worker()
        vip = confile.get_kk_vip()
        port = confile.get_kk_port()
        handler.modify_config(hosts,etcd,master,worker,vip,port)

    def buidl_ks(self):
        handler = action.KubeKey()
        handler.build()


    def restart_haproxy(self):
        lst = []
        for ssh in self.conn.list_master_ssh:
            handler = action.HAproxy(ssh)
            lst.append(gevent.spawn(handler.restart))
        gevent.joinall(lst)

    def restart_keepalived(self):
        lst = []
        for ssh in self.conn.list_master_ssh:
            handler = action.Keepalived(ssh)
            lst.append(gevent.spawn(handler.restart))
        gevent.joinall(lst)


KSConsole().modify_kk()