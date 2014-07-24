# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widgets/ui/FacadeAdjustments.ui'
#
# Created: Thu Jul 24 09:39:30 2014
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_facadeAdjustments(object):
    def setupUi(self, facadeAdjustments):
        facadeAdjustments.setObjectName(_fromUtf8("facadeAdjustments"))
        facadeAdjustments.resize(225, 113)
        self.gridLayout = QtGui.QGridLayout(facadeAdjustments)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.cavityVolts = QtGui.QGroupBox(facadeAdjustments)
        self.cavityVolts.setObjectName(_fromUtf8("cavityVolts"))
        self.gridLayout_2 = QtGui.QGridLayout(self.cavityVolts)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 1, 6, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem1, 1, 3, 1, 1)
        self.cavityVoltsMValue = QtGui.QDoubleSpinBox(self.cavityVolts)
        self.cavityVoltsMValue.setDecimals(4)
        self.cavityVoltsMValue.setSingleStep(0.0001)
        self.cavityVoltsMValue.setObjectName(_fromUtf8("cavityVoltsMValue"))
        self.gridLayout_2.addWidget(self.cavityVoltsMValue, 1, 2, 1, 1)
        self.cavityVoltsNValue = QtGui.QDoubleSpinBox(self.cavityVolts)
        self.cavityVoltsNValue.setDecimals(4)
        self.cavityVoltsNValue.setSingleStep(0.0001)
        self.cavityVoltsNValue.setObjectName(_fromUtf8("cavityVoltsNValue"))
        self.gridLayout_2.addWidget(self.cavityVoltsNValue, 1, 5, 1, 1)
        self.cavityVoltsNLabel = QtGui.QLabel(self.cavityVolts)
        self.cavityVoltsNLabel.setObjectName(_fromUtf8("cavityVoltsNLabel"))
        self.gridLayout_2.addWidget(self.cavityVoltsNLabel, 1, 4, 1, 1)
        self.cavityVoltsMLabel = QtGui.QLabel(self.cavityVolts)
        self.cavityVoltsMLabel.setObjectName(_fromUtf8("cavityVoltsMLabel"))
        self.gridLayout_2.addWidget(self.cavityVoltsMLabel, 1, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem2, 1, 0, 1, 1)
        self.cavityVoltsFormula = QtGui.QLabel(self.cavityVolts)
        self.cavityVoltsFormula.setAlignment(QtCore.Qt.AlignCenter)
        self.cavityVoltsFormula.setObjectName(_fromUtf8("cavityVoltsFormula"))
        self.gridLayout_2.addWidget(self.cavityVoltsFormula, 0, 1, 1, 5)
        self.gridLayout.addWidget(self.cavityVolts, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(facadeAdjustments)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(facadeAdjustments)
        QtCore.QMetaObject.connectSlotsByName(facadeAdjustments)
        facadeAdjustments.setTabOrder(self.cavityVoltsMValue, self.cavityVoltsNValue)
        facadeAdjustments.setTabOrder(self.cavityVoltsNValue, self.buttonBox)

    def retranslateUi(self, facadeAdjustments):
        facadeAdjustments.setWindowTitle(QtGui.QApplication.translate("facadeAdjustments", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.cavityVolts.setTitle(QtGui.QApplication.translate("facadeAdjustments", "Cavity Volts", None, QtGui.QApplication.UnicodeUTF8))
        self.cavityVoltsNLabel.setText(QtGui.QApplication.translate("facadeAdjustments", "n", None, QtGui.QApplication.UnicodeUTF8))
        self.cavityVoltsMLabel.setText(QtGui.QApplication.translate("facadeAdjustments", "m", None, QtGui.QApplication.UnicodeUTF8))
        self.cavityVoltsFormula.setText(QtGui.QApplication.translate("facadeAdjustments", "y = (x-n)/m", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.panel import TaurusWidget
