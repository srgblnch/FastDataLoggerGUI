#!/usr/bin/env python

# Code implementation generated from reading ui file 'ui/MainView.ui'
#
# Created: Thu Jul 10 14:46:43 2014 
#      by: Taurus UI code generator 3.2.0
#
# WARNING! All changes made in this file will be lost!

__docformat__ = 'restructuredtext'

import sys
import PyQt4.Qt as Qt
from ui_MainView import Ui_FastDataLoggerDLLRF
from taurus.qt.qtgui.panel import TaurusWidget

class FastDataLoggerDLLRF(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)
        
        self._ui = Ui_FastDataLoggerDLLRF()
        self._ui.setupUi(self)
        
    

def main():
    app = Qt.QApplication(sys.argv)
    w = FastDataLoggerDLLRF()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
