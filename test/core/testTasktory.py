#!python3
#-*- encoding:utf-8 -*-

import sys, os, datetime, unittest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', '..'))
sys.path.append(HOME_DIR)

from lib.core.Tasktory import Tasktory

OPEN = Tasktory.OPEN
WAIT = Tasktory.WAIT
CLOSE = Tasktory.CLOSE
CONST = Tasktory.CONST

class TestTasktory(unittest.TestCase):

    def check(self, task, ID, name, deadline, status, parent, comments):
        self.assertEqual(task.ID, ID)
        self.assertEqual(task.name, name)
        self.assertEqual(task.deadline, deadline)
        self.assertEqual(task.status, status)
        self.assertIs(task.parent, parent)
        self.assertIs(task.comments, comments)
        return

    def check_child(self, task, *children):
        self.assertListEqual(
                sorted(task.children, key=lambda t:t.ID),
                sorted(children, key=lambda t:t.ID)
                )
        return

    def check_time(self, task, *timetable):
        self.assertListEqual(
                sorted(task.timetable, key=lambda t:t[0]),
                sorted(timetable, key=lambda t:t[0])
                )
        return

    @classmethod
    def setUpClass(cls):
        return

    @classmethod
    def tearDownClass(cls):
        return

    def setUp(self):
        # ID : 0, 1
        # name : '', '#123.Hoge', 'ほげ'
        # deadlinee : 0, 1
        # timetable : [], [(0,1)], [(1,2)], [(0,1),(1,2)]
        # status : OPNE, WAIT, CLOSE, CONST
        # parent : None, t
        # children : [], [t], [t, t], [t[t]], [t[t, t], t[t, t]]
        # comments : '', 'HOGEHOGE', 'あいうえお'
        return

    def tearDown(self):
        return

    #==========================================================================
    # コンストラクタ
    #==========================================================================
    def test_init(self):
        return

    #==========================================================================
    # 比較／テスト
    #==========================================================================
    def test_lt(self):
        # TODO
        return

    def test_le(self):
        # TODO
        return

    def test_eq(self):
        # TODO
        return

    def test_ne(self):
        # TODO
        return

    def test_gt(self):
        # TODO
        return

    def test_ge(self):
        # TODO
        return

    def test_bool(self):
        return

    #==========================================================================
    # コンテナエミュレート
    #==========================================================================
    def test_len(self):
        # TODO
        return

    def test_getitem(self):
        # TODO
        return

    def test_setitem(self):
        # TODO
        return

    def test_iter(self):
        # TODO
        return

    def test_contains(self):
        # TODO
        return

    #==========================================================================
    # 数値型エミュレート
    #==========================================================================
    def test_add(self):
        # TODO
        return

    #==========================================================================
    # タスクトリデータ参照メソッド
    #==========================================================================
    def test_timetable_of_tree(self):
        # TODO
        return

    def test_total_time(self):
        # TODO
        return

    def test_total_time_of_tree(self):
        # TODO
        return

    def test_first_timestamp(self):
        # TODO
        return

    def test_last_timestamp(self):
        # TODO
        return

    #==========================================================================
    # タスクトリデータ変更メソッド
    #==========================================================================
    def test_add_time(self):
        # TODO
        return

    def test_append(self):
        # TODO
        return

    #==========================================================================
    # 抽象データ参照メソッド
    #==========================================================================
    def test_get(self):
        # TODO
        return

    def test_path(self):
        # TODO
        return

    def test_level(self):
        # TODO
        return

    def test_copy(self):
        # TODO
        return

    def test_copy_of_tree(self):
        # TODO
        return

    def test_clip(self):
        # TODO
        return

    #==========================================================================
    # 抽象データ変更メソッド
    #==========================================================================
    def test_commit(self):
        # TODO
        return

    def test_jack(self):
        # TODO
        return

if __name__ == '__main__':
    print(datetime.datetime.now())
    unittest.main()
