import gevent
from gevent import monkey
import time
import sys

import utils
import action


class Bonding():
    def __init__(self, file):
        self.config = utils.ConfFile(file)
        self.host_config = self.config.get_config()

    def create_bonding(self):
        for host in self.host_config:
            bonding = action.IpService(host[0])
            bonding.set_bonding("bond0", host[1])
            bonding.add_bond_slave()
