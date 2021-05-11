import sys
import gevent
from gevent import monkey

from ssh_authorized import SSHAuthorizeNoMGN
import utils
import action
import time

# 协程相关的补丁
monkey.patch_all()


timeout = gevent.Timeout(10)
#



class Scheduler():
    """
    多协程调度
    """

    def __init__(self):
        self.conf_file = utils.ConfFile()
        self.cluster = self.conf_file.cluster
        self.list_ssh = []


    def get_ssh_conn(self):
        ssh = SSHAuthorizeNoMGN()
        local_ip = utils.get_host_ip()
        for node in self.cluster['node']:
            if local_ip == node['ip1']:
                self.list_ssh.append(None)
            else:
                self.list_ssh.append(ssh.make_connect(node['ip1'],node['port'],'root',node['root_password']))

        return self.list_ssh


    def modify_hostname(self):
        lst = []
        for ssh,node in zip(self.list_ssh,self.cluster['node']):
            lst.append(gevent.spawn(action.Host(ssh).modify_hostname,node['hostname']))
        gevent.joinall(lst)

    def ssh_conn_build(self):
        ssh = SSHAuthorizeNoMGN()
        ssh.init_cluster_no_mgn('cluster',self.cluster['node'],self.list_ssh)

    def check_hostname(self):
        lst = []
        for ssh,node in zip(self.list_ssh,self.cluster['node']):
            lst.append(gevent.spawn(action.Host(ssh).check_hostname,node['hostname']))
        gevent.joinall(lst)
        result = [job.value for job in lst]
        return result #[True, True, True, True]


    def check_ssh_authorized(self):
        lst = []
        cluster_hosts = [node['hostname'] for node in self.cluster['node']]
        for ssh in self.list_ssh:
            lst.append(gevent.spawn(action.Host(ssh).check_ssh,cluster_hosts))
        gevent.joinall(lst)
        result = [job.value for job in lst]
        return result


    def sync_time(self):
        lst = []
        for ssh in self.list_ssh:
            lst.append(gevent.spawn(action.Corosync(ssh).sync_time))
        gevent.joinall(lst)



    def corosync_conf_change(self):
        lst = []
        cluster_name = self.conf_file.get_cluster_name()
        bindnetaddr = self.conf_file.get_bindnetaddr()[1]
        interface = self.conf_file.get_inferface()
        nodelist = self.conf_file.get_nodelist()

        for ssh in self.list_ssh:
            lst.append(gevent.spawn(action.Corosync(ssh).change_corosync_conf,
                                    cluster_name,
                                    bindnetaddr,
                                    interface,
                                    nodelist))

        gevent.joinall(lst)



    def restart_corosync(self):
        lst = []
        timeout.start()
        for ssh in self.list_ssh:
            lst.append(gevent.spawn(action.Corosync(ssh).restart_corosync))
        try:
            gevent.joinall(lst)
        except gevent.Timeout:
            print('执行重启corosync服务超时')
        else:
            timeout.close()


    def check_corosync(self):
        nodes = [node['hostname'] for node in self.cluster['node']]
        lst_ring_status = []
        lst_cluster_status = []
        for ssh,node in zip(self.list_ssh,self.cluster['node']):
            corosync = action.Corosync(ssh)
            lst_ring_status.append(gevent.spawn(corosync.check_ring_status,node))
            lst_cluster_status.append(gevent.spawn(corosync.check_corosync_status,nodes))

        gevent.joinall(lst_ring_status)
        gevent.joinall(lst_cluster_status)

        lst = []
        for x,y in zip([i.value for i in lst_ring_status],[i.value for i in lst_cluster_status]):
            if x and y:
                lst.append(True)
            else:
                lst.append(False)

        return lst


    def packmaker_conf_change(self):
        cluster_name = self.conf_file.get_cluster_name()
        packmaker = action.Pacemaker()

        lst = []
        lst.append(gevent.spawn(packmaker.modify_cluster_name,cluster_name))
        lst.append(gevent.spawn(packmaker.modify_policy))
        lst.append(gevent.spawn(packmaker.modify_stickiness))
        lst.append(gevent.spawn(packmaker.modify_stonith_enabled))

        gevent.joinall(lst)


    def check_packmaker(self):
        cluster_name = self.conf_file.get_cluster_name()
        packmaker = action.Pacemaker()
        return packmaker.check_crm_conf(cluster_name)




    def targetcli_conf_change(self):
        lst = []
        for ssh in self.list_ssh:
            print(ssh)
            targetcli = action.TargetCLI(ssh)
            lst.append(gevent.spawn(targetcli.set_auto_add_default_portal))
            lst.append(gevent.spawn(targetcli.set_auto_add_mapped_luns))
            lst.append(gevent.spawn(targetcli.set_auto_enable_tpgt))

        gevent.joinall(lst)


    def check_targetcli(self):
        lst = []
        for ssh in self.list_ssh:
            targetcli = action.TargetCLI(ssh)
            lst.append(gevent.spawn(targetcli.check_targetcli_conf))

        gevent.joinall(lst)
        result = [job.value for job in lst]
        return result


    def service_set(self):
        lst = []
        for ssh in self.list_ssh:
            executor = action.ServiceSet(ssh)
            lst.append(gevent.spawn(executor.set_disable_drbd))
            lst.append(gevent.spawn(executor.set_disable_linstor_controller))
            lst.append(gevent.spawn(executor.set_disable_targetctl))
            lst.append(gevent.spawn(executor.set_enable_linstor_satellite))
            lst.append(gevent.spawn(executor.set_enable_pacemaker))
            lst.append(gevent.spawn(executor.set_enable_corosync))

        gevent.joinall(lst)



    def check_service(self):
        lst = []
        for ssh in self.list_ssh:
            check_result = []
            executor = action.ServiceSet(ssh)
            check_result.append(gevent.spawn(executor.check_drbd))
            check_result.append(gevent.spawn(executor.check_linstor_controller))
            check_result.append(gevent.spawn(executor.check_linstor_satellite))
            check_result.append(gevent.spawn(executor.check_linstor_pacemaker))
            check_result.append(gevent.spawn(executor.check_corosync))
            gevent.joinall(check_result)
            check_result = [job.value for job in check_result]
            if all(check_result):
                lst.append(True)
            else:
                lst.append(False)

        return lst



    def replace_ra(self):
        other_node = []
        for ssh,node in zip(self.list_ssh,self.cluster['node']):
            executor = action.RA(ssh)
            lst = []
            lst.append(gevent.spawn(executor.backup_iscsilogicalunit()))
            lst.append(gevent.spawn(executor.backup_iscsitarget()))
            if ssh:
                other_node.append(node['hostname'])

        executor = action.RA()
        executor.cp_ra()
        executor.rename_ra()
        for node in other_node:
            executor.scp_ra(node)

    def set_ip_on_device(self):
        lst_set = []

        for ssh, node in zip(self.list_ssh, self.cluster['node']):
            ip_service = action.IpService(ssh)
            lst_set.append(gevent.spawn(ip_service.set_ip, node['private_ip']['device'], node['private_ip']['ip'], node['private_ip']['gateway']))
        gevent.joinall(lst_set)
        self.up_ip_service()
        print("Finish to set ip")

    def modify_ip_on_device(self):
        lst_modify = []

        for ssh, node in zip(self.list_ssh, self.cluster['node']):
            ip_service = action.IpService(ssh)
            lst_modify.append(gevent.spawn(ip_service.modify_ip, node['private_ip']['device'], node['private_ip']['ip'], node['private_ip']['gateway']))
        gevent.joinall(lst_modify)
        self.up_ip_service()
        print("Finish to modify ip")

    def up_ip_service(self):
        lst_up = []
        for ssh, node in zip(self.list_ssh, self.cluster['node']):
            ip_service = action.IpService(ssh)
            lst_up.append(gevent.spawn(ip_service.up_ip_service, node['private_ip']['device']))
        gevent.joinall(lst_up)