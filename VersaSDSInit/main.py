import control
import utils

import datetime
import action





controller = control.Scheduler()

controller.get_ssh_conn()
# controller.service_set()
# print(controller.check_service())

controller.replace_ra()

# controller.get_ssh_conn()
# controller.sync_time()
# print('同步时间结束')
# controller.corosync_conf_change()
# print('修改coro配置文件结束')
# controller.restart_corosync()
# print('执行重启')



# print(controller.check_corosync())


def run():
