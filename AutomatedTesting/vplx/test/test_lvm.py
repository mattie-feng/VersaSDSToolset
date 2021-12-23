from execute import lvm

class TestLVM:

    def setup_class(self):
        self.l = lvm.LVM()

    # vg /throw exception
    def test_get_vg(self):
        """获取 vg 信息"""
        assert 'VG' in self.l.get_vg()

    # None/thinlv
    def test_get_thinlv(self):
        """获取 thinlv 信息"""
        assert 'LV' in self.l.get_thinlv()

    # []/list_thinlv
    def test_refine_thinlv(self):
        """格式处理 thinlv 资源信息"""
        assert self.l.refine_thinlv() is not None

    # list_vg/[]
    def test_refine_vg(self):
        """格式处理 vg 资源信息"""
        assert self.l.refine_vg() is not None

    # True / None
    def test_is_vg_exists(self):
        """判断该 vg 是否存在，测试用例包括：vg存在/vg不存在"""
        # 不存在
        assert self.l.is_vg_exists('drbdpool2') is None
        # 存在
        assert self.l.is_vg_exists('drbdpool')

    # True / None
    def test_is_thinlv_exists(self):
        """判断该 thinlv 是否存在(参数thinlv的正常格式：vg_name/thinlv_name)，测试用例包括：thinlv存在/thinlv不存在"""
        # 不存在
        assert self.l.is_thinlv_exists('drbdpool2/thinlv_test') is None
        # 存在
        assert self.l.is_thinlv_exists('drbdpool/thinlv_test')