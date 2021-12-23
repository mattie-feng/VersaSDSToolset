import linstordb


# class TestDatabase:
#
#     def setup_class(self):
#         self.db = linstordb.Database()
#
#     def test_free(self):
#         pass
#
#     def test_read(self):
#         pass
#         # assert self.db.read(queries)


class TestLinstorDB:

    def setup_class(self):
        self.ldb = linstordb.LinstorDB()
        self.ldb.build_table('all')

    # 建表，并插入 linstor data 和 lvm data
    def test_build_table(self):
        """测试创建 linstor DB 相关数据库表是否成功"""
        # storagepooltb resourcetb nodetb vgtb thinlvtb 五个表
        # 查询表是否新建成功
        storage_data = self.ldb.fet_one(
            self.ldb.cur.execute(
                "SELECT COUNT(*) FROM sqlite_master where type='table' and (name='storagepooltb' or name ='resourcetb' or name='nodetb' or name='vgtb' or name='thinlvtb')"))
        assert storage_data[0] == 5

    # build_table中调用，该函数不传参直接调用 lvm 里的函数读取数据并插入
    # def test_insert_lvm_data(self):
    #     pass

    # build_table中调用，该函数不传参直接调用 linstor 里的函数读取数据并插入
    def test_insert_linstor_data(self):
        """直接调用 linstor 里的函数读取数据并插入"""
        nodetb_data = self.ldb.fet_one(self.ldb.cur.execute("SELECT * FROM nodetb"))
        assert len(nodetb_data) > 0

    def test_insert_data(self):
        """数据库插入数据"""
        idata = [('pytest', 'COMBINED', '10.203.1.111:3366(PLAIN)', 'Online')]
        sql = '''insert into nodetb(Node,NodeType,Addresses,State)values(?,?,?,?)'''
        self.ldb.insert_data(sql, idata, 'nodetb')
        nodetb_data = self.ldb.fet_all(self.ldb.cur.execute("SELECT * FROM nodetb"))
        judge = 0
        for i in nodetb_data:
            if 'pytest' in i:
                judge = 1
            else:
                pass
        assert judge == 1


class TestCollectData:

    def setup_method(self):
        self.cd = linstordb.CollectData()
        node_data = [('pytest', 'COMBINED', '10.203.1.111:3366(PLAIN)', 'Online')]
        sql1 = '''insert into nodetb(Node,NodeType,Addresses,State)values(?,?,?,?)'''
        self.cd.insert_data(sql1, node_data, 'nodetb')
        res_data = [('pytest', 'test_res1', 'pytest_sp1', 100, 1100, '/dev/drbd1100', '12 MiB', 'Unused', 'UpToDate')]
        sql2 = '''insert into resourcetb(Node, Resource, StoragePool, VolumeNr, MinorNr, DeviceName, Allocated, InUse, State)values(?,?,?,?,?,?,?,?,?)'''
        self.cd.insert_data(sql2, res_data, 'resourcetb')
        sp_data = [('test_sp1', 'pytest', 'LVM', '', '4.93GiB', '10.00GiB', 'False', 'Ok')]
        sql3 = '''insert into storagepooltb(StoragePool, Node, Driver, PoolName, FreeCapacity, TotalCapacity, SupportsSnapshots, State)values(?,?,?,?,?,?,?,?)'''
        self.cd.insert_data(sql3, sp_data, 'storagepooltb')

    def test_get_resource(self):
        """获取资源格式处理后的数据"""
        assert len(self.cd._get_resource()) >= 1

    def test_get_all_node(self):
        """获取全部 node 格式处理后的数据"""
        assert self.cd.get_all_node() is not None

    def test_get_node_info(self):
        """获取 node 信息格式处理后的数据"""
        assert 'pytest' in self.cd.get_node_info('pytest')

    def test_get_one_node(self):
        """获取单个 node 格式处理后的数据"""
        assert 'pytest_sp1' in self.cd.get_one_node('pytest')[0]

    def test_get_sp_in_node(self):
        """获取 storagepool 在 node 格式处理后的数据"""
        assert 'pytest' in self.cd.get_sp_in_node('pytest')[0]

    def test_get_all_res(self):
        """获取全部 res 格式处理后的数据"""
        assert self.cd.get_all_res() is not None

    def test_get_res_info(self):
        """获取 res 信息处理后的数据"""
        assert 'test_res1' in self.cd.get_res_info('test_res1')

    def test_get_one_res(self):
        """获取单个 res 格式处理后的数据"""
        assert self.cd.get_one_res('test_res1') == [['pytest', 'pytest_sp1', 'secondary', 'UpToDate']]

    def test_get_all_sp(self):
        """获取全部 storagepool 格式处理后的数据"""
        assert self.cd.get_all_sp() is not None

    def test_get_sp_info(self):
        """获取 storagepool 信息格式处理后的数据"""
        assert 'test_sp1' in self.cd.get_sp_info('test_sp1')

    def test_get_one_sp(self):
        """获取单个 storagepool 格式处理后的数据"""
        assert self.cd.get_one_sp('pytest_sp1') is not None
