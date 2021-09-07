import control
import sys



controller = control.KSConsole()

if len(sys.argv) == 2 and sys.argv[1] == 'kk':
    print("运行kk")
    controller.modify_kk()
    controller.buidl_ks()

elif len(sys.argv) == 2 and sys.argv[1] == 'vip':
    print("配置HAproxy")
    controller.install_haproxy()
    controller.modify_haproxy()
    controller.restart_haproxy()

    print("配置Keepalived")
    controller.install_keepalived()
    controller.modify_keepalived()
    controller.restart_keepalived()
elif len(sys.argv) > 2:
    print("输入参数kk/vip，或者不输入参数执行全部流程")

else:
    print("配置HAproxy")
    controller.install_haproxy()
    controller.modify_haproxy()
    controller.restart_haproxy()

    print("配置Keepalived")
    controller.install_keepalived()
    controller.modify_keepalived()
    controller.restart_keepalived()

    print("安装KK配置KS集群")
    controller.install_docker()
    controller.install_kk()
    controller.modify_kk()
    controller.buidl_ks()



