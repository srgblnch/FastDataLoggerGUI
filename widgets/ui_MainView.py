# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/MainView.ui'
#
# Created: Fri Jul 11 15:22:58 2014
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_FastDataLoggerDLLRF(object):
    def setupUi(self, FastDataLoggerDLLRF):
        FastDataLoggerDLLRF.setObjectName(_fromUtf8("FastDataLoggerDLLRF"))
        FastDataLoggerDLLRF.resize(800, 1000)
        self.gridLayout_5 = QtGui.QGridLayout(FastDataLoggerDLLRF)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.generalScrollArea = QtGui.QScrollArea(FastDataLoggerDLLRF)
        self.generalScrollArea.setWidgetResizable(True)
        self.generalScrollArea.setObjectName(_fromUtf8("generalScrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 786, 986))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.gridLayout = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.loadButton = QtGui.QPushButton(self.scrollAreaWidgetContents)
        self.loadButton.setObjectName(_fromUtf8("loadButton"))
        self.gridLayout.addWidget(self.loadButton, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(356, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 1, 1, 1)
        self.timeAndDecimation = timeAndDecimation(self.scrollAreaWidgetContents)
        self.timeAndDecimation.setObjectName(_fromUtf8("timeAndDecimation"))
        self.gridLayout.addWidget(self.timeAndDecimation, 0, 2, 1, 1)
        self.replotButton = QtGui.QPushButton(self.scrollAreaWidgetContents)
        self.replotButton.setObjectName(_fromUtf8("replotButton"))
        self.gridLayout.addWidget(self.replotButton, 0, 3, 1, 1)
        self.plotsTab = QtGui.QTabWidget(self.scrollAreaWidgetContents)
        self.plotsTab.setObjectName(_fromUtf8("plotsTab"))
        self.loops1Tab = QtGui.QWidget()
        self.loops1Tab.setObjectName(_fromUtf8("loops1Tab"))
        self.gridLayout_2 = QtGui.QGridLayout(self.loops1Tab)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.loops1ScrollArea = QtGui.QScrollArea(self.loops1Tab)
        self.loops1ScrollArea.setWidgetResizable(True)
        self.loops1ScrollArea.setObjectName(_fromUtf8("loops1ScrollArea"))
        self.loops1ScrollAreaWidgetContents = QtGui.QWidget()
        self.loops1ScrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 756, 823))
        self.loops1ScrollAreaWidgetContents.setObjectName(_fromUtf8("loops1ScrollAreaWidgetContents"))
        self.gridLayout_6 = QtGui.QGridLayout(self.loops1ScrollAreaWidgetContents)
        self.gridLayout_6.setObjectName(_fromUtf8("gridLayout_6"))
        self.loops1Plots = Loops(self.loops1ScrollAreaWidgetContents)
        self.loops1Plots.setObjectName(_fromUtf8("loops1Plots"))
        self.gridLayout_6.addWidget(self.loops1Plots, 0, 0, 1, 1)
        self.loops1ScrollArea.setWidget(self.loops1ScrollAreaWidgetContents)
        self.gridLayout_2.addWidget(self.loops1ScrollArea, 0, 0, 1, 1)
        self.plotsTab.addTab(self.loops1Tab, _fromUtf8(""))
        self.loops2Tab = QtGui.QWidget()
        self.loops2Tab.setObjectName(_fromUtf8("loops2Tab"))
        self.gridLayout_3 = QtGui.QGridLayout(self.loops2Tab)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.loops2ScrollArea = QtGui.QScrollArea(self.loops2Tab)
        self.loops2ScrollArea.setWidgetResizable(True)
        self.loops2ScrollArea.setObjectName(_fromUtf8("loops2ScrollArea"))
        self.loops2ScrollAreaWidgetContents = QtGui.QWidget()
        self.loops2ScrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 756, 823))
        self.loops2ScrollAreaWidgetContents.setObjectName(_fromUtf8("loops2ScrollAreaWidgetContents"))
        self.gridLayout_7 = QtGui.QGridLayout(self.loops2ScrollAreaWidgetContents)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.loops2Plots = Loops(self.loops2ScrollAreaWidgetContents)
        self.loops2Plots.setObjectName(_fromUtf8("loops2Plots"))
        self.gridLayout_7.addWidget(self.loops2Plots, 0, 0, 1, 1)
        self.loops2ScrollArea.setWidget(self.loops2ScrollAreaWidgetContents)
        self.gridLayout_3.addWidget(self.loops2ScrollArea, 0, 0, 1, 1)
        self.plotsTab.addTab(self.loops2Tab, _fromUtf8(""))
        self.diagTab = QtGui.QWidget()
        self.diagTab.setObjectName(_fromUtf8("diagTab"))
        self.gridLayout_4 = QtGui.QGridLayout(self.diagTab)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.diagScrollArea = QtGui.QScrollArea(self.diagTab)
        self.diagScrollArea.setWidgetResizable(True)
        self.diagScrollArea.setObjectName(_fromUtf8("diagScrollArea"))
        self.diagScrollAreaWidgetContents = QtGui.QWidget()
        self.diagScrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 741, 828))
        self.diagScrollAreaWidgetContents.setObjectName(_fromUtf8("diagScrollAreaWidgetContents"))
        self.gridLayout_8 = QtGui.QGridLayout(self.diagScrollAreaWidgetContents)
        self.gridLayout_8.setObjectName(_fromUtf8("gridLayout_8"))
        self.diagnosticsPlots = Diagnostics(self.diagScrollAreaWidgetContents)
        self.diagnosticsPlots.setObjectName(_fromUtf8("diagnosticsPlots"))
        self.gridLayout_8.addWidget(self.diagnosticsPlots, 0, 0, 1, 1)
        self.diagScrollArea.setWidget(self.diagScrollAreaWidgetContents)
        self.gridLayout_4.addWidget(self.diagScrollArea, 0, 0, 1, 1)
        self.plotsTab.addTab(self.diagTab, _fromUtf8(""))
        self.gridLayout.addWidget(self.plotsTab, 1, 0, 1, 4)
        self.progressBar = QtGui.QProgressBar(self.scrollAreaWidgetContents)
        self.progressBar.setEnabled(False)
        self.progressBar.setProperty("value", 100)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 2, 0, 1, 4)
        self.generalScrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout_5.addWidget(self.generalScrollArea, 0, 0, 1, 1)

        self.retranslateUi(FastDataLoggerDLLRF)
        self.plotsTab.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(FastDataLoggerDLLRF)

    def retranslateUi(self, FastDataLoggerDLLRF):
        FastDataLoggerDLLRF.setWindowTitle(QtGui.QApplication.translate("FastDataLoggerDLLRF", "ctrffdl", None, QtGui.QApplication.UnicodeUTF8))
        self.loadButton.setText(QtGui.QApplication.translate("FastDataLoggerDLLRF", "Load Data", None, QtGui.QApplication.UnicodeUTF8))
        self.replotButton.setText(QtGui.QApplication.translate("FastDataLoggerDLLRF", "Replot", None, QtGui.QApplication.UnicodeUTF8))
        self.plotsTab.setTabText(self.plotsTab.indexOf(self.loops1Tab), QtGui.QApplication.translate("FastDataLoggerDLLRF", "Loops1", None, QtGui.QApplication.UnicodeUTF8))
        self.plotsTab.setTabText(self.plotsTab.indexOf(self.loops2Tab), QtGui.QApplication.translate("FastDataLoggerDLLRF", "Loops2", None, QtGui.QApplication.UnicodeUTF8))
        self.plotsTab.setTabText(self.plotsTab.indexOf(self.diagTab), QtGui.QApplication.translate("FastDataLoggerDLLRF", "Diagnostics", None, QtGui.QApplication.UnicodeUTF8))

from loops import Loops
from taurus.qt.qtgui.panel import TaurusWidget
from timeanddecimation import timeAndDecimation
from diagnostics import Diagnostics
