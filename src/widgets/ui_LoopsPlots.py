# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/LoopsPlots.ui'
#
# Created: Thu Jul 10 14:48:34 2014
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Loops(object):
    def setupUi(self, Loops):
        Loops.setObjectName(_fromUtf8("Loops"))
        Loops.resize(612, 616)
        self.gridLayout = QtGui.QGridLayout(Loops)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.topLeft = TaurusPlot(Loops)
        self.topLeft.setObjectName(_fromUtf8("topLeft"))
        self.gridLayout.addWidget(self.topLeft, 0, 0, 1, 1)
        self.middleLeft = TaurusPlot(Loops)
        self.middleLeft.setObjectName(_fromUtf8("middleLeft"))
        self.gridLayout.addWidget(self.middleLeft, 1, 0, 1, 1)
        self.middleRight = TaurusPlot(Loops)
        self.middleRight.setObjectName(_fromUtf8("middleRight"))
        self.gridLayout.addWidget(self.middleRight, 1, 1, 1, 1)
        self.topRight = TaurusPlot(Loops)
        self.topRight.setObjectName(_fromUtf8("topRight"))
        self.gridLayout.addWidget(self.topRight, 0, 1, 1, 1)
        self.bottomLeft = TaurusPlot(Loops)
        self.bottomLeft.setObjectName(_fromUtf8("bottomLeft"))
        self.gridLayout.addWidget(self.bottomLeft, 2, 0, 1, 1)
        self.bottomRight = TaurusPlot(Loops)
        self.bottomRight.setObjectName(_fromUtf8("bottomRight"))
        self.gridLayout.addWidget(self.bottomRight, 2, 1, 1, 1)

        self.retranslateUi(Loops)
        QtCore.QMetaObject.connectSlotsByName(Loops)

    def retranslateUi(self, Loops):
        Loops.setWindowTitle(QtGui.QApplication.translate("Loops", "Form", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.panel import TaurusWidget
from taurus.qt.qtgui.plot import TaurusPlot
