# coding:utf-8
'''
Created on 2020/1/5
@author: Paul
@note: data post
'''
from flask import Flask,Blueprint

stor_blueprint = Blueprint("stor_blueprint", __name__)

# from . import views
from vplx_app.stor import views