# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widgets/ui/FileLoader.ui'
#
# Created: Tue Jul 29 14:37:25 2014
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_fileLoader(object):
    def setupUi(self, fileLoader):
        fileLoader.setObjectName(_fromUtf8("fileLoader"))
        fileLoader.resize(489, 220)
        self.gridLayout_4 = QtGui.QGridLayout(fileLoader)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.line = QtGui.QFrame(fileLoader)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout_4.addWidget(self.line, 2, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(fileLoader)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout_4.addWidget(self.buttonBox, 4, 1, 1, 1)
        self.fineTuneLabel = QtGui.QLabel(fileLoader)
        self.fineTuneLabel.setText(_fromUtf8(""))
        self.fineTuneLabel.setObjectName(_fromUtf8("fineTuneLabel"))
        self.gridLayout_4.addWidget(self.fineTuneLabel, 4, 0, 1, 1)
        self.fineTuneLayout = QtGui.QGridLayout()
        self.fineTuneLayout.setObjectName(_fromUtf8("fineTuneLayout"))
        self.locationLabel = QtGui.QLabel(fileLoader)
        self.locationLabel.setObjectName(_fromUtf8("locationLabel"))
        self.fineTuneLayout.addWidget(self.locationLabel, 0, 3, 1, 1)
        self.beamCurrentLabel = QtGui.QLabel(fileLoader)
        self.beamCurrentLabel.setObjectName(_fromUtf8("beamCurrentLabel"))
        self.fineTuneLayout.addWidget(self.beamCurrentLabel, 0, 0, 1, 1)
        self.facadeCombo = QtGui.QComboBox(fileLoader)
        self.facadeCombo.setEditable(True)
        self.facadeCombo.setObjectName(_fromUtf8("facadeCombo"))
        self.fineTuneLayout.addWidget(self.facadeCombo, 1, 4, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.fineTuneLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.facadeLabel = QtGui.QLabel(fileLoader)
        self.facadeLabel.setObjectName(_fromUtf8("facadeLabel"))
        self.fineTuneLayout.addWidget(self.facadeLabel, 1, 3, 1, 1)
        self.locationCombo = QtGui.QComboBox(fileLoader)
        self.locationCombo.setEditable(True)
        self.locationCombo.setObjectName(_fromUtf8("locationCombo"))
        self.fineTuneLayout.addWidget(self.locationCombo, 0, 4, 1, 1)
        self.beamCurrentValue = QtGui.QDoubleSpinBox(fileLoader)
        self.beamCurrentValue.setObjectName(_fromUtf8("beamCurrentValue"))
        self.fineTuneLayout.addWidget(self.beamCurrentValue, 0, 1, 1, 1)
        self.gridLayout_4.addLayout(self.fineTuneLayout, 3, 0, 1, 2)
        self.diagGroup = QtGui.QGroupBox(fileLoader)
        self.diagGroup.setObjectName(_fromUtf8("diagGroup"))
        self.gridLayout_2 = QtGui.QGridLayout(self.diagGroup)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.diagFileName = QtGui.QLineEdit(self.diagGroup)
        self.diagFileName.setReadOnly(True)
        self.diagFileName.setObjectName(_fromUtf8("diagFileName"))
        self.gridLayout_2.addWidget(self.diagFileName, 0, 0, 1, 1)
        self.diagFileDialog = QtGui.QToolButton(self.diagGroup)
        self.diagFileDialog.setObjectName(_fromUtf8("diagFileDialog"))
        self.gridLayout_2.addWidget(self.diagFileDialog, 0, 1, 1, 1)
        self.gridLayout_4.addWidget(self.diagGroup, 1, 0, 1, 2)
        self.loopsGroup = QtGui.QGroupBox(fileLoader)
        self.loopsGroup.setObjectName(_fromUtf8("loopsGroup"))
        self.gridLayout = QtGui.QGridLayout(self.loopsGroup)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.loopsFileName = QtGui.QLineEdit(self.loopsGroup)
        self.loopsFileName.setReadOnly(True)
        self.loopsFileName.setObjectName(_fromUtf8("loopsFileName"))
        self.gridLayout.addWidget(self.loopsFileName, 0, 0, 1, 1)
        self.loopsFileDialog = QtGui.QToolButton(self.loopsGroup)
        self.loopsFileDialog.setObjectName(_fromUtf8("loopsFileDialog"))
        self.gridLayout.addWidget(self.loopsFileDialog, 0, 1, 1, 1)
        self.gridLayout_4.addWidget(self.loopsGroup, 0, 0, 1, 2)

        self.retranslateUi(fileLoader)
        QtCore.QMetaObject.connectSlotsByName(fileLoader)

    def retranslateUi(self, fileLoader):
        fileLoader.setWindowTitle(QtGui.QApplication.translate("fileLoader", "Load Files", None, QtGui.QApplication.UnicodeUTF8))
        self.locationLabel.setText(QtGui.QApplication.translate("fileLoader", "RF plant:", None, QtGui.QApplication.UnicodeUTF8))
        self.beamCurrentLabel.setText(QtGui.QApplication.translate("fileLoader", "Beam current", None, QtGui.QApplication.UnicodeUTF8))
        self.facadeLabel.setText(QtGui.QApplication.translate("fileLoader", "Facade:", None, QtGui.QApplication.UnicodeUTF8))
        self.diagGroup.setTitle(QtGui.QApplication.translate("fileLoader", "Diagnostics file name:", None, QtGui.QApplication.UnicodeUTF8))
        self.diagFileDialog.setText(QtGui.QApplication.translate("fileLoader", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.loopsGroup.setTitle(QtGui.QApplication.translate("fileLoader", "Loops file name:", None, QtGui.QApplication.UnicodeUTF8))
        self.loopsFileDialog.setText(QtGui.QApplication.translate("fileLoader", "...", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.panel import TaurusWidget
