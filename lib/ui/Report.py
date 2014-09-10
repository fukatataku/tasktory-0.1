# -*- encoding:utf-8 -*-

import lib.ui.reports

class Report:

    @staticmethod
    def report_all(*args, **kwargs):
        """lib.ui.reports.*.report()を実行する
        """
        return [(m.__package__.split('.')[-1], m.report(*args, **kwargs))
                for m in lib.ui.reports.__modules__() if 'report' in dir(m)]
