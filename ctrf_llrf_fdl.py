#!/usr/bin/env python

#############################################################################
##
## This file is part of Taurus, a Tango User Interface Library
## 
## http://www.tango-controls.org/static/taurus/latest/doc/html/index.html
##
## Copyright 2014 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Taurus is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Taurus is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

import os,sys
import numpy as np

#The widgets are stored in a subdirectory and needs to be added to the pythonpath
linacWidgetsPath = os.environ['PWD']+'/widgets'
if not linacWidgetsPath in sys.path:
    sys.path.append(linacWidgetsPath)

from taurus.external.qt import Qt,QtGui,QtCore
from taurus.core.util import argparse
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus.qt.qtgui.base.taurusbase import TaurusBaseComponent
import taurus

from ui_MainView import Ui_FastDataLoggerDLLRF
from fileloader import fileLoader
from FdlFileParser import LoopsFile,DiagnosticsFile

class MainWindow(TaurusMainWindow):
    def __init__(self, parent=None):
        TaurusMainWindow.__init__(self)
        self.ui = Ui_FastDataLoggerDLLRF()
        self.ui.setupUi(self)
        self.initComponents()
        self._loopsParser = None
        self._diagParser = None
        self._activeParser = None
        self.splashScreen().finish(self)
    def initComponents(self):
        self.setWindowTitle("RF DLLRF FDL Taurus User Interface")
        self.centralwidget = self.ui.generalScrollArea
        self.setCentralWidget(self.centralwidget)
        Qt.QObject.connect(self.ui.loadButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self.loadFile)
        #TODO: remove the perspectives bar (meaning less in this gui)
        self.ui.replotButton.setEnabled(False)
        #TODO: this replot must be rescaling and decimating following the 
        #      settings in 
    def loadFile(self):
        self.info("Load file clicked")
        self.loader = LoadFileDialog(self)
        self.loader.closeApp.connect(self.cancelled)
        #Qt.QObject.connect(self.loader,Qt.SIGNAL("closeApp"),self.cancelled)
        self.loader.selectionDone.connect(self.prepare)
        #Qt.QObject.connect(self.loader,Qt.SIGNAL("selectionDone"),self.prepare)
        self.loader.show()
    def cancelled(self):
        self.info("cancelled()")
        self.loader.hide()
        self.loader = None
    def prepare(self):
        self.info("prepare()")
        selection = self.loader.getSelection()
        self.info("prepare(): "%(selection))
        self.loader.hide()
        self.loader = None
        #build a FdlFileParser objects
        self.prepareProgressBar()
        if len(selection['Loops']) > 0:
            self._loopsParser = LoopsFile(selection['Loops'])
            self._fileParser = self._loopsParser
            self._loopsParser.step.connect(self.updateProgressBar)
            self._loopsParser.process()
            self._loopsParser.complete.connect(self.endProgressBar)
        elif len(selection['Diag']) > 0:
            self._diagParser = DiagnosticsFile(selection['Diag'])
            self._fileParser = self._diagParser
            self._diagParser.process()
            self._diagParser.complete.connect(self.endProgressBar)
        #TODO: configure ranges and decimation
        #TODO: plot signals
        #self.ui.topLeft.
    def prepareProgressBar(self):
        self.enableTimeAndDecimation(False)
        self.ui.progressBar.setEnabled(True)
        self.ui.progressBar.setValue(0)
    def updateProgressBar(self):
        self.ui.progressBar.setValue(self._fileParser.percentage)
    def endProgressBar(self):
        self.enableTimeAndDecimation(True)
        self.ui.progressBar.setValue(100)
        self.ui.progressBar.setEnabled(False)
        #TODO: report the anomalities rate in the statusBar
        #TODO: for the current self._fileParser
        if type(self._fileParser) == LoopsFile:
            self.ui.loops1Plots._ui.topLeft.attachRawData({\
                                    'title':'Voltage Cavity',
                                    'x':np.linspace(0,411,len(self._fileParser._signals['CavVolt_kV'])),
                                    'y':self._fileParser._signals['CavVolt_kV']\
                                    })
    def enableTimeAndDecimation(self,enable=True):
        self.ui.timeAndDecimation._ui.startValue.setEnabled(enable)
        self.ui.timeAndDecimation._ui.stopValue.setEnabled(enable)
        self.ui.timeAndDecimation._ui.decimationValue.setEnabled(enable)
        self.ui.replotButton.setEnabled(enable)

sandbox = '/data'
defaultConfigurations = "%s/RF/FDL_Lyrtech"%(sandbox)
knownPlants = ['%s%s'%(s,p) for s in ['06','10','14'] for p in ['A','B']]+['LAB']

class LoadFileDialog(Qt.QDialog,TaurusBaseComponent):
    '''This class is made to show a dialog to the user where select the 
       files to be loaded in the FDL application.
       There can be one or two files to be loaded (one from each type).
       From the file(s) name(s), it will attempt to infer the plant and 
       the corresponding facade. In this two cases, if something when 
       wrong, a human readable message shall be written in 
       'fineTuneLabel' QLabel widget.
    '''
    closeApp = QtCore.pyqtSignal()
    selectionDone = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        Qt.QDialog.__init__(self, parent)
        name = "LoadFileDialog"
        self.call__init__(TaurusBaseComponent, name, parent=parent,
                          designMode=False)
        self._parent = parent
        self.resize(500, 200)
        #self.ui = Ui_fileLoader()
        #self.ui.setupUi(self)
        self.initComponents()

    def initComponents(self):
        self.setWindowTitle("Fast Data Logger file loader")
        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        self._panel = fileLoader()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._panel)
        #signals for the file choosers:
        Qt.QObject.connect(self.panel().loopsFileDialog,
                           Qt.SIGNAL('clicked(bool)'),
                           self.selectLoopsFile)
        self._loopsFile = ""
        Qt.QObject.connect(self.panel().diagFileDialog,
                           Qt.SIGNAL('clicked(bool)'),
                           self.selectDiagFile)
        self._diagFile = ""
        #TODO: signals for plants and facades
        self.panel().locationCombo.addItems(['']+knownPlants)
        Qt.QObject.connect(self.panel().locationCombo,
                           Qt.SIGNAL('editTextChanged(QString)'),
                           self.selectPlant)
        self._plant = ""
        db = taurus.Database()
        db.getServerNameInstances('LLRFFacade')
        facadesFound = [x.serverInstance() for x in \
                                       db.getServerNameInstances('LLRFFacade')]
        self.panel().facadeCombo.addItems(['']+facadesFound)
        self.info("Found %d facades: %s"%(len(facadesFound),facadesFound))
        self._facade = ""
        #signals for the action buttons
        okButton = self.panel().buttonBox.button(QtGui.QDialogButtonBox.Ok)
        okButton.setEnabled(False)
        Qt.QObject.connect(okButton,
                           Qt.SIGNAL('clicked(bool)'),self.accepted)
        cancellButton = \
                   self.panel().buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        Qt.QObject.connect(cancellButton,
                           Qt.SIGNAL('clicked(bool)'),self.canceled)

    def selectFile(self,dialogTitle):
        filters = "Binary data files (*.dat);;All files (*)"
        fileName = QtGui.QFileDialog.getOpenFileName(self,dialogTitle,
                                                 defaultConfigurations,filters)
        self.info("Selected: %s"%(fileName))
        plant = fileName.rsplit('/',1)[1].split('_')[1]
        if not plant in knownPlants:
            self.warningMsg("File name structure", "The name of the selected "\
                            "file does not contain the RF plant tag.")
        else:
            self.selectPlant(plant)
        return fileName

    def selectLoopsFile(self):
        fileName = self.selectFile("Loops file chooser")
        if not fileName.rsplit('/',1)[1].startswith('Loops'):
            self.warningMsg("File name structure","The name of the selected "\
                            "file does not starts with 'Loops'")
        self.panel().loopsFileName.setText(fileName)
        self._loopsFile = fileName
        self.panel().buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)

    def selectDiagFile(self):
        fileName = self.selectFile("Diagnostics file chooser")
        if not fileName.rsplit('/',1)[1].startswith('Diag'):
            self.warningMsg("File name structure","The name of the selected "\
                            "file does not starts with 'Diag'")
        self.panel().diagFileName.setText(fileName)
        self._diagFile = fileName
        self.panel().buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)

    def selectPlant(self,plant):
        self.info("Selecting the plant: %s"%(str(plant)))
        currentText = self.panel().locationCombo.currentText()
        currentIndex = self.panel().locationCombo.currentIndex()
        self.info("Current combo text: %s at %d"
                  %(currentText,currentIndex))
        newIndex = self.panel().locationCombo.findText(str(plant))
        if newIndex == -1: #doesn't exist
            self.panel().addItem(str(plant))
        elif newIndex != currentIndex and currentText != '':
            self.warning("Location has change!!")
            pass#TODO: warn the user about a location change
        self.panel().locationCombo.setCurrentIndex(newIndex)
        self._plant = plant
        #self.searchFacade()
        #it cannot be smart enough to know that

    def searchFacade(self):
        self._plant
        

    def getSelection(self):
        return {'Loops':self._loopsFile,
                'Diag':self._diagFile,
                'plant':self._plant,
                'facade':self._facade}

    def panel(self):
        return self._panel._ui
    
    def accepted(self):
        self.info("Accepted call")
        if len(self._loopsFile) == 0 and len(self._diagFile) == 0:
            self.error("cannot accept without any file chosen!")
            return
        self.selectionDone.emit()

    def canceled(self):
        self.info("Cancelling...")
        self.closeApp.emit()

    def warningMsg(self,title,msg):
        QtGui.QMessageBox.warning(self,title,msg)

def main():
    parser = argparse.get_taurus_parser()
    app = TaurusApplication(sys.argv, cmd_line_parser=parser,
                      app_name='ctrfdllrf_fdl', app_version='0.1',
                      org_domain='ALBA', org_name='ALBA')
    options = app.get_command_line_options()
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()