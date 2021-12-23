# coding:utf-8
'''
Created on 2020/3/2
@author: Paul
@note: data
'''

from flask import views
from vplx_app.stor import stor_blueprint
from vplx_app.stor import model
'''
@note: LINSTOR数据api
'''
stor_blueprint.add_url_rule('/resource/show/oprt', view_func=model.OprtResource.as_view('resource_oprt'))
stor_blueprint.add_url_rule('/resource/show/data', view_func=model.ResourceResult.as_view('resource_data'))
 
stor_blueprint.add_url_rule('/node/show/oprt', view_func=model.OprtNode.as_view('node_oprt'))
stor_blueprint.add_url_rule('/node/show/data', view_func=model.NodeResult.as_view('node_data'))
 
stor_blueprint.add_url_rule('/storagepool/show/oprt', view_func=model.OprtStoragepool.as_view('storagepool_oprt'))
stor_blueprint.add_url_rule('/storagepool/show/data', view_func=model.StoragepoolResult.as_view('storagepool_data'))

'''
@note: 删除api
'''
stor_blueprint.add_url_rule('/resource/show/delete', view_func=model.ResourceD.as_view('resource_d'))
stor_blueprint.add_url_rule('/node/show/delete', view_func=model.NodeD.as_view('node_d'))
stor_blueprint.add_url_rule('/storagepool/show/delete', view_func=model.StoragepoolD.as_view('storagepool_d'))

'''
@note: 修改api
'''
stor_blueprint.add_url_rule('/LINSTOR/modify', view_func=model.LINSTORModify.as_view('linstor_modify'))

'''
@note: 创建资源api
'''
stor_blueprint.add_url_rule('/LINSTOR/SP/Create', view_func=model.SpCreate.as_view('sp_create'))
stor_blueprint.add_url_rule('/LINSTOR/Node/Create', view_func=model.NodeCreate.as_view('node_create'))
stor_blueprint.add_url_rule('/LINSTOR/Resource/Create', view_func=model.ResourceCreate.as_view('resource_create'))

'''
@note:交互
'''
stor_blueprint.add_url_rule('/LINSTOR', view_func=model.LINSTORView.as_view('LINSTORview'))
stor_blueprint.add_url_rule('/LINSTOR/Create/lvm', view_func=model.lvmView.as_view('lvmview'))
stor_blueprint.add_url_rule('/LINSTOR/Create/sp', view_func=model.spView.as_view('spview'))
stor_blueprint.add_url_rule('/LINSTOR/Create/node_create', view_func=model.nodecreateView.as_view('nodecreateview'))
stor_blueprint.add_url_rule('/LINSTOR/Create/node_num', view_func=model.nodenumView.as_view('nodenumview'))

