#!/usr/bin/env python

# Code implementation generated from reading ui file 'ui/LoopsPlots.ui'
#
# Created: Thu Jul 10 11:55:08 2014 
#      by: Taurus UI code generator 3.2.0
#
# WARNING! All changes made in this file will be lost!

__docformat__ = 'restructuredtext'

import sys
import PyQt4.Qt as Qt
from ui_LoopsPlots import Ui_Loops
from taurus.qt.qtgui.panel import TaurusWidget

class Loops(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)
        
        self._ui = Ui_Loops()
        self._ui.setupUi(self)
        
    
    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'loops'
        ret['group'] = 'RF_FDL_DLLRF'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret


def main():
    app = Qt.QApplication(sys.argv)
    w = Loops()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
