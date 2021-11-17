# -*- coding: utf-8 -*-
import paramiko
import socket
import subprocess
import yaml
import sys
import re
import time
import traceback
from functools import wraps
import log


def _init():  # 全局变量初始化
    global _global_dict
    _global_dict = {}

    global _times
    _times = 0


def set_global_dict_value(key, value):
    _global_dict[key] = value


def get_global_dict_value(key):
    try:
        return _global_dict[key]
    except KeyError:
        # print("KeyError of global value.")
        return get_host_ip()


def set_times(value):
    global _times
    _times = value


def get_times():
    return _times


def prt_log(logger, conn, str_, warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    print(str(str_))
    if warning_level == 0:
        logger.write_to_log(conn, 'INFO', 'INFO', 'finish', 'output', str_)
    elif warning_level == 1:
        logger.write_to_log(conn, 'INFO', 'WARNING', 'fail', 'output', str_)
    elif warning_level == 2:
        logger.write_to_log(conn, 'INFO', 'ERROR', 'exit', 'output', str_)
        sys.exit()


def deco_yaml_dict(func):
    """
    装饰器，判断yaml文件的key是否存在，不存在则提示并退出
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(self, *args):
        try:
            result = func(self, *args)
            return result
        except Exception as e:
            self.logger.write_to_log(None, 'DATA', 'DEBUG', 'exception', '', str(traceback.format_exc()))
            print(e)
            sys.exit()

    return wrapper


def exec_cmd(cmd, logger, conn=None):
    oprt_id = log.create_oprt_id()
    func_name = traceback.extract_stack()[-2][2]
    logger.write_to_log(conn, 'DATA', 'STR', func_name, '', oprt_id)
    logger.write_to_log(conn, 'OPRT', 'CMD', func_name, oprt_id, cmd)
    if conn:
        result = conn.exec_cmd(cmd)
        logger.write_to_log(conn, 'DATA', 'CMD', func_name, oprt_id, result)
        return result
    else:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding="utf-8")
        if p.returncode == 0:
            result = p.stdout
            logger.write_to_log(conn, 'DATA', 'CMD', func_name, oprt_id, {"st": True, "rt": result})
            return {"st": True, "rt": result}
        else:
            logger.write_to_log(conn, 'DATA', 'CMD', func_name, oprt_id, {"st": False, "rt": p.stderr})
            return {"st": False, "rt": p.stderr}


def check_ip(ip):
    """检查IP格式"""
    re_ip = re.compile(
        r'^((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})(\.((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})){3}$')
    result = re_ip.match(ip)
    if result:
        return True
    else:
        print(f"ERROR in IP format of {ip}, please check.")
        return False


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def re_search(logger, re_string, tgt_string, output_type='bool'):
    oprt_id = log.create_oprt_id()
    re_obj = re.compile(re_string)
    re_result = re_obj.search(tgt_string)
    logger.write_to_log(None, 'OPRT', 'REGULAR', 're_search', oprt_id, {'re': re_string, 'string': tgt_string})
    if re_result:
        if output_type == 'bool':
            re_result = True
        if output_type == 'groups':
            re_result = re_result.groups()
        if output_type == 'group':
            re_result = re_result.group()
    logger.write_to_log(None, 'DATA', 'REGULAR', 're_search', oprt_id, re_result)
    return re_result


def re_findall(logger, re_string, tgt_string):
    oprt_id = log.create_oprt_id()
    re_obj = re.compile(re_string)
    logger.write_to_log(None, 'OPRT', 'REGULAR', 're_findall', oprt_id, {'re': re_string, 'string': tgt_string})
    re_result = re_obj.findall(tgt_string)
    logger.write_to_log(None, 'DATA', 'REGULAR', 're_findall', oprt_id, re_result)
    return re_result


class SSHConn(object):

    def __init__(self, host, port=22, username="root", password=None, timeout=8):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self.ssh_connect()

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            # time.sleep(1)
            # objSSHClient.exec_command("\x003")
            self.SSHConnection = objSSHClient
        except:
            print(f" Failed to connect {self._host}")

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            print(f'Connect retry for {self._host}')
            self._connect()
            if not self.SSHConnection:
                sys.exit()

    def exec_cmd(self, command):
        if self.SSHConnection:
            stdin, stdout, stderr = self.SSHConnection.exec_command(command)
            err = stderr.read()
            if len(err) > 0:
                err = err.decode() if isinstance(err, bytes) else err
                return {"st": False, "rt": err}
            data = stdout.read()
            if len(data) >= 0:
                data = data.decode() if isinstance(data, bytes) else data
                return {"st": True, "rt": data}

    def exec_cmd_and_print(self, command):
        result = ''
        if self.SSHConnection:
            stdin, stdout, stderr = self.SSHConnection.exec_command(command, get_pty=True, bufsize=1)
            while not stdout.channel.exit_status_ready():
                # print(f"{command} in progress....")
                time.sleep(1)
                result = stdout.readline()
                print(result)
                if stdout.channel.exit_status_ready():
                    # a = stdout.readlines()
                    # print(a)
                    print(f"{command} finished....")
                    break
            return {"st": True, "rt": result}


class ConfFile():
    def __init__(self, file, logger):
        self.yaml_file = file
        self.logger = logger
        self.config = self.read_yaml()

    def read_yaml(self):
        """读YAML文件"""
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_dict = yaml.safe_load(f)
                self.logger.write_to_log(None, "DATA", 'INPUT', 'yaml_file', self.yaml_file, yaml_dict)
            return yaml_dict
        except FileNotFoundError:
            prt_log(self.logger, None, f"Please check the file name: {self.yaml_file}", 2)
        except TypeError:
            prt_log(self.logger, None, "Error in the type of file name.", 2)

    @deco_yaml_dict
    def get_vplx_configs(self):
        for vplx_config in self.config["versaplx"]:
            if not check_ip(vplx_config['public_ip']):
                prt_log(self.logger, None, f"Please check the config of {vplx_config['public_ip']}", 2)
        return self.config["versaplx"]

    @deco_yaml_dict
    def get_test_mode(self):
        test_mode_list = ["quorum", "iscsi", "drbd_in_used"]
        if self.config["test_mode"] not in test_mode_list:
            prt_log(self.logger, None, f"Please check whether the config of test_mode in {test_mode_list}", 2)
        return self.config["test_mode"]

    @deco_yaml_dict
    def get_use_case(self):
        return self.config["use_case"]

    @deco_yaml_dict
    def get_test_times(self):
        if not isinstance(self.config["test_times"], int):
            prt_log(self.logger, None, "Please enter test_times of int type", 2)
        return self.config["test_times"]

    @deco_yaml_dict
    def get_resource_size(self):
        return self.config["resource_size"]

    @deco_yaml_dict
    def get_resource(self):
        return self.config["resource"]

    @deco_yaml_dict
    def get_target(self):
        return self.config["target"]

    @deco_yaml_dict
    def get_crm_log_path(self):
        return self.config["crm_log_path"]

    @deco_yaml_dict
    def get_device(self):
        return self.config["device"]
