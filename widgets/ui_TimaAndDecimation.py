# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widgets/ui/TimaAndDecimation.ui'
#
# Created: Thu Jul 24 09:39:53 2014
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_timeAndDecimation(object):
    def setupUi(self, timeAndDecimation):
        timeAndDecimation.setObjectName(_fromUtf8("timeAndDecimation"))
        timeAndDecimation.resize(285, 82)
        self.gridLayout = QtGui.QGridLayout(timeAndDecimation)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.decimationLabel = QtGui.QLabel(timeAndDecimation)
        self.decimationLabel.setObjectName(_fromUtf8("decimationLabel"))
        self.gridLayout.addWidget(self.decimationLabel, 2, 0, 1, 1)
        self.startValue = QtGui.QDoubleSpinBox(timeAndDecimation)
        self.startValue.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.startValue.setMaximum(411.0)
        self.startValue.setObjectName(_fromUtf8("startValue"))
        self.gridLayout.addWidget(self.startValue, 0, 1, 1, 1)
        self.startLabel = QtGui.QLabel(timeAndDecimation)
        self.startLabel.setObjectName(_fromUtf8("startLabel"))
        self.gridLayout.addWidget(self.startLabel, 0, 0, 1, 1)
        self.decimationValue = QtGui.QSpinBox(timeAndDecimation)
        self.decimationValue.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.decimationValue.setMinimum(1)
        self.decimationValue.setMaximum(1000)
        self.decimationValue.setObjectName(_fromUtf8("decimationValue"))
        self.gridLayout.addWidget(self.decimationValue, 2, 1, 1, 1)
        self.stopLabel = QtGui.QLabel(timeAndDecimation)
        self.stopLabel.setObjectName(_fromUtf8("stopLabel"))
        self.gridLayout.addWidget(self.stopLabel, 1, 0, 1, 1)
        self.endValue = QtGui.QDoubleSpinBox(timeAndDecimation)
        self.endValue.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.endValue.setMaximum(411.0)
        self.endValue.setProperty("value", 411.0)
        self.endValue.setObjectName(_fromUtf8("endValue"))
        self.gridLayout.addWidget(self.endValue, 1, 1, 1, 1)

        self.retranslateUi(timeAndDecimation)
        QtCore.QMetaObject.connectSlotsByName(timeAndDecimation)
        timeAndDecimation.setTabOrder(self.startValue, self.endValue)
        timeAndDecimation.setTabOrder(self.endValue, self.decimationValue)

    def retranslateUi(self, timeAndDecimation):
        timeAndDecimation.setWindowTitle(QtGui.QApplication.translate("timeAndDecimation", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.decimationLabel.setText(QtGui.QApplication.translate("timeAndDecimation", "Decimation [1,1000]", None, QtGui.QApplication.UnicodeUTF8))
        self.startValue.setSuffix(QtGui.QApplication.translate("timeAndDecimation", " ms", None, QtGui.QApplication.UnicodeUTF8))
        self.startLabel.setText(QtGui.QApplication.translate("timeAndDecimation", "Start Display [0,411] ms", None, QtGui.QApplication.UnicodeUTF8))
        self.stopLabel.setText(QtGui.QApplication.translate("timeAndDecimation", "End Display [0,411] ms", None, QtGui.QApplication.UnicodeUTF8))
        self.endValue.setSuffix(QtGui.QApplication.translate("timeAndDecimation", " ms", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.panel import TaurusWidget
