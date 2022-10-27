import paramiko
import subprocess
import logging
import sys
import time
import re

def exec_cmd(cmd, conn=None):
    if conn:
        result = conn.exec_cmd(cmd)
    else:
        result = subprocess.getoutput(cmd)
    log_data = f'{conn._host if conn else "localhost"} - {cmd} - {result}'
    Log().logger.info(log_data)
    if result:
        result = result.rstrip('\n')
    return result

class SSHConn(object):

    def __init__(self, host, port=22, username=None, password=None, timeout=None):
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
            data = stdout.read()
            if len(data) > 0:
                data = data.decode() if isinstance(data, bytes) else data
                return data
            err = stderr.read()
            if len(err) > 0:
                err = err.decode() if isinstance(err, bytes) else err
                return False

    def exec_copy_id_rsa_pub(self,target_ip,passwd):
        cmd = f'ssh-copy-id -o stricthostkeychecking=no -i /root/.ssh/id_rsa.pub root@{target_ip}'
        conn = self.SSHConnection.invoke_shell()
        conn.keep_this = self.SSHConnection
        print(cmd)
        time.sleep(2)
        conn.send(cmd + '\n')
        time.sleep(2)
        stdout = conn.recv(1024)
        info = stdout.decode()
        result = re.findall(r'Number of key(s) added: 1',info)
        if result == []:
            time.sleep(2)
            conn.send(passwd + '\n')

        time.sleep(1)
        stdout = conn.recv(9999)

    def ssh_close(self):
        self.SSHConnection.close()


class Log(object):
    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            Log._instance = super().__new__(cls)
            Log._instance.logger = logging.getLogger()
            Log._instance.logger.setLevel(logging.INFO)
            Log.set_handler(Log._instance.logger)
        return Log._instance

    @staticmethod
    def set_handler(logger):
        fh = logging.FileHandler('./SSHFreeLog.log', mode='a')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)