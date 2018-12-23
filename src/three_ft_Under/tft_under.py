# -*- coding: utf-8 -*-
# Copyright: (C) 2018 Lovac42
# Support: https://github.com/lovac42/3ft_Under
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.0.4


from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, runHook
from anki.utils import intTime
from .config import *

ADDON_NAME='3ft_Under'


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
        qact=QAction("Bury 3ft Under", mw)
        qact.triggered.connect(self.bury)
        menu.addAction(qact)


    def onConfigLoaded(self):
        if self.config.get('auto_bury_on_startup', True):
            self.bury()


    def bury(self):
        use_cid=self.config.get('use_card_creation_time',True)
        scan_days=self.config.get('scan_days',3)
        mod_cutoff=mw.col.sched.dayCutoff-(86400*scan_days)
        if use_cid:
            cid_cutoff=mod_cutoff*1000 #convert to cid time
            sql="id > %d" % cid_cutoff
        else:
            sql="mod > %d" % mod_cutoff

        toBury=mw.col.db.list(
            "select id from cards where type=0 and odid=0 and %s"%sql)

        if toBury:
            rememorize=self.config.get('use_rememorize_to_reschedule',False)
            if rememorize and use_cid: #mod-time may lockup anki for processing
                log=self.config.get('rememorize_log',True)
                min_days=self.config.get('rememorize_min_days',2)
                max_days=self.config.get('rememorize_max_days',7)
                runHook('ReMemorize.rescheduleAll',
                    toBury,min_days,max_days,log)
            else:
                mw.checkpoint(_("Bury 3ft Under"))
                mw.col.db.executemany("""
update cards set queue=-2,mod=%d,usn=%d where id=?"""%
            (intTime(), mw.col.usn()), ([i] for i in toBury))
                mw.col.log(toBury)

            mw.reset() #update view


tfu=ThreeFeetUnder()

