# -*- coding:utf-8 -*-
import action
import sys


def set_nmcli_config():
    """设置使network-manager可用"""
    network_manager = action.NetworkManagerService()
    print("Start to modify NetworkManager.conf ...")
    if network_manager.modify_config():
        print("Start to set renderer to NetworkManager ...")
        if network_manager.modify_renderer():
            print("netplan apply ...")
            if network_manager.netplan_apply():
                print("Start to restart NetworkManager ...")
                if network_manager.restart_network_manager():
                    return True


def all_deploy(conf_args):
    """一键执行完成软件安装以及配置、root密码设置、允许以root用户登录、连接IP的设置的功能"""
    install = action.InstallSoftware()
    root_config = action.RootConfig()
    system_service = action.SystemService()
    set_hostname(conf_args)
    print("\nPrepare to install software...")
    if install.update_apt():
        print("Start to install openssh-server")
        if install.install_software("openssh-server"):
            print(" Start openssh service")
            if system_service.oprt_ssh_service("start"):
                print("Set can be logged as root")
                if root_config.set_root_permit_login():
                    print(" Restart openssh service")
                    system_service.oprt_ssh_service("restart")
        print("Start to install network-manager")
        if install.install_software("network-manager"):
            print(" Start to set network-manager config")
            if set_nmcli_config():
                set_local_ip(conf_args)
        print("\n")
    else:
        sys.exit()


def set_root_pwd(conf_args):
    """root密码设置、重启SSH服务"""
    system_service = action.SystemService()
    root_config = action.RootConfig()
    print(" Start to set root password")
    root_config.set_root_password(conf_args["Root new password"])
    print(" Start to restart openssh service")
    system_service.oprt_ssh_service("restart")
    print("Finish to set root password and can be logged as root")


def set_local_ip(conf_args):
    """连接IP的设置的功能"""
    ip_service = action.IpService()
    print(f"Start to set {conf_args['IP']} on the {conf_args['Device']}")
    ssh_service = action.SystemService()
    if ip_service.set_local_ip(conf_args['Device'], conf_args['IP'], conf_args['Gateway']):
        ip_service.up_local_ip_service(conf_args['Device'])
        print(" Start to restart openssh service")
        ssh_service.oprt_ssh_service("restart")
        print(f"Finish to set {conf_args['IP']} on the {conf_args['Device']}")


def set_hostname(conf_args):
    system_service = action.SystemService()
    print('Start to modify hostname')
    system_service.modify_hostname(conf_args["Hostname"])
    system_service.modify_hostsfile('127.0.1.1', conf_args["Hostname"])
    print(f"Finish to modify hostname")
