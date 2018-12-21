# -*- coding: utf-8 -*-
# Copyright: (C) 2018 Lovac42
# Support: https://github.com/lovac42/3FT_Under
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.0.1


from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, runHook
from anki.utils import intTime
from .config import *

ADDON_NAME='three_ft_Under'


class ThreeFeetUnder:
    def __init__(self):
        self.config=Config(ADDON_NAME)
        addHook(ADDON_NAME+'.configLoaded', self.onConfigLoaded)
        self.setupMenu()


    def setupMenu(self):
        menu=None
        for a in mw.form.menubar.actions():
            if '&Study' == a.text():
                menu=a.menu()
                # menu.addSeparator()
                break
        if not menu:
            menu=mw.form.menubar.addMenu('&Study')
        qact=QAction("Bury 3FT Under", mw)
        qact.triggered.connect(self.bury)
        menu.addAction(qact)


    def onConfigLoaded(self):
        if self.config.get('auto_bury_on_startup', True):
            self.bury()


    def bury(self):
        scan_days=self.config.get('scan_days',3)
        cutoff=mw.col.sched.dayCutoff-(86400*scan_days)
        cutoff*=1000 #convert to cid time

        toBury=mw.col.db.list(
            "select id from cards where odid=0 and id > ?", cutoff)

        if toBury:
            rememorize=self.config.get('use_rememorize_to_reschedule',False)
            if rememorize:
                log=self.config.get('rememorize_log',True)
                min_days=self.config.get('rememorize_min_days',2)
                max_days=self.config.get('rememorize_max_days',7)
                runHook('ReMemorize.rescheduleAll',
                    toBury,min_days,max_days,log)
            else:
                mw.col.db.executemany("""
update cards set queue=-2,mod=%d,usn=%d where id=?"""%
            (intTime(), mw.col.usn()), ([i] for i in toBury))
                mw.col.log(toBury)

            mw.reset() #update view


tfu=ThreeFeetUnder()

