import paramiko
import subprocess
import yaml

def read_config(yaml_name):
    try:
        with open(yaml_name, encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"配置文件读取错误，请检查配置文件名: {yaml_name}")
    except TypeError:
        print("配置文件读取错误，请检查输入的类型")

def check_id_rsa_pub(ssh_obj):
    cmd = '[ -f /root/.ssh/id_rsa.pub ] && echo True || echo False'
    result = ssh_obj.exec_cmd(cmd)
    result = result.replace(" ","")
    result = result.replace("\n","")
    if result == 'False':
        return True
    else:
        return False

def create_id_rsa_pub(ssh_obj):
    cmd = 'ssh-keygen -f /root/.ssh/id_rsa -N ""'
    result = ssh_obj.exec_cmd(cmd)
    if not result:
        return False
    else:
        return True


