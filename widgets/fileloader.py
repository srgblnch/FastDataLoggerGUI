#!/usr/bin/env python

# Code implementation generated from reading ui file 'ui/FileLoader.ui'
#
# Created: Thu Jul 10 14:46:49 2014 
#      by: Taurus UI code generator 3.2.0
#
# WARNING! All changes made in this file will be lost!

__docformat__ = 'restructuredtext'

import sys
import PyQt4.Qt as Qt
from ui_FileLoader import Ui_fileLoader
from taurus.qt.qtgui.panel import TaurusWidget

class fileLoader(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)
        
        self._ui = Ui_fileLoader()
        self._ui.setupUi(self)
        
    

def main():
    app = Qt.QApplication(sys.argv)
    w = fileLoader()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
