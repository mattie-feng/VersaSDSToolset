import time
import utils
import re

corosync_conf_path = '/etc/corosync/corosync.conf'
read_data = './corosync.conf'
crm_lincontrl_config = './crm_lincontrl_config'


class IpService(object):
    def __init__(self, conn=None):
        self.conn = conn

    def set_ip(self, device, ip, gateway, netmask=24):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection add con-name {connection_name} type ethernet ifname {device} ipv4.addresses {ip}/{netmask} ipv4.gateway {gateway} ipv4.method manual"
        utils.exec_cmd(cmd, self.conn)

    def up_ip_service(self, device):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection up id {connection_name}"
        utils.exec_cmd(cmd, self.conn)

    def modify_ip(self, device, new_ip, gateway, netmask=24):
        connection_name = 'vtel_' + device
        cmd = f"nmcli connection modify {connection_name} ipv4.address {new_ip}/{netmask} ipv4.gateway {gateway}"
        utils.exec_cmd(cmd, self.conn)


class Host():
    def __init__(self,conn=None):
        self.conn = conn


    def modify_hostname(self,hostname):
        cmd = f'hostnamectl set-hostname {hostname}'
        utils.exec_cmd(cmd,self.conn)


    def modify_hostsfile(self,ip,hostname):
        cmd = f"sed -i 's/{ip}.*/{ip}\t{hostname}/g' /etc/hosts"
        utils.exec_cmd(cmd,self.conn)


    def check_hostname(self,hostname):
        lc_hostname = utils.exec_cmd('hostname',self.conn)
        if lc_hostname == hostname:
            return True


    def check_ssh(self,cluster_hosts):
        # 1. 验证是否输入的host是否存在~/.ssh/authorized_keys这个文件
        # 2. 验证输入的hosts每个公钥最后的root@hostname, 是不是配置文件中都有记录
        ak_is_exist = bool(utils.exec_cmd('[ -f /root/.ssh/authorized_keys ] && echo True'))
        time.sleep(0)
        if not ak_is_exist:
            return
        if not self._check_authorized_keys(cluster_hosts):
            return
        return True


    def _check_authorized_keys(self,cluster_hosts):
        authorized_keys = utils.exec_cmd('cat /root/.ssh/authorized_keys')
        time.sleep(0)
        hosts = re.findall('ssh-rsa\s[\s\S]*?\sroot@(.*)', authorized_keys)
        if set(cluster_hosts) <= set(hosts):
            return True



class Corosync():
    original_attr = {'cluster_name': 'debian',
                     'bindnetaddr': '127.0.0.1'}

    interface_pos = '''                ttl: 1
        }'''

    nodelist_pos = "logging {"

    def __init__(self,conn=None):
        self.conn = conn


    def sync_time(self):
        cmd = 'ntpdate -u ntp.api.bz'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)



    def change_corosync_conf(self,cluster_name,bindnetaddr,interface,nodelist):
        # editor = utils.FileEdit(corosync_conf_path) # 读取原配置文件数据
        editor = utils.FileEdit(read_data)

        editor.replace_data(f"cluster_name: {self.original_attr['cluster_name']}",
                            f"cluster_name: {cluster_name}")
        editor.insert_data(f'\trrp_mode: passive', anchor='        # also set rrp_mode.', type='under')
        editor.replace_data(f"bindnetaddr: {self.original_attr['bindnetaddr']}",
                            f"bindnetaddr: {bindnetaddr}")

        interface = utils.FileEdit.add_data_to_head(interface, '\t') # 缩进处理
        editor.insert_data(interface,anchor=self.interface_pos,type='under')
        editor.insert_data(nodelist, anchor=self.nodelist_pos,type='above')

        # editor = utils.FileEdit(read_data) # 恢复原始配置文件，需要read_data存在
        utils.exec_cmd(f'echo "{editor.data}" > {corosync_conf_path}',self.conn)



    def restart_corosync(self):
        cmd = 'systemctl restart corosync'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)



    def check_ring_status(self,node):
        cmd = 'corosync-cfgtool -s'
        data = utils.exec_cmd(cmd,self.conn)
        ring_data = re.findall('RING ID\s\d*[\s\S]*?id\s*=\s*(.*)',data)
        if len(ring_data) == 2:
            if node['public_ip'] in ring_data and node['private_ip']['ip'] in ring_data:
                return True



    def check_corosync_status(self,nodes,timeout=30):
        cmd = 'crm st'
        t_beginning = time.time()
        node_online = []
        while not node_online:
            data = utils.exec_cmd(cmd, self.conn)
            node_online = re.findall('Online:\s\[(.*?)\]', data)
            if node_online:
                node_online = node_online[0].strip().split(' ')
                if set(node_online) == set(nodes):
                    return True
                else:
                    time.sleep(1)
            seconds_passed = time.time() - t_beginning
            if timeout and seconds_passed > timeout:
                return



class Pacemaker():
    def __init__(self,conn=None):
        self.conn = conn

    def modify_cluster_name(self,cluster_name):
        cmd = f"crm config property cluster-name={cluster_name}"
        utils.exec_cmd(cmd, self.conn)
        time.sleep(0)

    def modify_policy(self):
        cmd = "crm config property no-quorum-policy=ignore"
        utils.exec_cmd(cmd, self.conn)
        time.sleep(0)

    def modify_stonith_enabled(self):
        cmd = "crm config property stonith-enabled=false"
        utils.exec_cmd(cmd, self.conn)
        time.sleep(0)

    def modify_stickiness(self):
        cmd = "crm config rsc_defaults resource-stickiness=1000"
        utils.exec_cmd(cmd, self.conn)
        time.sleep(0)


    def check_crm_conf(self,cluster_name):
        cmd = 'crm config show | cat'
        data = utils.exec_cmd(cmd,self.conn)
        data_property = re.search('property cib-bootstrap-options:\s([\s\S]*)',data).group(1)
        re_cluster_name = re.findall('cluster-name=(\S*)', data_property)
        re_stonith_enabled = re.findall('stonith-enabled=(\S*)', data_property)
        re_policy = re.findall('no-quorum-policy=(\S*)', data_property)
        re_resource_stickiness = re.findall('resource-stickiness=(\d*)', data)

        if not re_cluster_name or re_cluster_name[0] != cluster_name:
            return

        if not re_stonith_enabled or re_stonith_enabled[0] != 'false':
            return

        if not re_policy or re_policy[0] != 'ignore':
            return

        if not re_resource_stickiness or re_resource_stickiness[0] != '1000':
            return

        return True



class TargetCLI():
    def __init__(self,conn=None):
        self.conn = conn



    def set_auto_add_default_portal(self):
        cmd = "targetcli set global auto_add_default_portal=false"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def set_auto_add_mapped_luns(self):
        cmd = "targetcli set global auto_add_mapped_luns=false"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)

    def set_auto_enable_tpgt(self):
        cmd = "targetcli set global auto_enable_tpgt=true"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def check_targetcli_conf(self):
        cmd = "targetcli get global"
        data = utils.exec_cmd(cmd,self.conn)
        auto_add_default_portal = re.findall('auto_add_default_portal=(\w*)',data)
        auto_add_mapped_luns = re.findall('auto_add_mapped_luns=(\w*)',data)
        auto_enable_tpgt = re.findall('auto_enable_tpgt=(\w*)',data)


        if not auto_add_default_portal or auto_add_default_portal[0] != 'false':
            return False

        if not auto_add_mapped_luns or auto_add_mapped_luns[0] != 'false':
            return False

        if not auto_enable_tpgt or auto_enable_tpgt[0] != 'true':
            return False

        return True



class ServiceSet():
    def __init__(self,conn=None):
        self.conn = conn


    def set_disable_drbd(self):
        cmd = 'systemctl disable drbd'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def set_disable_linstor_controller(self):
        cmd = 'systemctl disable linstor-controller'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)

    def set_disable_targetctl(self):
        cmd = 'systemctl disable rtslib-fb-targetctl'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def set_enable_linstor_satellite(self):
        cmd = 'systemctl enable linstor-satellite'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def set_enable_pacemaker(self):
        cmd = 'systemctl enable pacemaker'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def set_enable_corosync(self):
        cmd = 'systemctl enable corosync'
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def check_drbd(self):
        cmd = 'systemctl status drbd'
        data = utils.exec_cmd(cmd,self.conn)
        time.sleep(0)
        result = re.findall('/lib/systemd/system/drbd.service; disabled; vendor preset: enabled',data)
        if result:
            return True


    def check_linstor_controller(self):
        cmd = 'systemctl status linstor-controller'
        data = utils.exec_cmd(cmd,self.conn)
        time.sleep(0)
        result = re.findall('/lib/systemd/system/linstor-controller.service; disabled; vendor preset: enabled',data)
        if result:
            return True


    # 没办法验证
    # def check_targetctl(self):
    #     cmd = 'systemctl status rtslib-fb-targetctl'
    #     data = utils.exec_cmd(cmd,self.conn)
    #     time.sleep(0)
    #     if result:
    #         return True

    def check_linstor_satellite(self):
        cmd = 'systemctl status linstor-satellite'
        data = utils.exec_cmd(cmd,self.conn)
        time.sleep(0)
        result = re.findall('/lib/systemd/system/linstor-satellite.service; enabled; vendor preset: enabled',data)
        if result:
            return True


    def check_linstor_pacemaker(self):
        cmd = 'systemctl status pacemaker'
        data = utils.exec_cmd(cmd,self.conn)
        time.sleep(0)
        result = re.findall('/lib/systemd/system/pacemaker.service; enabled; vendor preset: enabled',data)
        if result:
            return True


    def check_corosync(self):
        cmd = 'systemctl status corosync'
        data = utils.exec_cmd(cmd,self.conn)
        time.sleep(0)
        result = re.findall('/lib/systemd/system/corosync.service; enabled; vendor preset: enabled',data)
        if result:
            return True



class RA():

    def __init__(self,conn=None):
        self.conn = conn
        self.ra_path = self._get_ra_path()
        self.heartbeat_path = '/usr/lib/ocf/resource.d/heartbeat'
        self.ra_target = 'iSCSITarget.mod_cache_gena_acl_0'
        self.ra_logicalunit = 'iSCSILogicalUnit.450_patch1476_mod'


    def backup_iscsilogicalunit(self):
        cmd = f'mv {self.heartbeat_path}/iSCSILogicalUnit {self.heartbeat_path}/iSCSILogicalUnit.bak'
        if bool(utils.exec_cmd(f'[ -f {self.heartbeat_path}/iSCSILogicalUnit ] && echo True',self.conn)):
            utils.exec_cmd(cmd,self.conn)


    def backup_iscsitarget(self):
        cmd = f'mv {self.heartbeat_path}/iSCSITarget {self.heartbeat_path}/iSCSITarget.bak'
        if bool(utils.exec_cmd(f'[ -f {self.heartbeat_path}/iSCSITarget ] && echo True',self.conn)):
            utils.exec_cmd(cmd,self.conn)

    def cp_ra(self):
        cmd = 'cp %s/* %s/'%(self.ra_path,self.heartbeat_path)
        utils.exec_cmd(cmd,self.conn)

    def rename_ra(self):
        cmd = f'mv {self.heartbeat_path}/{self.ra_target} {self.heartbeat_path}/iSCSITarget;' \
            f'mv {self.heartbeat_path}/{self.ra_logicalunit} {self.heartbeat_path}/iSCSILogicalUnit'

        if bool(utils.exec_cmd(f'[ -f {self.heartbeat_path}/{self.ra_logicalunit} ] && echo True')) \
                and bool(utils.exec_cmd(f'[ -f {self.heartbeat_path}/{self.ra_logicalunit} ] && echo True')):
            utils.exec_cmd(cmd)


    def scp_ra(self,hostname):
        cmd = f'scp {self.heartbeat_path}/iSCSITarget {self.heartbeat_path}/iSCSILogicalUnit {hostname}:{self.heartbeat_path}/'
        utils.exec_cmd(cmd,self.conn)



    def check_ra_logicalunit(self):
        cmd = f'grep -rs "#{self.ra_logicalunit}" {self.heartbeat_path}/iSCSILogicalUnit'
        result = utils.exec_cmd(cmd,self.conn)
        if result:
            return True


    def check_ra_target(self):
        cmd = f'grep -rs "#{self.ra_target}" {self.heartbeat_path}/iSCSITarget'
        result = utils.exec_cmd(cmd,self.conn)
        if result:
            return True


    def _get_ra_path(self):
        # list_path_now = sys.path[0].split('/')
        # list_path_now.pop(-1)
        # list_path_now.append('RA')
        # ra_path = '/'.join(list_path_now)

        ra_path = '../RA'

        return ra_path



class HALinstorController():
    stencil = """primitive p_drbd_linstordb ocf:linbit:drbd \
        params drbd_resource=linstordb \
        op monitor interval=29 role=Master \
        op monitor interval=30 role=Slave \
        op start interval=0 timeout=240s \
        op stop interval=0 timeout=100s
primitive p_fs_linstordb Filesystem \
        params device="/dev/drbd/by-res/linstordb/0" directory="/var/lib/linstor" fstype=ext4 \
        op start interval=0 timeout=60s \
        op stop interval=0 timeout=100s \
        op monitor interval=20s timeout=40s
primitive p_linstor-controller systemd:linstor-controller \
        op start interval=0 timeout=100s \
        op stop interval=0 timeout=100s \
        op monitor interval=30s timeout=100s
group g_linstor p_fs_linstordb p_linstor-controller
ms ms_drbd_linstordb p_drbd_linstordb \
        meta master-max=1 master-node-max=1 clone-max=3 clone-node-max=1 notify=true
colocation c_linstor_with_drbd inf: g_linstor ms_drbd_linstordb:Master
order o_drbd_before_linstor inf: ms_drbd_linstordb:promote g_linstor:start"""


    def __init__(self,conn=None):
        self.conn = conn


    def linstor_is_conn(self):
        cmd_result = utils.exec_cmd('linstor n l',self.conn)
        if not 'Connection refused' in cmd_result:
            return True

    def pool0_is_exist(self,list_node):
        cmd = 'linstor sp l -s pool0 | cat'
        pool0_table = utils.exec_cmd(cmd,self.conn)
        for node in list_node:
            if not node in pool0_table:
                return False
        return True



    def create_rd(self,name):
        cmd = f"linstor resource-definition create {name}"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)

    def create_vd(self,name,size):
        cmd = f"linstor volume-definition create {name} {size}"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)

    def create_res(self,name,node,sp):
        cmd = f"linstor resource create {node} {name} --storage-pool {sp}"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)

    def delete_rd(self,name):
        cmd = f"linstor rd d {name}"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)

    def stop_controller(self):
        cmd = f"systemctl stop linstor-controller"
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def backup_linstor(self,backup_path):
        """
        E.g: backup_path = 'home/samba' 文件夹
        """
        cmd = f"rsync -avp /var/lib/linstor {backup_path}/"
        if not bool(utils.exec_cmd(f'[ -d {backup_path} ] && echo True', self.conn)):
            utils.exec_cmd(f"mkdir -p {backup_path}")
        utils.exec_cmd(cmd,self.conn)
        time.sleep(0)


    def get_controller(self):
        data = utils.exec_cmd("crm st | cat",self.conn)
        controller = re.findall("Masters: \[\s(\w*)\s\]",data)
        if controller:
            return controller[0]


    def is_active_controller(self):
        cmd_result = utils.exec_cmd("systemctl status linstor-controller | cat",self.conn)
        status = re.findall('Active:\s(\w*)\s', cmd_result)
        if status and status[0] == 'active':
            return True


    def move_database(self,backup_path):
        cmd_mkfs = "mkfs.ext4 /dev/drbd/by-res/linstordb/0"
        cmd_rm = "rm -rf /var/lib/linstor/*"
        cmd_mount = "mount /dev/drbd/by-res/linstordb/0 /var/lib/linstor"
        cmd_rsync = f"rsync -avp {backup_path}/linstor/ /var/lib/linstor/"

        utils.exec_cmd(cmd_mkfs,self.conn)
        utils.exec_cmd(cmd_rm,self.conn)
        utils.exec_cmd(cmd_mount,self.conn)
        utils.exec_cmd(cmd_rsync,self.conn)
        time.sleep(0)


    def add_linstordb_to_pacemaker(self,clone_max):
        self.stencil = self.stencil.replace(f'clone-max=3',f'clone-max={clone_max}')
        with open('crm_lincontrl_config','w') as f:
            f.write(self.stencil)
        cmd  = "crm config load update crm_lincontrl_config"
        utils.exec_cmd(cmd,self.conn)
        # 这里可以设置删除这个文件，但好像没有必要



    def check_linstor_controller(self,list_node):
        data = utils.exec_cmd('crm st | cat',self.conn)
        p_fs_linstordb = re.findall('p_fs_linstordb\s*\(ocf::heartbeat:Filesystem\):\s*(.*)',data)
        p_linstor_controller = re.findall('p_linstor-controller\s*\(systemd:linstor-controller\):\s*(.*)',data)
        masters = re.findall('Masters:\s\[\s(\w*)\s\]', data)
        slaves = re.findall('Slaves:\s\[\s(.*)\s\]', data)


        if not p_fs_linstordb or 'Started' not in p_fs_linstordb[0]:
            return
        if not p_linstor_controller or 'Started' not in p_linstor_controller[0]:
            return
        if not masters and len(masters) != 1:
            return
        if not slaves:
            return

        slaves = slaves[0].split(' ')
        all_node = []
        all_node.extend(masters)
        all_node.extend(slaves)
        if set(all_node) != set(list_node):
            return
        return True


    def check_linstor_file(self,path):
        data = utils.exec_cmd(f'ls -l {path}')
        if 'linstordb.mv.db' in data and \
            'linstordb.trace.db' in data and \
            'loop_device_mapping' in data:

            return True

    def get_linstordb_lv(self):
        cmd = 'lvs /dev/*/linstordb* -o lv_name,vg_name --noheadings'
        lv_data = utils.exec_cmd(cmd,self.conn)
        list_lv = []
        if not 'invalid characters' in lv_data:
            lv_all = re.findall('\s*(\w*)\s(\w*)',lv_data)
            if lv_all:
                list_lv = [f"/dev/{lv[1]}/{lv[0]}" for lv in lv_all]
        return list_lv

    def remove_lv(self,list_lv):
        """
        删除指定的lv，最后返回删除失败（已挂载）的lv列表
        :param lv_dict: E.g {'lv01':'vg01','lv02':'vg01'}
        :return:
        """

        fail_list = []
        for lv in list_lv:
            cmd = f"lvremove {lv} -y"
            cmd_result = utils.exec_cmd(cmd,self.conn)
            if 'in use' in cmd_result:
                fail_list.append(lv)

        return fail_list # 返回已挂载而导致无法删除的lv


    def umount_lv(self,list_lv):
        for lv in list_lv:
            cmd = f'umount {lv}'
            utils.exec_cmd(cmd,self.conn)


    def secondary_drbd(self,drbd):
        cmd = f'drbdadm secondary {drbd}'
        utils.exec_cmd(cmd,self.conn)

