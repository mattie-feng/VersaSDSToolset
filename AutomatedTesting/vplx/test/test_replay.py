from unittest.mock import patch

import replay
import consts

# 检查文件是否存在，存在返回True，否则返回False
from commands import ReplayCommands
from vtel import MyArgumentParser, VtelCLI


def test_isFileExists():
    """检查文件是否存在，测试用例包括文件存/文件不存在"""
    # 存在a
    assert replay.isFileExists('replay.py')
    # 不存在
    assert not replay.isFileExists('XXXX.py')


def test_read_log_files():
    """测试能否成功读取 log 文件"中的数据"""
    # 读取成功则不为空字符
    assert replay._read_log_files()
    # 读取失败


def test_get_log_files():
    """ 测试是否能成功获取 log 文件"""
    # 获取成功则不为空列表
    assert replay._get_log_files('logDB.db')
    # 获取失败


class TestLogDB:

    def setup_class(self):
        self.log = replay.LogDB()
        self.tid = '1603872339'

    def test_drop_table(self):
        """删除 logtable 数据库表"""
        sql = 'select count(*) from sqlite_master where type="table" and name = "logtable"'
        self.log._drop_table()
        assert self.log.cur.execute(sql).fetchone()[0] == 0

    def test_create_table(self):
        """创建 logtable 数据库表"""
        sql = 'select count(*) from sqlite_master where type="table" and name = "logtable"'
        self.log._create_table()
        assert self.log.cur.execute(sql).fetchone()[0] == 1

    def test_insert_data(self):
        """数据库插入数据"""
        # data = ('2020/10/28 16:05:39', self.tid, 'test', 'DATA', 'STR', 'cmd_input', '', '8033629173')
        data = ('2020/10/28 16:05:39', self.tid, 'test', 'DATA', 'STR', 'cmd_input', '6311017008',
                "{'valid': '1', 'cmd': 'stor -h'}")
        self.log.insert_data(data)
        sql = f'SELECT data FROM logtable'
        getdata = self.log.sql_fetch_one(sql)
        assert eval(getdata) == {'cmd': 'stor -h', 'valid': '1'}

    def test_sql_fetch_one(self):
        """获取单一列数据"""
        sql = f'SELECT * FROM logtable'
        assert self.log.sql_fetch_one(sql) is not None

    def test_sql_fetch_all(self):
        """获取满足条件的全部数据列"""
        sql = f'SELECT * FROM logtable'
        # sql = f"SELECT data, describe1 FROM logtable WHERE transaction_id='1603872339'"
        assert self.log.sql_fetch_all(sql) is not None

    def test_get_oprt_result(self):
        """根据 oprt_id 获取 type1为 DATA 的 result"""
        replay.LogDB.oprt_id = '6311017008'
        assert self.log.get_oprt_result() == {'result': "{'valid': '1', 'cmd': 'stor -h'}",
                                              'time': '2020/10/28 16:05:39'}
        replay.LogDB.oprt_id = '123456'
        assert self.log.get_oprt_result() == {'time': '', 'result': ''}
        replay.LogDB.oprt_id = ''
        assert self.log.get_oprt_result() == {'time': '', 'result': ''}

    def test_get_id(self):
        """根据tid,describe1获取对应的time，db_id，opt_id"""
        # data = ('2020/10/28 16:05:39', self.tid, 'test', 'DATA', 'STR', 'cmd_input', '6311017008',
        #         "{'valid': '1', 'cmd': 'stor -h'}")
        # self.log.insert_data(data)
        replay.LogDB.id_pointer = 0
        replay.LogDB.transaction_id = '1603872339'
        assert self.log.get_id('cmd_input') == {'db_id': 1, 'oprt_id': "{'valid': '1', 'cmd': 'stor -h'}",
                                                'time': '2020/10/28 16:05:39'}
        replay.LogDB.transaction_id = '12234566'
        assert self.log.get_id('cmd_input') == {'time': '', 'db_id': '', 'oprt_id': ''}

    def test_get_cmd_via_tid(self):
        """通过 tid 获取用户操作"""
        replay.LogDB.transaction_id = '1603872339'
        assert self.log.get_cmd_via_tid() == {'cmd': 'stor -h', 'tid': '1603872339', 'valid': '1'}

    def test_get_cmd_via_time(self):
        """通过时间段获取用户操作"""
        star_time = '2020/10/1 10:00:00'
        end_time = '2020/11/1 17:00:00'
        assert self.log.get_cmd_via_time(star_time, end_time) == [
            {'cmd': 'stor -h', 'tid': '1603872339', 'valid': '1'}]

    def test_get_anwser(self):
        """根据tid获取对应的time，answer"""
        data = ('2020/01/28 16:05:39', '1603872111', 'test', 'DATA', 'STR', 'confirm deletion', 'confirm deletion',
                "{'valid': '1', 'cmd': 'stor -h'}")
        self.log.insert_data(data)
        self.log.transaction_id = '1603872111'
        assert self.log.get_anwser() == ('2020/01/28 16:05:39', "{'valid': '1', 'cmd': 'stor -h'}")
        self.log.transaction_id = '1234567'
        assert self.log.get_anwser() == ('', '')

    def test_get_cmd_output(self):
        """根据tid获取对应的time，db_id,output"""
        data = ('2020/01/29 16:05:39', '1603872222', 'test', 'INFO', 'STR', 'output', 'output',
                "{'valid': '1', 'cmd': 'stor -h'}")
        self.log.insert_data(data)
        self.log.transaction_id = '1603872222'
        assert self.log.get_cmd_output() == {'time': '2020/01/29 16:05:39', 'db_id': 3,
                                             'output': "{'valid': '1', 'cmd': 'stor -h'}"}
        self.log.transaction_id = '12345678'
        assert self.log.get_cmd_output() == {'time': '', 'db_id': '', 'output': ''}
        # assert self.log.get_cmd_output('1603872222') == ('2020/01/29 16:05:39', "{'valid': '1', 'cmd': 'stor -h'}")

    def test_get_all_cmd(self):
        """获取全部类型为 cmd_input 的数据"""
        assert self.log.get_all_cmd() is not None


class TestReplay:

    def setup_class(self):
        self.rpl = replay.Replay()
        self.log = replay.LogDB()
        data = ('2020/10/28 16:05:39', '1603872339', 'test', 'DATA', 'INPUT', 'cmd_input',
                '[/home/samba/celia/VersaTEL-dev/Orion/vplx]',
                "{'valid': '0', 'cmd': 'iscsi d s'}")
        self.log.insert_data(data)

    def test_make_table(self):
        """将replay 数据整理成表格的测试函数"""
        list_data = [['test_time', 'test_opt', 'test_return']]
        assert self.rpl.make_table("", [])._rows == []
        assert self.rpl.make_table("", list_data)._rows == [['test_time', 'test_opt', 'test_return']]

    # test_replay_execute 函数中包含该函数测试
    # def test_replay_lite(self):
    #     """测试 lite 模式下 replay 功能"""
    #     # 备注由于while 里面含有 input 而且 input内容作为 while 循环的判断条件暂时未找到数据隔离方法，需要使用-s操作
    #     assert self.rpl.replay_lite() is None

    def test_replay_single(self):
        """测试单独 replay 一条命令，测试用例包括：正常执行/执行命令为空/执行命令 valid 不等于0"""
        parser = VtelCLI().parser
        rpl_cmd = ReplayCommands(parser)
        dict_cmd = {'tid': '1603872339', 'valid': '0', 'cmd': 'iscsi d s'}
        dict_cmd_error = {'tid': '1603872339', 'valid': '1', 'cmd': 'test_cmd'}
        # 正常 replay 命令
        assert self.rpl.replay_single(rpl_cmd.parser, dict_cmd) is None
        # replay 命令为空
        with patch('builtins.print') as terminal_print:
            self.rpl.replay_single(rpl_cmd.parser, {})
            terminal_print.assert_called_with('There is no command to replay')
        # replay 命令 valid != 0
        with patch('builtins.print') as terminal_print:
            self.rpl.replay_single(rpl_cmd.parser, dict_cmd_error)
            terminal_print.assert_called_with('Command error: test_cmd , and cannot be executed')

    def test_replay_execute(self, mocker, monkeypatch):
        """测试 replay 功能，测试用例包括：tid 不为空 ，tid 为空但时间段不为空，tid 为空时间段参数只有一个"""
        # 备注由于while 里面含有 input 而且 input内容作为 while 循环的判断条件暂时未找到数据隔离方法，需要使用-s操作
        parser = VtelCLI().parser
        rpl_cmd = ReplayCommands(parser)
        star_time = '2020/10/1 10:00:00'
        end_time = '2020/11/1 17:00:00'
        # transation_id 不为空
        print('transation_id 不为空,直接调用 replay_single 函数无输入')
        assert self.rpl.replay_execute(rpl_cmd.parser, '1603872339') is None
        # transation_id 为空，但是 start_time 和 end_time 不为空
        print(
            'transation_id 不为空但start_time 和 end_time 不为空,输入： -l -> 1 -> 2 -> 3 -> ls -> all -> -l -> -n -> 1 -> ls -> all -> exit')
        assert self.rpl.replay_execute(rpl_cmd.parser, None, star_time, end_time) is None
        # 其他情况
        # 数据隔离，模拟设置logdb.get_all_cmd函数的返回值
        mocker.patch.object(replay.LogDB, 'get_all_cmd', return_value=[])
        assert self.rpl.replay_execute(rpl_cmd.parser) is None
        monkeypatch.setattr('builtins.input', lambda: "exit")
        assert self.rpl.replay_execute(rpl_cmd.parser, None, star_time) is None
        # 这种情况不存在，argparser的解析器读取参数时，若参数只有一个则为 star_time
        # assert self.rpl.replay_execute(rpl_cmd.parser, None, None, end_time) is None

    # def test_replay_execute_ls(self, monkeypatch):
    #     parser = VtelCLI().parser
    #     rpl_cmd = ReplayCommands(parser)
    #     star_time = '2020/10/1 10:00:00'
    #     end_time = '2020/11/1 17:00:00'
    #     # replay.input = lambda: 'ls'
    #     # with mocker.patch.object(__builtins__, 'input', lambda: 'ls'):
    #     assert self.rpl.replay_execute(rpl_cmd.parser, None, star_time, end_time) is None
    #     # monkeypatch.setattr('builtins.input', lambda: "exit")
    #
    #     # mocker.patch.object(replay.LogDB, 'get_all_cmd', return_value=[])
    #     # assert self.rpl.replay_execute(rpl_cmd.parser) is None

    def test_collapse_data(self):
        """测试折叠数据功能，调用该函数"""
        self.rpl.collapse_data()

    # def test_reset_data(self):
    #     assert False
