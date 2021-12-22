# coding:utf-8
from flask import Flask, jsonify, render_template, request, make_response, views
from flask_cors import *
import copy
from execute import iscsi
import iscsi_json
import consts
import log

'''
@author: paul
@note: 防止跨域问题出现
'''
def cors_data(data_dict):
    response = make_response(jsonify(data_dict))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response

'''
@note: 从服务器上取值
request后面可以跟多种不同的取值方式，可以自行百度
'''
def get_request_data():
    if request.method == 'GET':
        str_data = request.args.items()
        dict_data = dict(str_data)
        tid = dict_data['tid']
        # 记录除了tid之后接收到的数据
        logger = log.Log()
        logger.tid = tid
        return dict_data

"""
@author: paul
@note: iSCSI创建资源类函数
"""  
class HostCreate(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        host = dict_data["host_name"]
        iqn = dict_data["host_iqn"]
        logger.write_to_log('OPRT', 'ROUTE', '/host/create', dict_data['ip'], dict_data)
        host_obj = iscsi.Host()
        host_create_results = host_obj.create(host, iqn)
        logger.write_to_log('DATA', 'RESULT', 'HostCreate', 'result', host_create_results)
        if host_create_results == True:
            result = "0"
        else:
            result = "1"
        logger.write_to_log('DATA', 'RETURN', 'HostCreate', 'result', result)
        return cors_data(result)

    
class HostGroupCreate(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        print(dict_data)
        logger = log.Log()
        host = dict_data['host'].split(',')
        host_group_name = dict_data["host_group_name"]
        logger.write_to_log('OPRT', 'ROUTE', '/hg/create', dict_data['ip'], dict_data)
        host_group_obj = iscsi.HostGroup()
        host_group_create_results = host_group_obj.create(host_group_name, host)
        logger.write_to_log('DATA', 'RESULT', 'HostGroupCreate', 'result', host_group_create_results)
        if host_group_create_results == True:
            result = "0"
        else:
            result = "1"
        logger.write_to_log('DATA', 'RETURN', 'HostGroupCreate', 'result', result)
        return cors_data(result)

    
class DiskGroupCreate(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        disk = dict_data['disk'].split(',')
        logger.write_to_log('OPRT', 'ROUTE', '/dg/create', dict_data['ip'], dict_data)
        disk_group_name = dict_data["disk_group_name"]
        disk_group_obj = iscsi.DiskGroup()

        disk_group_create_results = disk_group_obj.create(disk_group_name, disk)
        logger.write_to_log('DATA', 'RESULT', 'DiskGroupCreate', 'result', disk_group_create_results)
        if disk_group_create_results == True:
            result = "0"
        else:
            result = "1"
        logger.write_to_log('DATA', 'RETURN', 'DiskGroupCreate', 'result', result)
        return cors_data(result)

    
class MapCreate(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        map_name = dict_data["map_name"]
        host_group_name = dict_data["host_group"].split(',')
        disk_group_name = dict_data["disk_group"].split(',')
        print(disk_group_name)
        logger.write_to_log('OPRT', 'ROUTE', '/map/create', dict_data['ip'], dict_data)
        map_obj = iscsi.Map()
        map_create_results = map_obj.create(map_name, host_group_name, disk_group_name)
        logger.write_to_log('DATA', 'RESULT', 'MapCreate', 'result', map_create_results)
        if map_create_results == True:
            result = "0"
        else:
            result = "1"
        logger.write_to_log('DATA', 'RETURN', 'MapCreate', 'result', result)
        return cors_data(result)

'''
@note: 获取tid,网页传值，tid-时间戳
'''
def get_tid():
    if request.method == 'GET':
        str_transaction_id = request.args.items()
        dict_transaction = dict(str_transaction_id)
        return dict_transaction["transaction_id"]

'''
@author: paul
@note: 获取iSCSI数据路由
OprtALLxx为更新数据路由- 操作路由，调用update函数
AllxxxResult为获取数据路由
前后顺序
'''
# host
HOST_RESULT = None
def update_host():
    global HOST_RESULT
    js = iscsi_json.JsonOperation()
    js.json_data = js.read_json()
    HOST_RESULT = js.json_data['Host']
    
    return True


class OprtAllHost(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/host/show/oprt', dict_data['ip'], '')
        if update_host():
            logger.write_to_log('DATA', 'RETURN', 'OprtAllHost', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtAllHost', 'result', '1')
            return cors_data("1")

    
class AllHostResult(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('DATA', 'ROUTE', '/host/show/data', dict_data['ip'], '')
        if not HOST_RESULT:
            update_host()
        logger.write_to_log('DATA', 'RETURN', 'AllHostResult', 'result', HOST_RESULT)
        return cors_data(HOST_RESULT)


# disk   
DISK_RESULT = None


def update_disk():
    global DISK_RESULT
    disk = iscsi.Disk()
    disk.update_disk()
    js = iscsi_json.JsonOperation()
    DISK_RESULT = js.read_json()['Disk']
    return True


class OprtAllDisk(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/disk/show/oprt', dict_data["ip"], '')
        if update_disk():
            logger.write_to_log('DATA', 'RETURN', 'OprtAllDisk', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtAllDisk', 'result', '1')
            return cors_data("1")

    
class AllDiskResult(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('DATA', 'ROUTE', '/disk/show/data', dict_data["ip"], '')
        if not DISK_RESULT:
            update_disk()
        logger.write_to_log('DATA', 'RETURN', 'AllDiskResult', 'result', DISK_RESULT)
        print(DISK_RESULT)
        return cors_data(DISK_RESULT)


# hostgroup
HOSTGROUP_RESULT = None


def update_hg():
    global HOSTGROUP_RESULT

    js = iscsi_json.JsonOperation()
    host_group = iscsi.HostGroup()
    js.json_data = js.read_json()
    HOSTGROUP_RESULT = js.json_data['HostGroup']
    return True


class OprtAllHg(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/hg/show/oprt', dict_data['ip'], '')
        if update_hg():
            logger.write_to_log('DATA', 'RETURN', 'OprtAllHg', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtAllHg', 'result', '1')
            return cors_data("1")


class AllHgResult(views.MethodView):
    
    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('DATA', 'ROUTE', '/hg/show/data', dict_data['ip'], '')
        if not HOSTGROUP_RESULT:
            update_hg()
        logger.write_to_log('DATA', 'RETURN', 'AllHgResult', 'result', HOSTGROUP_RESULT)
        return cors_data(HOSTGROUP_RESULT)

    
# diskgroup
DISKGROUP_RESULT = None


def update_dg():
    global DISKGROUP_RESULT
    js = iscsi_json.JsonOperation()
    js.json_data = js.read_json()
    DISKGROUP_RESULT = js.json_data['DiskGroup']
    print(DISKGROUP_RESULT)
    return True


class OprtAllDg(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/dg/show/oprt', dict_data['ip'], '')
        if update_dg():
            logger.write_to_log('DATA', 'RETURN', 'OprtAllDg', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtAllDg', 'result', '1')
            return cors_data("1")

    
class AllDgResult(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('DATA', 'ROUTE', '/dg/show/data', dict_data['ip'], '')
        if not DISKGROUP_RESULT:
            update_dg()
        logger.write_to_log('DATA', 'RETURN', 'AllDgResult', 'result', DISKGROUP_RESULT)
        return cors_data(DISKGROUP_RESULT)
    
    
# map
MAP_RESULT = None


def update_map():
    global MAP_RESULT
    js = iscsi_json.JsonOperation()
    js.json_data = js.read_json()
    MAP_RESULT = js.json_data['Map']
    return True


class OprtAllMap(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/map/show/oprt', dict_data['ip'], '')
        if update_map():
            logger.write_to_log('DATA', 'RETURN', 'OprtAllMap', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtAllMap', 'result', '1')
            return cors_data("1")

    
class AllMapResult(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('DATA', 'ROUTE', '/map/show/data', dict_data['ip'], '')
        if not MAP_RESULT:
           update_map()
        logger.write_to_log('DATA', 'RETURN', 'AllMapResult', 'result', MAP_RESULT)
        return cors_data(MAP_RESULT)

'''
@author: paul
@note: iSCSI修改资源路由
CheckxxModify为验证判断路由，返回修改影响到前端展示。
xxModify为实际修改路由，触发实际修改动作，返回修改结果到前端
'''


class CheckHostModify(views.MethodView):
    def get(self):
        print("0000000")
        dict_data = get_request_data()
        print("1111111")
        host_name = dict_data['host_name']
        print("0022200")
        host_iqn = dict_data['host_iqn']
        print("111111")
        js = iscsi_json.JsonOperation()
        print("2222")
        js.json_data = js.read_json()
        print("13333331")
        json_data_before = copy.deepcopy(js.json_data)
        print("13444444331")
        js.update_data('Host', host_name, host_iqn)
        print("6555555533331")
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        print("65566666663331")
        message = '\n'.join(obj_iscsi.show_info())
        print("--------------")
        print("message",message)
        dict = {'iscsi_data':True, 'info':message}
        return cors_data(dict)


class HostModify(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        host_name = dict_data['host_name']
        host_iqn = dict_data['host_iqn']
        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        js.update_data('Host', host_name, host_iqn)
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        # 确认JSON文件在途中未被修改
        json_data_now = js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.create_iscsilogicalunit()
            obj_iscsi.delete_iscsilogicalunit()
            obj_iscsi.modify_iscsilogicalunit()
            js.commit_data()
            message = '操作完成'
        else:
            message = '配置文件已被修改，请重新操作'
        return cors_data(message)

  
class CheckHgModify(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        hg = dict_data['hg_name']
        list_host = dict_data['host'].split(',') if dict_data['host'] else []

        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        js.update_data('HostGroup', hg, list_host)
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        message = '\n'.join(obj_iscsi.show_info())
        dict = {'iscsi_data': True, 'info': message}
        return cors_data(dict)


class HgModify(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        hg = dict_data['hg_name']
        list_host = dict_data['host'].split(',') if dict_data['host'] else []
        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        if not list_host:
            js.delete_data('HostGroup',hg)
            js.arrange_data('HostGroup',hg)
        else:
            js.update_data('HostGroup', hg, list_host)
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        # 确认JSON文件在途中未被修改
        json_data_now = js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.create_iscsilogicalunit()
            obj_iscsi.delete_iscsilogicalunit()
            obj_iscsi.modify_iscsilogicalunit()
            js.commit_data()
            message = '操作完成'
        else:
            message = '配置文件已被修改，请重新操作'
        return cors_data(message)
    

class CheckDgModify(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        dg = dict_data['dg_name']
        list_disk = dict_data['disk'].split(',') if dict_data['disk'] else []
        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        js.update_data('DiskGroup', dg, list_disk)
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        message = '\n'.join(obj_iscsi.show_info())
        dict = {'iscsi_data': True, 'info': message}
        return cors_data(dict)


class DgModify(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        dg = dict_data['dg_name']
        list_disk = dict_data['disk'].split(',') if dict_data['disk'] else []

        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        if not list_disk:
            js.delete_data('DiskGroup',dg)
            js.arrange_data('DiskGroup',dg)
        else:
            js.update_data('DiskGroup', dg, list_disk)
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        # 确认JSON文件在途中未被修改
        json_data_now = js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.create_iscsilogicalunit()
            obj_iscsi.delete_iscsilogicalunit()
            obj_iscsi.modify_iscsilogicalunit()
            js.commit_data()
            message = '操作完成'
        else:
            message = '配置文件已被修改，请重新操作'
        return cors_data(message)
    

class CheckMapModify(views.MethodView):

    def get(self):
        dict_data = get_request_data()
        map = dict_data['map_name']
        print(dict_data)
        list_hg = dict_data['hg'].split(',') if dict_data['hg'] else []
        list_dg = dict_data['dg'].split(',') if dict_data['dg'] else []
        js = iscsi_json.JsonOperation()
        json_data_before = copy.deepcopy(js.json_data)
        if not list_hg or not list_dg:
            js.delete_data('Map',map)
        else:
            js.update_data('Map',map,{'HostGroup': list_hg, 'DiskGroup': list_dg})
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        message = '\n'.join(obj_iscsi.show_info())
        dict = {'iscsi_data': True, 'info': message}
        return cors_data(dict)


class MapModify(views.MethodView):

    def get(self):

        dict_data = get_request_data()
        map = dict_data['map_name']
        list_hg = dict_data['hg'].split(',') if dict_data['hg'] else []
        list_dg = dict_data['dg'].split(',') if dict_data['dg'] else []
        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        if not list_hg or not list_dg:
            js.delete_data('Map',map)
        else:
            js.update_data('Map',map,{'HostGroup': list_hg, 'DiskGroup': list_dg})

        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        # 确认JSON文件在途中未被修改
        json_data_now = js.read_json()
        if json_data_before == json_data_now:
            try:
                obj_iscsi.create_iscsilogicalunit()
                obj_iscsi.delete_iscsilogicalunit()
                obj_iscsi.modify_iscsilogicalunit()
            except Exception:
                message = '执行失败'
            else:
                js.commit_data()
                message = '操作完成'
        else:
            message = '配置文件已被修改，请重新操作'
        return cors_data(message)


'''

@author: paul
@note: iSCSI删除资源
@bug: 可修改建议，前端返回2个值，一个类型，一个值，类型值"Hg"等，值指具体的Hg的值。


'''
class CheckAllDelete(views.MethodView):
 
    def get(self):
        dict_data = get_request_data()
        iscsi_type = dict_data['iscsi_type']
        iscsi_name = dict_data['iscsi_name']

        print(iscsi_type, iscsi_name)

        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        js.delete_data(iscsi_type,iscsi_name)
        if iscsi_type != 'Map':
            js.arrange_data(iscsi_type, iscsi_name)
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        message = '\n'.join(obj_iscsi.show_info())
        dict = {'iscsi_data':True, 'info':message}
        return cors_data(dict)
 
 
class AllDelete(views.MethodView):
 
    def get(self):
        dict_data = get_request_data()
        iscsi_type = dict_data['iscsi_type']
        iscsi_name = dict_data['iscsi_name']

        print(iscsi_type,iscsi_name)

        js = iscsi_json.JsonOperation()
        js.json_data = js.read_json()
        json_data_before = copy.deepcopy(js.json_data)
        try:
            js.delete_data(iscsi_type, iscsi_name)
        except KeyError:
            message = '配置文件已被修改，请重新操作'
            return cors_data(message)
        
        if iscsi_type != 'Map':
            js.arrange_data(iscsi_type, iscsi_name)
        obj_iscsi = iscsi.IscsiConfig(json_data_before, js.json_data)
        # 确认JSON文件在途中未被修改
        json_data_now = js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.create_iscsilogicalunit()
            obj_iscsi.delete_iscsilogicalunit()
            obj_iscsi.modify_iscsilogicalunit()
            js.commit_data()
            message = '操作完成'
        else:
            message = '配置文件已被修改，请重新操作'
        return cors_data(message)
