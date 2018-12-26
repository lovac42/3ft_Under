# -*- coding: utf-8 -*-
# Copyright: (C) 2018 Lovac42
# Support: https://github.com/lovac42/3ft_Under
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Version: 0.0.6


import random
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
        qact.triggered.connect(self.checkStats)
        menu.addAction(qact)


    def onConfigLoaded(self):
        if self.config.get('auto_bury_on_startup', True):
            self.checkStats()


    def checkStats(self):
        use_mod=self.config.get('use_modification_time',False)
        scan_days=self.config.get('scan_days',3)
        mod_cutoff=mw.col.sched.dayCutoff-(86400*scan_days)
        if use_mod:
            sql="mod > %d" % mod_cutoff
        else:
            cid_cutoff=mod_cutoff*1000 #convert to cid time
            sql="id > %d" % cid_cutoff

        newCards=mw.col.db.list("""
select id from cards where type=0 and 
queue=0 and odid=0 and %s"""%sql)

        if newCards:
            remDict=self.config.get('rememorize')
            rememorize=remDict.get('reschedule_with_rememorize',False)
            if rememorize:
                self.toReMemorize(newCards)
            else:
                self.toBury(newCards)
            mw.reset() #update view


    def toBury(self, cids):
        mw.checkpoint(_("Bury 3ft Under"))
        mw.col.db.executemany("""
update cards set queue=-2,mod=%d,usn=%d where id=?"""%
            (intTime(), mw.col.usn()), ([i] for i in cids))
        mw.col.log(cids)


    def toReMemorize(self, cids):
        remDict=self.config.get('rememorize')
        min_days=remDict.get('min_days',2)
        max_days=remDict.get('max_days',7)
        change_ivl=remDict.get('change_ivl',True)

        mw.moveToState("deckBrowser")
        if change_ivl:
            log=remDict.get('log',True)
            runHook('ReMemorize.rescheduleAll',
                    cids,min_days,max_days,log)
        else:
            mw.checkpoint(_("Reschedule"))
            mw.progress.start()
            for cid in cids:
                card=mw.col.getCard(cid)
                due=random.randint(min_days,max_days)
                runHook('ReMemorize.changeDue',card,due)
            mw.progress.finish()
        mw.autosave()


tfu=ThreeFeetUnder()

