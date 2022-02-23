import json
import os
import subprocess
from collections import Counter
from unittest.mock import patch

import pytest

import iscsi_json


class TestJsonOperation:

    def setup_class(self):
        # path = '../vplx/map_config.json'
        # os.remove(path)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        self.js = iscsi_json.JsonOperation()
        self.js.json_data = {
            "Host": {},
            "Disk": {},
            "HostGroup": {},
            "DiskGroup": {},
            "Map": {},
            "Portal": {},
            "Target": {}}
    @staticmethod
    def teardown_class():
        with open('../vplx/map_config.json', "w") as fw:
            json_dict = {
                "Host": {},
                "Disk": {},
                "HostGroup": {},
                "DiskGroup": {},
                "Map": {},
                "Portal": {},
                "Target": {}}
            json.dump(json_dict, fw, indent=4, separators=(',', ': '))
        # 同步下资源
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        # 修改json文件权限
        subprocess.run('chmod -R 777 map_config.json', shell=True)
        # 删除测试json文件
        # path = '../vplx/map_config.json'
        # os.remove(path)

    # 1.成功返回 json_dict
    # 2.文件不存在时新建一个空的 json 文件，有相应的数据结构
    # 3.文件格式不是 json 读取失败返回None，print('Failed to read json file.')
    def test_read_json(self):
        """JsonOperation 类读取 json 文件测试函数，测试用例包括：正常读取/文件不存在/文件格式不是json"""
        assert self.js.read_json() is not None
        # 删除文件使文件不存在
        path = '../vplx/map_config.json'
        os.remove(path)
        # json config 初创需要同步后才能执行之后的操作，不然抛出SystemExit
        with pytest.raises(SystemExit) as exsinfo:
            self.js.read_json()
        assert exsinfo.type == SystemExit
        # assert self.js.read_json() == json_dict
        # 破坏 json 正确结构
        with open(path, 'a') as json:
            json.write('ahdfjksj')
        with pytest.raises(SystemExit) as exsinfo:
            self.js.read_json()
            with patch('builtins.print') as terminal_print:
                terminal_print.assert_called_with('Failed to read json file.')
        assert exsinfo.type == SystemExit
        # 删除错误文件
        os.remove(path)

    # 该函数已删除
    # 修改为 update_data
    # def test_add_data(self):

    def test_update_data(self):
        """JsonOperation 类更新 json 数据测试函数"""
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        data = self.js.update_data('Disk', 'pytest_disk', 'pytest_path')
        assert data == {'pytest_disk': 'pytest_path'}
        data_host = self.js.update_data('Host', 'pytest_host', 'pytest_iqn')
        assert data_host['pytest_host'] == 'pytest_iqn'
        data_hg = self.js.update_data('HostGroup', 'pytest_hg', ['pytest_host1', 'pytest_host2'])
        assert data_hg['pytest_hg'] == ['pytest_host1', 'pytest_host2']
        data_dg = self.js.update_data('DiskGroup', 'pytest_dg', ['pytest_disk1', 'pytest_disk2'])
        assert data_dg['pytest_dg'] == ['pytest_disk1', 'pytest_disk2']
        data_map = self.js.update_data('Map', 'pytest_map', {'HostGroup': ['pytest_hg'], 'DiskGroup': ['pytest_dg']})
        assert data_map['pytest_map'] == {'HostGroup': ['pytest_hg'], 'DiskGroup': ['pytest_dg']}

    # def test_get_data(self):
    #     self.js.update_data('Host', 'pytest_host', 'pytest_iqn')
    #     assert 'pytest_host' in self.js.get_data('Host')

    def test_check_key(self):
        """JsonOperation 类检查某个类型的目标是否存在测试函数"""
        assert self.js.check_key('Host', 'pytest_host')

        assert not self.js.check_key('Host', 'pytest_host0')

    def test_check_value(self):
        """JsonOperation 类检查某个类型的目标资源是否被使用测试函数"""
        assert self.js.check_value('Host', 'pytest_iqn')
        assert not self.js.check_value('Host', 'pytest_iqn_false')
        # self.js.delete_data('Host', 'pytest_host')

    # ------------------   add  ----------------   2020.12.28

    # 具体函数没调用
    # def test_get_map_by_group(self):
    #     """JsonOperation 类根据 hg/dg 读取到使用这个 hg 的所有 map 测试函数"""
    #     assert self.js.get_map_by_group('HostGroup', 'pytest_hg') == ['pytest_map']
    #     assert not self.js.get_map_by_group('HostGroup', 'pytest_hg1')
    #     assert self.js.get_map_by_group('DiskGroup', 'pytest_dg') == ['pytest_map']
    #     assert not self.js.get_map_by_group('DiskGroup', 'pytest_dg1')

    def test_cover_data(self):
        """JsonOperation 类更新该资源的全部数据的测试函数"""
        assert self.js.cover_data('Disk', {'pytest_disk1': 'pytest_path1'}) == {'pytest_disk1': 'pytest_path1'}

    # 无返回值，无输出
    def test_append_member(self):
        """JsonOperation 类某个类别的某个目标添加成员的测试函数"""
        self.js.append_member('HostGroup', 'pytest_map', ['pytest_hg1'], type='Map')
        assert Counter(self.js.json_data['Map']['pytest_map']['HostGroup']) == Counter(['pytest_hg', 'pytest_hg1'])
        self.js.append_member('HostGroup', 'pytest_hg', ['pytest_host3'])
        assert Counter(self.js.json_data['HostGroup']['pytest_hg']) == Counter(
            ['pytest_host1', 'pytest_host2', 'pytest_host3'])

    # 无返回值，无输出
    def test_remove_member(self):
        """JsonOperation 类某个类别的某个目标移除成员的测试函数"""
        self.js.remove_member('HostGroup', 'pytest_map', ['pytest_hg1'], type='Map')
        assert Counter(self.js.json_data['Map']['pytest_map']['HostGroup']) == Counter(['pytest_hg'])
        self.js.remove_member('HostGroup', 'pytest_hg', ['pytest_host3'])
        assert Counter(self.js.json_data['HostGroup']['pytest_hg']) == Counter(['pytest_host1', 'pytest_host2'])

    def test_check_in_res(self):
        """JsonOperation 类检查某个类别的某个目标的成员的测试函数"""
        assert self.js.check_in_res('Map', 'DiskGroup', 'pytest_dg')
        assert not self.js.check_in_res('Map', 'DiskGroup', 'pytest_dg0')
        assert self.js.check_in_res('Map', 'HostGroup', 'pytest_hg')
        assert not self.js.check_in_res('Map', 'DiskGroup', 'pytest_dg0')

    def test_arrange_data(self):
        """JsonOperation 类中对删除了传入的资源之后，处理与之相关的其他资源数据的测试函数"""
        with pytest.raises(TypeError) as exsinfo:
            self.js.arrange_data('host', 'pytest_host')
        assert exsinfo.type == TypeError

    def test_delete_data(self):
        """JsonOperation 类删除数据的测试函数"""
        data_map = self.js.delete_data('Map', 'pytest_map')
        assert 'pytest_map' not in data_map
        data = self.js.delete_data('DiskGroup', 'pytest_dg')
        assert 'pytest_dg' not in data
        data = self.js.delete_data('HostGroup', 'pytest_hg')
        assert 'pytest_hg' not in data
        data = self.js.delete_data('Host', 'pytest_host')
        assert 'pytest_host' not in data


    # 不进行单独测试
    # def test_commit_data(self):
    #     self.js.commit_data()

    # 具体函数没调用
    # def test_get_hg_by_host(self):
    #     # host 存在
    #     assert self.js.get_hg_by_host('pytest_host1') == ['pytest_hg']
    #     # host 不存在
    #     assert not self.js.get_hg_by_host('pytest_host')

    # 具体函数没调用
    # def test_get_disk_by_dg(self):
    #     assert Counter(self.js.get_disk_by_dg(['pytest_dg'])) == Counter(['pytest_disk1', 'pytest_disk2'])
    #     # 不存在抛 KeyError
    #     with pytest.raises(KeyError) as exsinfo:
    #         self.js.get_disk_by_dg(['pytest_dg1', 'pytest_dg3'])
    #     assert exsinfo.type == KeyError

    # def test_get_map_by_host(self):
    #     assert self.js.get_map_by_host('pytest_host1') == ['pytest_map']
    #
    # def test_get_map_by_disk(self):
    #     assert self.js.get_map_by_disk('pytest_disk1') == ['pytest_map']
    #
    # def test_get_iqn_by_disk(self):
    #     self.js.update_data('Host', 'pytest_host1', 'pytest_iqn1')
    #     self.js.update_data('Host', 'pytest_host2', 'pytest_iqn2')
    #
    #     assert Counter(self.js.get_iqn_by_disk('pytest_disk1')) == Counter(['pytest_iqn1', 'pytest_iqn2'])
    #
    # def test_get_dg_by_disk(self):
    #     self.js.update_data('Disk', 'pytest_disk1', 'pytest_path1')
    #     self.js.update_data('Disk', 'pytest_disk2', 'pytest_path2')
    #     assert self.js.get_dg_by_disk('pytest_disk2') == ['pytest_dg']
    #
    # def test_get_disk_by_hg(self):
    #     assert Counter(self.js.get_disk_by_hg('pytest_hg')) == Counter(['pytest_disk1', 'pytest_disk2'])
    #
    # # 无调用
    # def test_get_disk_by_host(self):
    #     assert Counter(self.js.get_disk_by_host('pytest_host1')) == Counter(['pytest_disk1', 'pytest_disk2'])
    #
    # def test_get_iqn_by_map(self):
    #     assert Counter(self.js.get_iqn_by_map('pytest_map')) == Counter(['pytest_iqn1', 'pytest_iqn2'])
    #
    # def test_get_iqn_by_hg(self):
    #     assert Counter(self.js.get_iqn_by_hg(['pytest_hg'])) == Counter(['pytest_iqn1', 'pytest_iqn2'])
    #
    # def test_get_disk_with_iqn(self):
    #     assert Counter(self.js.get_iqn_by_disk('pytest_disk1')) == Counter(['pytest_iqn1', 'pytest_iqn2'])

