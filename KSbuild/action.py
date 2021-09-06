import utils

class Keeplived():
    def __init__(self, conn=None):
        self.conn = conn

    def install(self):
        cmd = "apt install -y keepalived"
        utils.exec_cmd(cmd)


    def modify_conf(self,filepath,router_id, interface, virtual_router_id, priority,unicast_src_ip, unicast_peer_list, virtual_ipaddress):
        editor = utils.FileEdit("./keeplived.conf")
        editor.replace_data("router_id LVS_DEVEL",f"router_id {router_id}")
        editor.replace_data("priority 100",f"priority {priority}")
        editor.replace_data("interface eno1", f"interface {interface}")
        editor.replace_data("virtual_router_id 60",f"virtual_router_id {virtual_router_id}")
        editor.replace_data("unicast_src_ip 127.0.0.1", f"unicast_src_ip {unicast_src_ip}")
        unicast_peer_data = ""
        for unicast_peer in unicast_peer_list:
            unicast_peer_data += f"    {unicast_peer}\n"
        editor.insert_data(unicast_peer_data,anchor="  unicast_peer {",type='under')
        editor.insert_data(f"    {virtual_ipaddress}",anchor="  virtual_ipaddress {",type='under')

        utils.exec_cmd(f'echo "{editor.data}" > {filepath}', self.conn)


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









