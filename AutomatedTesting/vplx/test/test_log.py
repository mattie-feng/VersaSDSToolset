import log


class TestLog:

    def setup_class(self):
        # self.log = log.Log('test', '1603872339')
        self.log = log.Log()

    # 返回一个 MyLoggerAdapter 对象
    # def test_logger_input(self):
    #     assert self.log.logger_input() is not None

    # 无返回值，日志开关变量为'no'时不做日志记录
    def test_write_to_log(self):
        """将 debug 信息写入 log file"""
        assert self.log.write_to_log('t1','t2','d1','d2','data') is None
