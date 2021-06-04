# -*- coding:utf-8 -*-
import subprocess
import os
import re
import yaml
import pprint


def exec_cmd(cmd):
    """subprocess执行命令"""
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if p.returncode == 0:
        result = p.stdout
        result = result.decode() if isinstance(result, bytes) else result
        # print("result", result)
        return {"st": True, "rt": result}
    else:
        print(f"  Failed to execute command: {cmd}")
        print("  Error message:\n", p.stderr)
        return {"st": False, "rt": p.stderr}


class LVMOperation(object):
    def __init__(self):
        pass

    def get_pvs(self):
        cmd = "pvs --noheadings"
        result = exec_cmd(cmd)
        if result["st"]:
            vgs_list = re.findall('(\S+)\s+(\S*)\s+lvm2\s+\S+\s+(\S+)\s+(\S+)\s*?', result["rt"])
            # print(vgs_list)
            return vgs_list

    def get_vgs(self):
        cmd = "vgs --noheadings"
        result = exec_cmd(cmd)
        if result["st"]:
            vgs_list = re.findall('(\S+)\s+(\d+)\s+(\d+)\s+\d+\s+\S+\s+(\S+)\s+(\S+)\s*?', result["rt"])
            # print(vgs_list)
            return vgs_list

    def get_lvs(self):
        cmd = "lvs --noheadings"
        result = exec_cmd(cmd)
        if result["st"]:
            vgs_list = re.findall('(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s(\S*).*\s', result["rt"])
            # pprint.pprint(vgs_list)
            return vgs_list

    def data_processing(self):
        pv_list = self.get_pvs()
        vg_list = self.get_vgs()
        lv_list = self.get_lvs()

        vg_dict = {}
        for vg in vg_list:
            vg_data = {'free size': None, 'total size': None, 'linstor storage pool': {'pool': None}}
            pv_key = f'pvs({vg[1]})'
            lv_key = f'lvs({vg[2]})'
            vg_data['total size'] = vg[3]
            vg_data['free size'] = vg[4]
            vg_data[pv_key] = None
            vg_data[lv_key] = None
            pv_dict = {}
            lv_dict = {}
            for pv in pv_list:
                if pv[1] == vg[0]:
                    pv_dict[pv[0]] = pv[2]
            vg_data[pv_key] = pv_dict

            for lv in lv_list:
                if lv[1] == vg[0] and not lv[4]:
                    lv_dict[lv[0]] = {"size": lv[3]}
            vg_data[lv_key] = lv_dict

            for pool in lv_dict:
                pool_dict = {}
                for lv in lv_list:
                    if lv[4] == pool:
                        pool_dict[lv[0]] = {"size": lv[3]}
                if len(pool_dict) != 0:
                    pool_key = f'lvs({len(pool_dict)})'
                    vg_data[lv_key][pool][pool_key] = pool_dict
            vg_dict[vg[0]] = vg_data
        return vg_dict


class YamlData(object):
    def __init__(self):
        self.yaml_file = 'test.yaml'
        self.yaml_dict = None

    def read_yaml(self):
        """读YAML文件"""
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_dict = yaml.safe_load(f)
            return yaml_dict
        except FileNotFoundError:
            print("Please check the file name:", self.yaml_file)

    def update_yaml(self):
        """更新文件内容"""
        with open("test2.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(self.yaml_dict, f, default_flow_style=False)

    def show(self, dict_vg):
        # dict_vg = self.vg_template(["vg1", "vg2"])
        print(yaml.dump(dict_vg, sort_keys=False))

    def vg_template(self, vg_list):
        vg_dict = {}
        for vg in vg_list:
            vg_data = {'free size': None, 'total size': None, 'linstor storage pool': {'pool': None}, 'pvs': None,
                       'lvs': None}
            vg_dict[vg] = vg_data
        return vg_dict


if __name__ == '__main__':
    # conf.read_yaml()
    lvm_operation = LVMOperation()
    dict_vg = lvm_operation.data_processing()
    lvm_operation.get_vgs()
    lvm_operation.get_pvs()
    lvm_operation.get_lvs()

    conf = YamlData()
    conf.show(dict_vg)
