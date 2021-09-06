import utils

class Keeplived():
    def __init__(self, conn=None):
        self.conn = conn

    def install(self):
        cmd = "apt install -y keepalived"
        utils.exec_cmd(cmd)


    def modify_conf(self,interface,IP_list,):
        pass


class HAproxy():
    def __init__(self,conn=None):
        self.conn = conn


    def install(self):
        cmd = "apt install -y haproxy"
        utils.exec_cmd(cmd,self.conn)


    def get_server(self, hostname, ip, port):
        return f"    server {hostname} {ip}:{port} check\n"


    def modify_cfg(self,file_path,data):
        editor = utils.FileEdit("./haproxy.cfg")
        editor.insert_data(f"{data}",f'    default-server inter 10s downinter 5s rise 2 fall 2 slowstart 60s maxconn 250 maxqueue 256 weight 100', type='under')
        utils.exec_cmd(f'echo "{editor.data}" > {file_path}', self.conn)


    def restart(self):
        utils.exec_cmd("systemctl restart haproxy",self.conn)
        utils.exec_cmd("systemctl enable haproxy",self.conn)



class KubeKey():
    def __init__(self,conn=None):
        self.conn = conn

    def install(self):
        utils.exec_cmd("export KKZONE=cn && curl -sfL https://get-kk.kubesphere.io | VERSION=v1.1.0 sh -")
        utils.exec_cmd("chmod +x kk")

    def create_config(self):
        cmd = "./kk create config --with-kubesphere v3.1.0 --with-kubernetes v1.20.4"
        utils.exec_cmd(cmd)


    def modify_config(self):
        pass









# def modify_hx():
#     lst = []
#     if not os.path.exists("./haproxy.cfg"):
#         print("haproxy.cfg 文件不存在，退出")
#         sys.exit()
#     with open("./haproxy.cfg") as f:
#         data = f.read()
#
#     for ssh in self.conn.list_ssh:
#         handler = action.HAproxy(ssh)
#         lst.append(gevent.spawn(handler.modify_cfg,data))
#     gevent.joinall(lst)






