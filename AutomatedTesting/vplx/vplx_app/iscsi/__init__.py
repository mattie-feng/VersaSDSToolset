# coding:utf-8

from flask import Flask,Blueprint

iscsi_blueprint = Blueprint("iscsi_blueprint", __name__)

from vplx_app.iscsi import views
# from . import views