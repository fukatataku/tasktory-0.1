#!C:/python/python3.4/python
# -*- encoding:utf-8 -*-

import os, datetime, configparser
from multiprocessing import Process, Pipe

import win32api

from lib.core.Tasktory import Tasktory
from lib.core.Manager import Manager
from lib.ui.Journal import Journal
from lib.ui.Report import Report
from lib.ui.TrayIcon import TrayIcon
from lib.monitor.monitor import file_monitor, dir_monitor
from lib.common.RWTemplate import RWTemplate
from lib.common.exceptions import *
from lib.common.common import *

class WinMain:

    BLOCK = 0
    UNBLOCK = 1
    QUIT = 2

    def __init__(self):
        # 日付
        self.today = datetime.date.today()

        # メイン設定読み込み
        self.main_config()

        # システム初期化
        self.initialize()

        # 準備
        self.prepare()

        # トレイアイコンのポップアップメニュー作成
        self.prepare_command()

        # サブプロセス準備
        self.prepare_process()
        return

    def __del__(self):
        return

    def main_config(self):
        config = configparser.ConfigParser()
        config.read(MAIN_CONF_FILE, encoding='utf-8-sig')
        self.root = config['MAIN']['ROOT']
        self.profile_name = config['MAIN']['PROFILE_NAME']
        self.journal_file = config['JOURNAL']['JOURNAL_FILE']
        self.infinite = int(config['JOURNAL']['INFINITE'])
        self.report_dir = config['REPORT']['REPORT_DIR']
        self.report_name_tmpl = RWTemplate(config['REPORT']['REPORT_NAME'])
        return

    def initialize(self):
        # ルートディレクトリが存在しなければ、作成する
        if not os.path.isfile(os.path.join(self.root, self.profile_name)):
            Manager.put(
                    self.root,
                    Tasktory('', self.today.toordinal() + 3650),
                    self.profile_name)

        # ジャーナルディレクトリが存在しなければ、作成する
        journal_dir = os.path.dirname(self.journal_file)
        if not os.path.isdir(journal_dir):
            os.makedirs(journal_dir)

        return

    def prepare(self):
        # ジャーナルが存在するなら、memoを取り出す
        memo = ''
        if os.path.isfile(self.journal_file):
            _, memo = self.read_journal()

        # ファイルシステムからツリーを読み込む
        tree = Manager.get_tree(self.root, self.profile_name)

        # 新しいジャーナルを書き出す
        self.write_journal(tree, memo)

        # 新しいジャーナルを読み込む
        self.jtree, self.memo = self.read_journal()

        # ファイルシステムの状態を読み込む
        self.paths = Manager.listtask(self.root, self.profile_name)

        return

    def prepare_command(self):
        # メニューコマンドを作成する
        def num():
            n = 0
            while True:
                yield n
                n += 1
            return
        gen = num()
        self.com_map = {}
        self.com_menu = []

        # 同期コマンド
        iD = next(gen)
        self.com_map[iD] = self.sync
        self.com_menu.append(('Sync', iD))

        # レポートコマンド
        sub_menu = []
        iD = next(gen)
        reports = Report.reports()
        self.com_map[iD] = lambda: self.write_report(reports)
        sub_menu.append(('All', iD))
        for name, func in reports:
            iD = next(gen)
            self.com_map[iD] = lambda: self.write_report([(name, func)])
            sub_menu.append((name, iD))
        self.com_menu.append(('Report', sub_menu))

        # セパレータ
        self.com_menu.append((None, None))

        # 終了コマンド
        iD = next(gen)
        self.com_map[iD] = self.quit
        self.com_menu.append(('Quit', iD))

        return

    def prepare_process(self):
        # パイプ
        self.conn = Pipe()

        # トレイアイコン作成／開始
        self.tray_icon = Process(target=TrayIcon,
                args=(self.conn[1], ICON_PATH, POPMSG_MAP, self.com_menu))

        # 監視プロセス作成
        self.jnl_monitor = Process(
                target=file_monitor, args=(self.journal_file, self.conn[1]))
        self.fs_monitor = Process(
                target=dir_monitor, args=(self.root, self.conn[1]))

        return

    def run(self):
        # プロセス開始
        self.tray_icon.start()
        self.hwnd = self.conn[0].recv()[1]
        self.jnl_monitor.start()
        self.fs_monitor.start()

        try:
            ignore = WinMain.UNBLOCK
            while True:
                # 通知が来るまでブロック
                ret = self.conn[0].recv()

                #==============================================================
                # 自身による通知
                #==============================================================
                if ret[0] == os.getpid():
                    if ret[1] == WinMain.BLOCK:
                        ignore = WinMain.BLOCK
                        continue
                    elif ret[1] == WinMain.UNBLOCK:
                        ignore == WinMain.UNBLOCK
                        continue
                    elif ret[1] == WinMain.QUIT:
                        break

                # 自分自身による更新は無視する
                elif ignore == WinMain.BLOCK:
                    continue

                #==============================================================
                # ジャーナルが更新された場合の処理
                #==============================================================
                if ret[0] == self.jnl_monitor.pid:
                    self.block()
                    try:
                        self.update_filesystem()
                    finally:
                        self.unblock()

                #==============================================================
                # ファイルシステムが更新された場合の処理
                #==============================================================
                elif ret[0] == self.fs_monitor.pid:
                    self.block()
                    try:
                        self.update_journal()
                    finally:
                        self.unblock()

                #==============================================================
                # トレイアイコンからコマンドが実行された場合の処理
                #==============================================================
                elif ret[0] == self.tray_icon.pid:
                    self.com_map[ret[1]]()
        finally:
            win32api.SendMessage(self.hwnd, TrayIcon.MSG_DESTROY, None, None)
            self.tray_icon.terminate()
            self.jnl_monitor.terminate()
            self.fs_monitor.terminate()
            for conn in self.conn: conn.close()
        return

    def read_journal(self):
        # ジャーナル読み込み用のコンフィグを読み込む
        with open(JOURNAL_READ_TMPL_FILE, 'r', encoding='utf-8-sig') as f:
            journal_tmpl = RWTemplate(f.read())
        config = configparser.ConfigParser()
        config.read(JOURNAL_CONF_FILE, encoding='utf-8-sig')
        section = config['ReadTemplate']
        taskline_tmpl = RWTemplate(section['TASKLINE'])
        date_reg = Journal.date_regex(section['DATE'])
        time_reg = Journal.time_regex(section['TIME'])
        times_delim = section['TIMES_DELIM']

        # ファイルからジャーナルテキストを読み込む
        with open(self.journal_file, 'r', encoding='utf-8-sig') as f:
            journal = f.read()

        # ジャーナルからタスクトリリストを作成する
        tasktories, memo = Journal.tasktories(
                journal, journal_tmpl, taskline_tmpl,
                date_reg, time_reg, times_delim)

        # 同じタスクトリが複数存在する場合は例外を送出する
        paths = [Journal.foot(t).path() for t in tasktories]
        if len(paths) != len(set(paths)):
            raise JournalDuplicateTasktoryException()

        # タスクトリリストを統合してツリーにする
        jtree = sum(tasktories[1:], tasktories[0]) if tasktories else None

        # ツリーを診断する
        if jtree is not None and Manager.overlap(jtree):
            raise JournalOverlapTimetableException()

        return jtree, memo

    def write_journal(self, tree, memo):
        # ジャーナル書き出し用のコンフィグを読み込む
        with open(JOURNAL_WRITE_TMPL_FILE, 'r', encoding='utf-8-sig') as f:
            journal_tmpl = RWTemplate(f.read())
        config = configparser.ConfigParser()
        config.read(JOURNAL_CONF_FILE, encoding='utf-8-sig')
        section = config['WriteTemplate']
        taskline_tmpl = RWTemplate(section['TASKLINE'])
        date_tmpl = RWTemplate(section['DATE'])
        time_tmpl = RWTemplate(section['TIME'])
        times_delim = section['TIMES_DELIM']

        # ツリーからジャーナルテキストを作成する
        journal = Journal.journal(
                self.today, tree, memo, journal_tmpl, taskline_tmpl,
                time_tmpl, times_delim, self.infinite)

        # ジャーナルテキストをファイルに書き出す
        with open(self.journal_file, 'w', encoding='utf-8') as f:
            f.write(journal)

        # ジャーナル書き出し設定を読み込み設定にセットする
        with open(JOURNAL_READ_TMPL_FILE, 'w', encoding='utf-8') as f:
            f.write(journal_tmpl.template)
        section = config['ReadTemplate']
        section['TASKLINE'] = taskline_tmpl.template.replace('%', '%%')
        section['DATE'] = date_tmpl.template.replace('%', '%%')
        section['TIME'] = time_tmpl.template.replace('%', '%%')
        section['TIMES_DELIM'] = times_delim
        with open(JOURNAL_CONF_FILE, 'w', encoding='utf-8') as f:
            config.write(f)

        return

    def write_report(self, reports):
        # レポート書き出し開始を通知する
        self.message(INFO_REPO_START)

        # ファイルシステムからタスクツリーを読み込む
        tree = Manager.get_tree(self.root, self.profile_name)

        for name, func in reports:
            # レポートテキストを作成する
            repo_text = func(self.today, tree)

            # レポートファイルパスを作成する
            repo_filename = self.report_name_tmpl.substitute({
                'YEAR' : str(self.today.year),
                'MONTH' : str(self.today.month),
                'DAY' : str(self.today.day),
                })
            repo_file = os.path.join(self.report_dir, name, repo_filename)

            # ディレクトリが無ければ作成する
            if not os.path.isdir(os.path.join(self.report_dir, name)):
                os.makedirs(os.path.join(self.report_dir, name))

            # ファイルに書き出す
            with open(repo_file, 'w', encoding='utf-8') as f:
                f.write(repo_text)

        # レポート書き出し完了を通知する
        self.message(INFO_REPO_END)
        return

    def update_filesystem(self):
        # ジャーナルを読み込む
        new_jtree, new_memo = self.read_journal()

        # タスクの状態に変化が無ければ無視する
        if Manager.same_tree(self.jtree, new_jtree):
            return

        # ファイルシステムからツリーを読み出す
        tree = Manager.get_tree(self.root, self.profile_name)

        # 読み出したツリーの内、更新対象タスクの当日の作業時間を抹消する
        start = datetime.datetime.combine(self.today, datetime.time())
        end = start + datetime.timedelta(1)
        start = int(start.timestamp())
        end = int(end.timestamp())
        for node in [tree.find(n.path()) for n in new_jtree]:
            if node is None: continue
            node.timetable = [t for t in node.timetable\
                    if not (start <= t[0] < end)]

        # マージする
        new_tree = tree + new_jtree

        # 作業時間の重複の有無を確認する（非必須）
        if Manager.overlap(new_tree):
            pass

        # 未設定期日を補完する
        for node in new_tree:
            if node.deadline is None:
                node.deadline = max([n.deadline for n in node
                    if n.deadline is not None])

        # ファイルシステムへの書き出し開始を通知する
        self.message(INFO_FS_START)

        # ファイルシステムに書き出す
        for node in new_tree:
            Manager.put(self.root, node, self.profile_name)

        # ファイルシステムへの書き出し完了を通知する
        self.message(INFO_FS_END)

        # メンバ変数にセットする
        self.jtree = new_jtree
        self.memo = new_memo
        return

    def update_journal(self):
        # 現在のファイルシステムの状態を読み込む
        new_paths = Manager.listtask(self.root, self.profile_name)

        # ファイルシステムの状態に変化が無ければ無視する
        if org_paths == new_paths:
            return

        # ファイルシステムからツリーを読み込む
        tree = Manager.get_tree(self.root, self.profile_name)

        # ジャーナルへの書き出し開始を通知する
        self.message(INFO_JNL_START)

        # ジャーナルに書き出す
        self.write_journal(tree, self.memo)

        # ジャーナルへの書き出し完了を通知する
        self.message(INFO_JNL_END)

        # メンバ変数にセットする
        self.paths = new_paths

        return

    def message(self, msg):
        win32api.SendMessage(self.hwnd, TrayIcon.MSG_POPUP, msg, None)
        return

    def block(self):
        self.conn[1].send((os.getpid(), WinMain.BLOCK))
        return

    def unblock(self):
        self.conn[1].send((os.getpid(), WinMain.UNBLOCK))
        return

    def quit(self):
        self.conn[1].send((os.getpid(), WinMain.QUIT))
        return

    def sync(self):
        return

if __name__ == '__main__':
    main = WinMain()
    main.run()
    del main
