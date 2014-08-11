# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widgets/ui/DiagPlots.ui'
#
# Created: Thu Jul 24 11:13:00 2014
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Diagnostics(object):
    def setupUi(self, Diagnostics):
        Diagnostics.setObjectName(_fromUtf8("Diagnostics"))
        Diagnostics.resize(612, 820)
        self.gridLayout = QtGui.QGridLayout(Diagnostics)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.topRight = TaurusPlot(Diagnostics)
        self.topRight.setObjectName(_fromUtf8("topRight"))
        self.gridLayout.addWidget(self.topRight, 0, 1, 1, 1)
        self.middleDownRight = TaurusPlot(Diagnostics)
        self.middleDownRight.setObjectName(_fromUtf8("middleDownRight"))
        self.gridLayout.addWidget(self.middleDownRight, 2, 1, 1, 1)
        self.middleDownLeft = TaurusPlot(Diagnostics)
        self.middleDownLeft.setObjectName(_fromUtf8("middleDownLeft"))
        self.gridLayout.addWidget(self.middleDownLeft, 2, 0, 1, 1)
        self.topLeft = TaurusPlot(Diagnostics)
        self.topLeft.setObjectName(_fromUtf8("topLeft"))
        self.gridLayout.addWidget(self.topLeft, 0, 0, 1, 1)
        self.middleUpLeft = TaurusPlot(Diagnostics)
        self.middleUpLeft.setObjectName(_fromUtf8("middleUpLeft"))
        self.gridLayout.addWidget(self.middleUpLeft, 1, 0, 1, 1)
        self.bottomLeft = TaurusPlot(Diagnostics)
        self.bottomLeft.setObjectName(_fromUtf8("bottomLeft"))
        self.gridLayout.addWidget(self.bottomLeft, 3, 0, 1, 1)
        self.middleUpRight = TaurusPlot(Diagnostics)
        self.middleUpRight.setObjectName(_fromUtf8("middleUpRight"))
        self.gridLayout.addWidget(self.middleUpRight, 1, 1, 1, 1)
        self.bottomRight = TaurusPlot(Diagnostics)
        self.bottomRight.setObjectName(_fromUtf8("bottomRight"))
        self.gridLayout.addWidget(self.bottomRight, 3, 1, 1, 1)

        self.retranslateUi(Diagnostics)
        QtCore.QMetaObject.connectSlotsByName(Diagnostics)

    def retranslateUi(self, Diagnostics):
        Diagnostics.setWindowTitle(QtGui.QApplication.translate("Diagnostics", "Form", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.panel import TaurusWidget
from taurus.qt.qtgui.plot import TaurusPlot
