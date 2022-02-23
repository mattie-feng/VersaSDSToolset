# coding:utf-8
'''
Created on 2020/3/2
@author: Paul
@note: data post
'''

from flask import Flask, Blueprint

def create_app():

    from vplx_app.stor import stor_blueprint
    from vplx_app.iscsi import iscsi_blueprint

    app = Flask(__name__)

    # 将蓝图注册到app
    app.register_blueprint(stor_blueprint)
    app.register_blueprint(iscsi_blueprint)
    return app
