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
import time

#The widgets are stored in a subdirectory and 
#needs to be added to the pythonpath
linacWidgetsPath = os.environ['PWD']+'/widgets'
if not linacWidgetsPath in sys.path:
    sys.path.append(linacWidgetsPath)

import taurus
try:#normal way
    from taurus.external.qt import Qt,QtGui,QtCore
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt,QtGui,QtCore
    from FdlFileParser import MyQtSignal
from taurus.core.util import argparse,Logger
from FdlLogger import *
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus.qt.qtgui.base.taurusbase import TaurusBaseComponent
from taurus.qt.qtgui.resource import getThemeIcon

from ui_MainView import Ui_FastDataLoggerDLLRF
from fileloader import fileLoader
from FdlFileParser import LoopsFile,DiagnosticsFile
from FdlSignals import SignalFields,Y2_
from FdlFacadeManager import FacadeManager,FACADES_SERVERNAME
from FdlSignalProcessor import SignalProcessor
from FdlPlotter import Plotter

class MainWindow(TaurusMainWindow,FdlLogger):
    def __init__(self, parent=None):
        TaurusMainWindow.__init__(self)
        FdlLogger.__init__(self)
        self.ui = Ui_FastDataLoggerDLLRF()
        self.ui.setupUi(self)
        self.initComponents()
        self._loader = None
        self._loopsParser = None
        self._diagParser = None
        #self._activeParser = None
        #self._facadaAdjustments = None
        self._facade = None
        self._postProcessor = None
        self._plotter = None
        self.splashScreen().finish(self)
    def initComponents(self):
        self.updateWindowTitle()
        self.centralwidget = self.ui.generalScrollArea
        self.setCentralWidget(self.centralwidget)
        #Remove the perspectives bar (meaning less in this gui)
        self.perspectivesToolBar.clear()
        self.prepareTimeAndDecimation()
        self.prepareHeader()
        #prepare button reactions
        Qt.QObject.connect(self.ui.loadButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self.loadFile)
        Qt.QObject.connect(self.ui.cancelButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self.cancel)
        #Like the button add also the loadFile to the menu
        self.loadFileAction = Qt.QAction(getThemeIcon("document-open"),
                                         'Open Files...',self)
        Qt.QObject.connect(self.loadFileAction, Qt.SIGNAL("triggered()"),
                           self.loadFile)
        #add the action before the first of the actions already existing
        try:
            before = self.fileMenu.actions()[0]
            self.fileMenu.insertAction(before,self.loadFileAction)
            self.fileMenu.insertAction(before,self.fileMenu.addSeparator())
        except Exception,e:
            self.fileMenu.addAction(self.loadFileAction)
            self.error("The 'Open Files...' action cannot be inserted as "\
                       "the first element of the 'File' menu")
        self.prepareWidgets()
        #adjustments on the facade configuration
        self.facadeAction = Qt.QAction('Facade fits',self)
        self.facadeAction.setEnabled(False)
        try:
            before = self.toolsMenu.actions()[0]
            self.toolsMenu.insertAction(before,self.facadeAction)
            self.toolsMenu.insertAction(before,self.toolsMenu.addSeparator())
        except Exception,e:
            self.error("The 'Facade fits' action cannot be inserted as "\
                       "the first element of the 'Tools' menu")
            self.toolsMenu.addAction(self.facadeAction)
    
    def updateWindowTitle(self,plant=None):
        title = "RF DLLRF FDL Taurus User Interface"
        if plant != None:
            title += " - %s"%plant
        self.setWindowTitle(title)
    
    def prepareTimeAndDecimation(self):
        self.ui.timeAndDecimation._ui.startValue.setMinimumWidth(100)
        self.ui.timeAndDecimation._ui.startValue.setSuffix(' ms')
        self.ui.timeAndDecimation._ui.endValue.setSuffix(' ms')
        Plotter(self) #the creation of this object (not yet needed) stablishes 
        #the initial default values and ranges of the time&decimation box.
    
    def prepareHeader(self):
        self.ui.LoopsFileValue.setReadOnly(True)
        self.ui.DiagFileValue.setReadOnly(True)
        self.ui.BeamCurrentValue.setMinimum(1.0)
        self.ui.BeamCurrentValue.setMaximum(400.0)
        #self.ui.beamCurrentValue.setValue(100.0)
        self.ui.BeamCurrentValue.setSuffix(' mA')
        self.ui.BeamCurrentValue.setEnabled(False)
    
    def prepareWidgets(self):
        self.ui.loadButton.setEnabled(True)
        self.ui.cancelButton.hide()
        self.ui.replotButton.setEnabled(False)
        self.ui.timeAndDecimation._ui.startValue.setEnabled(False)
        self.ui.timeAndDecimation._ui.endValue.setEnabled(False)
        self.ui.timeAndDecimation._ui.decimationValue.setEnabled(False)
        self.ui.BeamCurrentValue.setEnabled(False)
    
    def _enableWidgets(self,enable):
        #buttons
        self.ui.loadButton.setEnabled(enable)
        if enable:
            self.ui.cancelButton.hide()
        else:
            self.ui.cancelButton.show()
        #progressBar
        self.enableProgressBar(not enable)
        #configuration integers and replot
        self.ui.replotButton.setEnabled(enable)
        self.ui.timeAndDecimation._ui.startValue.setEnabled(enable)
        self.ui.timeAndDecimation._ui.endValue.setEnabled(enable)
        self.ui.timeAndDecimation._ui.decimationValue.setEnabled(enable)
        self.ui.BeamCurrentValue.setEnabled(enable)
        
    def closeEvent(self,event):
        if (self._loopsParser != None and self._loopsParser.isProcessing())or\
           (self._diagParser  != None and  self._diagParser.isProcessing()):
            result = QtGui.QMessageBox.question(self,
                                                "Confirm Exit...",
                                             "Are you sure you want to exit ?",
                                   QtGui.QMessageBox.Yes| QtGui.QMessageBox.No)
            if result == QtGui.QMessageBox.Yes:
                if self._loopsParser != None and \
                self._loopsParser.isProcessing():
                    self.info("Close event confirmed, "\
                              "cancelling the loops file processing.")
                    self._loopsParser.abort()
                if self._diagParser != None and \
                self._diagParser.isProcessing():
                    self.info("Close event confirmed, "\
                              "cancelling the diagnostics file processing.")
                    self._diagParser.abort()
#                if self._facade != None:
#                    if hasattr(self._facade,"_facadeAdjustments"):
#                        self._facade._facadeAdjustments = None
#                    self._facade.cancelFacade()
                self._closeFacadeDialog()
                event.accept()
            else:
                self._closeFacadeDialog()
                self.warning("User cancelled the close event!")
                event.ignore()
        else:
            self._closeFacadeDialog()
            self.info("close event, without pending task: "\
                      "no confirmation required.")
            event.accept()
    
    def _closeFacadeDialog(self):
        if self._facade != None:
            #if hasattr(self._facade,"_facadeAdjustments"):
                #self._facade._facadeAdjustments = None
            self._facade.cancelFacade()
    
    ####
    #--- Load file section
    def loadFile(self):
        self.debug("Load file clicked")
        if self._loader == None:
            self._loader = LoadFileDialog(self)
            self.connectSignal(self._loader,'closeApp',self.closeLoaderWidget)
            self.connectSignal(self._loader,'selectionDone',self.prepare)
        self._loader.show()
    def closeLoaderWidget(self):
        self.debug("closeLoaderWidget()")
        self._loader.hide()
        self._loader = None

    def prepare(self):
        self.cleanPrevious()
        selection = self._loader.getSelection()
        self.debug("prepare(): %s"%(str(selection)))
        self._loader.hide()
        #build a FdlFileParser objects
        self.prepareProgressBar()
        if len(selection['Loops']) > 0:
            self._loopsParser = LoopsFile(selection['Loops'])
            self.connectSignal(self._loopsParser,'step',self.loadingStep)
            self.connectSignal(self._loopsParser,'done',self.loadComplete)
            self.connectSignal(self._loopsParser,'swapping',
                           self.itsSwapping)
            self._loopsParser.process()
            self.memory()
        else:
            #self._loopsParser = None
            self.callCarbageCollector()
        if len(selection['Diag']) > 0:
            self._diagParser = DiagnosticsFile(selection['Diag'])
            self.connectSignal(self._diagParser,'step',self.loadingStep)
            self.connectSignal(self._diagParser,'done',self.loadComplete)
            self.connectSignal(self._diagParser,'swapping',
                           self.itsSwapping)
            #self._diagParser.process()
            self.memory()
        else:
            self._diagParser = None
            self.callCarbageCollector()
        self._launchParsers()
        self.parsingStatusMessage()
        #facade and plotting:
        self.facadeManagerBuilder(selection['facade'],selection['beamCurrent'])
        if self._facade.populateFacadeParams():
            self._facade.doFacadeAdjusments()
        self.populateHeader()
        self.memory()
        self._loader = None

    def populateHeader(self):
        selection = self._loader.getSelection()
        self.ui.LoopsFileValue.setText(selection['Loops'].split('/')[-1])
        self.ui.DiagFileValue.setText(selection['Diag'].split('/')[-1])
        self.updateWindowTitle(selection['plant'])
        self.ui.BeamCurrentValue.setValue(selection['beamCurrent'])
        #self.ui.BeamCurrentValue.setEnabled(True)
        #TODO: connect to FacadeManager to recalculate when this value changes
        self.connectSignal(self.ui.BeamCurrentValue,
                           'editingFinished()',
                           self.facadeHasUpdated)

    def connectSignal(self,obj,signalStr,callback):
        try:
            objStr = [ k for k,v in locals().iteritems() if v is obj][0]
            try:#normal way
                signal = getattr(obj,signalStr)
                signal.connect(callback)
                self.debug("Connected %s signal"%(signalStr))
            except:#backward compatibility to pyqt 4.4.3
                Qt.QObject.connect(obj,Qt.SIGNAL(signalStr),callback)
                self.deprecated("Connected %s signal"%(signalStr))
        except Exception,e:
            self.error("Cannot proceed conntecting %s signal due to: %s"
                       %(signalStr,e))
            
    def _launchParsers(self):
        if self._diagParser != None and hasattr(self._diagParser,'process'):
            self.debug("Launching Diagnostics parser")
            self._diagParser.process()
            time.sleep(0.1)
        if self._loopsParser != None and hasattr(self._loopsParser,'process'):
            self.debug("Launching Loops parser")
            self._loopsParser.process()
    def loadingStep(self):
        self.updateProgressBar()
        
    def loadComplete(self):
        alldone = True
        if self._getGlobalPercentage() == 100:
            if self._loopsParser == None:
                #when there is only a diagnostics file, change the tab
                self.ui.plotsTab.setCurrentIndex(2)
            self.endProgressBar()
            self.signalProcessorBuilder()
            self.populateSignalProcessor()
            self.enableProgressBar(False)
            self._postProcessor.process()
            #FIXME: report the user if something wasn't possible to be calculated
        #TODO: report the anomalies rate in the statusBar
    def cancel(self):
        if self._loopsParser != None:
            self._loopsParser.abort()
        if self._diagParser != None:
            self._diagParser.abort()
        self._closeFacadeDialog()
        self._enableWidgets(True)
        self.cancelStatusMessage()
    #--- done load file section
    ####
    
    ####
    #--- progress bar tools
    def enableProgressBar(self,enable):
        self.ui.progressBar.setEnabled(enable)
    def prepareProgressBar(self):
        self._enableWidgets(False)
        self.ui.progressBar.setValue(0)
    def _getGlobalPercentage(self):
        value = 0
        if self._loopsParser != None:
            value = self._loopsParser.percentage
        if self._diagParser != None:
            if value != 0:
                value = (value+self._diagParser.percentage)/2
                self.showMessage("Parsing Loops (%d%%) and Diagnostics "\
                                 "(%d%%) files."%(self._loopsParser.percentage,
                                                  self._diagParser.percentage))
            else:
                value = self._diagParser.percentage
        return value
    def updateProgressBar(self,value=None):
        if value == None:
            value = self._getGlobalPercentage()
        self.debug("new progress bar value %g%%"%(value))
        self.ui.progressBar.setValue(int(value))
    def endProgressBar(self):
        if self.areParsersProcessing():
            self.debug("One parser has finished, waiting the other")
            self.updateProgressBar()
            return
        self.debug("No more parsers working, proceed to calculations")
        self.ui.progressBar.setValue(100)
        self._enableWidgets(True)
    def showMessage(self,msg):
        self.info("Print in the statusBar the message: '%s'"%(msg))
        self.statusBar().showMessage(msg)
    def parsingStatusMessage(self):
        if self._loopsParser != None and self._diagParser != None:
            self.showMessage("Parsing Loops and Diagnostics files.")
        elif self._loopsParser != None:
            self.showMessage("Parsing Loops file.")
        elif self._diagParser != None:
            self.showMessage("Parsing Diagnostics file.")
    def processingStatusMessage(self):
        self.showMessage("Doing the data calculations.")
    def plottingStatusMessage(self):
        self.showMessage("Plotting the signals.")
    def cancelStatusMessage(self):
        self.showMessage("Process cancelled...")
    #--- done progress bar tools
    ####
    
    ####
    #--- File loaders area
    def areParsersProcessing(self):
        if self._loopsParser != None:
            loops = self.isLoopsProcessing() 
        else:
            loops = False
        if self._diagParser != None:
            diag = self.isDiagProcessing()
        else:
            diag = False
        return loops or diag
    def isLoopsProcessing(self):
        return self._loopsParser != None and self._loopsParser.isProcessing()
    def isDiagProcessing(self):
        return self._diagParser != None and self._diagParser.isProcessing()
    
    #--- done file loaders area
    ####
    
    ####
    #--- facade information area
    def facadeManagerBuilder(self,instanceName,beamCurrent):
        if self._facade != None and self._facade.instanceName != instanceName:
            self._facade = None
            self.callCarbageCollector()
        if self._facade == None:
            self._facade = FacadeManager(instanceName,beamCurrent)
        self.facadeAction.setEnabled(True)
        self.connect(self.facadeAction, Qt.SIGNAL("triggered()"),
                     self._facade.doFacadeAdjusments)
    #--- done facade information area
    ####
    
    ####
    #--- 
    def signalProcessorBuilder(self):
        self.debug("Builder for the SignalProcessor")
        if self._postProcessor != None:
            self.callCarbageCollector()
        else:
            self._postProcessor = SignalProcessor(self._facade)
            self.connectSignal(self._facade,'updated', self.facadeHasUpdated)
            self.connectSignal(self._postProcessor,'oneProcessed',
                               self.oneSignalProcessed)
            self.connectSignal(self._postProcessor,'allProcessed',
                               self.allSignalsProcessed)
            self.connectSignal(self._postProcessor,'swapping',
                               self.itsSwapping)
    def populateSignalProcessor(self):
        if self._loopsParser != None:
            self._postProcessor.appendSignals(self._loopsParser._signals)
            self.debug("loopsParser size is %d bytes, and it has delivered "\
                       "its data to postProcessor"
                       %(self._loopsParser.getObjectSize()))
            self._loopsParser = None
        if self._diagParser != None:
            self._postProcessor.appendSignals(self._diagParser._signals)
            self.debug("diagParser size is %d bytes, and it has delivered "\
                       "its data to postProcessor"
                       %(self._diagParser.getObjectSize()))
            self._diagParser = None
            self.memory()
    def facadeHasUpdated(self):
        self.debug("Received update signal from facade and calling processor")
        if not self.areParsersProcessing() and self._postProcessor != None:
            self.enableProgressBar(True)
            self.processingStatusMessage()
            self._postProcessor.process()
            self.memory()
    def oneSignalProcessed(self):
        self.debug("Received from SignalProcessor that one signal more has"\
                   "been processed. Update progress bar.")
        self.updateProgressBar(self._postProcessor.processPercentage)
        self.memory()
    def allSignalsProcessed(self):
        self.debug("Received from SignalProcessor that all signals has been "\
                   "processed. Create the Plotter")
        self.updateProgressBar(100)
        self.enableProgressBar(False)
        self.plotManagerBuilder()
    #---
    ####

    ####
    #--- plotting section
    def plotManagerBuilder(self):
        self.debug("Builder for the Plotter")
        if self._plotter != None:
            self.callCarbageCollector()
        else:
            self._plotter = Plotter(self)
            #self.connectSignal(self._plotter,'swapping',self.itsSwapping)
            self.connectSignal(self._plotter,'onePlotted',self.onePlotted)
            self.connectSignal(self._plotter,'allPlotted',self.allPlotted)
        self.populatePlotter()
    def populatePlotter(self):
        self._plotter.cleanSignals()
        self._plotter.appendSignals(self._postProcessor._signals)
        self.enableProgressBar(True)
        self.plottingStatusMessage()
        self._plotter.doPlots(force=True)
        self.memory()
    def onePlotted(self):
        self.updateProgressBar(self._plotter.processPercentage)
        self.memory()
    def allPlotted(self):
        self.updateProgressBar(100)
        self.enableProgressBar(False)
        self.cleanLoaders()
        self.memory()
        self.showMessage("")
    #--- done plotting section
    ####
    
    ####
    #--- Memory issues managing area
    def cleanPrevious(self):
        if self._postProcessor != None:
            self._postProcessor = None
        if self._plotter != None:
            self._plotter = None
        self.callCarbageCollector()
    def cleanLoaders(self):
        if self._loopsParser != None:
            self._loopsParser = None
        if self._diagParser != None:
            self._diagParser = None
        self.callCarbageCollector()
    def itsSwapping(self):
        if self.isProcessSwapping():
            QtGui.QMessageBox.warning(self,"Alert: swapping!",
            "The application has start to use swap memory and its process has"\
            "been paused. It will resume when memory issue is fixed.")
        while self._thereAreObjectsInStandby():
            if not self.isProcessSwapping():
                self._swapRecovery()
            else:
                swapUse,swapUnit = biggestBinaryPrefix(
                                            self.getProcessSwapUse(),unit='kB')
                self.debug("Still in swap (%s %s)"%(swapUse,swapUnit))
                time.sleep(1)
    def _thereAreObjectsInStandby(self):
        return self._loopsParser._standby.isSet() or \
               self._diagParser._standby.isSet() or \
               self._postProcessor._standby.isSet() or \
               self._plotter._standby.isSet()
    def _swapRecovery(self):
        for standby in [self._loopsParser._standby,self._diagParser._standby,
                        self._postProcessor._standby,self._plotter._standby]:
            if stanby.isSet():
                standby.clear()
    #--- done memory issues managing area
    ####

sandbox = '/data'
defaultConfigurations = "%s/RF/FDL_Lyrtech"%(sandbox)

#FACADE's hackishes:
# facade's device instances naming pattern:
#   - {longLocation}_RF_FACADE-{plant}[-02]
# filename's pattern:
#   - {Loops,Diag}_{shortLocation}{plant}_...
# Where 'shortLocation' has removed the 'SR' when sector is present, 
# and in those cases there are 'A' and 'B' plants, 
# not present in the other cases

PlantsDescriptor = {'WR':[''],'BO':[''],
                    'SR06':['A','B'],'SR10':['A','B'],'SR14':['A','B']}
knownPlants = ['%s%s'%(location,plant) for location in PlantsDescriptor.keys()\
                                       for plant in PlantsDescriptor[location]]
knownPlants.sort()

class PlantTranslator:
    def __init__(self,shortName):
        self._shortName = shortName
        if len(shortName) == 3 and \
           'SR%s'%(shortName[:2]) in PlantsDescriptor.keys():
            self._location = 'SR%s'%(shortName[:2])
            self._inSectorPlant = shortName[-1:]
        else:
            self._location = shortName
            self._inSectorPlant = ''
    @property
    def shortName(self):
        return self._shortName
    @property
    def completeName(self):
        return "%s%s"%(self._location,self._inSectorPlant)
    @property
    def facadeInstanceName(self):
        return "%s_RF_FACADE%s"%(self._location,"-%s"%self._inSectorPlant \
                                if len(self._inSectorPlant)>0 else '')

class LoadFileDialog(Qt.QDialog,TaurusBaseComponent):
    '''This class is made to show a dialog to the user where select the 
       files to be loaded in the FDL application.
       There can be one or two files to be loaded (one from each type).
       From the file(s) name(s), it will attempt to infer the plant and 
       the corresponding facade. In this two cases, if something when 
       wrong, a human readable message shall be written in 
       'fineTuneLabel' QLabel widget.
    '''
    try:#normal way
        closeApp = QtCore.pyqtSignal()
        selectionDone = QtCore.pyqtSignal()
        backward = False
    except:#backward compatibility to pyqt 4.4.3
        closeApp = MyQtSignal('closeApp')
        selectionDone = MyQtSignal('selectionDone')
        backward = True
    
    def __init__(self, parent=None):
        Qt.QDialog.__init__(self, parent)
        name = "LoadFileDialog"
        self.call__init__(TaurusBaseComponent, name, parent=parent,
                          designMode=False)
        if self.backward:
            self.closeApp._parent = self
            self.selectionDone._parent = self
        self._parent = parent
        self.resize(500, 200)
        #self.ui = Ui_fileLoader()
        #self.ui.setupUi(self)
        self._plant = None
        self._beamCurrent = 100#mA
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
        #signals for plants and facades
        self.panel().locationCombo.addItems(['']+knownPlants)
        Qt.QObject.connect(self.panel().locationCombo,
                           Qt.SIGNAL('editTextChanged(QString)'),
                           self.selectPlant)
        self.info("Known %d plants: %s"%(len(knownPlants),knownPlants))
        self._facadesFound = [x.serverInstance() for x in \
                  taurus.Database().getServerNameInstances(FACADES_SERVERNAME)]
        self._facadesFound.sort()
        self.panel().facadeCombo.addItems(['']+self._facadesFound)
        self.info("Found %d facades: %s"
                  %(len(self._facadesFound),self._facadesFound))
        #segment for the beam current
        self.setupBeamCurrent()
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
        fileName = str(QtGui.QFileDialog.getOpenFileName(self,dialogTitle,
                                                defaultConfigurations,filters))
        self.debug("Selected: %s"%(fileName))
        shortName = fileName.rsplit('/',1)[1].split('_')[1]
        self._plant = PlantTranslator(shortName)
        if not self._plant.completeName in knownPlants:
            self.warningMsg("File name structure", "The name of the selected "\
                            "file does not contain the RF plant tag.")
            self.warning("From the selected filename, the short plant name "\
                         "found was %s, and the longer version was %s. But "\
                         "wasn't possible to relate with one known"
                         %(shortName,self._plant.completeName))
        else:
            self.selectPlant(self._plant.completeName)
        return fileName

    def selectLoopsFile(self):
        fileName = self.selectFile("Loops file chooser")
        if not fileName.rsplit('/',1)[1].startswith('Loops'):
            self.warningMsg("File name structure","The name of the selected "\
                            "file does not starts with 'Loops'")
        self.panel().loopsFileName.setText(fileName)
        self._loopsFile = fileName
        self.panel().buttonBox.button(QtGui.QDialogButtonBox.Ok).\
                                                               setEnabled(True)

    def selectDiagFile(self):
        fileName = self.selectFile("Diagnostics file chooser")
        if not fileName.rsplit('/',1)[1].startswith('Diag'):
            self.warningMsg("File name structure","The name of the selected "\
                            "file does not starts with 'Diag'")
        self.panel().diagFileName.setText(fileName)
        self._diagFile = fileName
        self.panel().buttonBox.button(QtGui.QDialogButtonBox.Ok).\
                                                               setEnabled(True)

    def selectPlant(self,plant):
        self.info("Selecting the plant: %s"%(str(plant)))
        currentText = self.panel().locationCombo.currentText()
        currentIndex = self.panel().locationCombo.currentIndex()
        self.debug("Current combo text: %s at %d"
                  %(currentText,currentIndex))
        newIndex = self.panel().locationCombo.findText(str(plant))
        if newIndex != currentIndex and currentText != '':
            self.warning("Location has change!!")
            pass#TODO: warn the user about a location change
        elif newIndex == -1: #doesn't exist
            self.panel().locationCombo.addItem(str(plant))
        self.panel().locationCombo.setCurrentIndex(newIndex)
        self.searchFacade()
        #it cannot be smart enough to know that

    def searchFacade(self):
        self.debug("given the known plants (%s) and the current selected "\
                  "plant (%s) which of the found facades (%s) can be?"
                  %(knownPlants,self._plant.completeName,self._facadesFound))
        if self._plant.facadeInstanceName in self._facadesFound:
            self.info("Match found in facade instances: %s"
                      %(self._plant.facadeInstanceName))
            newIndex = self.panel().facadeCombo.findText(\
                                                self._plant.facadeInstanceName)
        else:
            self.warning("Not match found of %s in %s"
                         %(self._plant.facadeInstanceName,self._facadesFound))
            newIndex = -1
        #Alert the user in case something was already selected (by the user
        #or perhaps the different location plant of another file
        currentText = self.panel().locationCombo.currentText()
        currentIndex = self.panel().facadeCombo.currentIndex()
        if newIndex != currentIndex and currentText != '':
            self.warning("facade selection has change!!")
            pass#TODO: warn the user about a location change
        elif newIndex == -1: #doesn't exist
            self.panel().facadeCombo.\
                                   addItem(str(self._plant.facadeInstanceName))
        self.panel().facadeCombo.setCurrentIndex(newIndex)
        
    def getSelection(self):
        selection = {'Loops':self._loopsFile,
                     'Diag':self._diagFile,
                     'plant':self._plant.completeName,
                     'facade':self._plant.facadeInstanceName,
                     'beamCurrent':self.getBeamCurrent()}
#        selection = {}
#        self.debug("Selection: Loops = %s"%(self._loopsFile))
#        selection['Loops'] = self._loopsFile
#        self.debug("Selection: Diag = %s"%(self._diagFile))
#        selection['Diag'] = self._diagFile
#        self.debug("Selection: plant = %s"%(self._plant.completeName))
#        selection['plant'] = self._plant.completeName
#        self.debug("Selection: facade = %s"%(self._plant.facadeInstanceName))
#        selection['facade'] = self._plant.facadeInstanceName
#        self.debug("Selection: BeamCurrent = %f"%(self.getBeamCurrent()))
#        selection['beamCurrent'] = self.getBeamCurrent()
        
        self.debug("selection: %s"%(selection))
        return selection

    def panel(self):
        return self._panel._ui
    
    def accepted(self):
        self.debug("Accepted call")
        if len(self._loopsFile) == 0 and len(self._diagFile) == 0:
            self.error("cannot accept without any file chosen!")
            return
        self.selectionDone.emit()

    def canceled(self):
        self.debug("Cancelling...")
        self.closeApp.emit()

    def warningMsg(self,title,msg):
        QtGui.QMessageBox.warning(self,title,msg)

    def setupBeamCurrent(self):
        self.panel().beamCurrentValue.setMinimum(1.0)
        self.panel().beamCurrentValue.setMaximum(400.0)
        self.panel().beamCurrentValue.setValue(100.0)
        self.panel().beamCurrentValue.setSuffix(' mA')
        self.setBeamCurrent(self._beamCurrent)
    def setBeamCurrent(self,value):
        self.panel().beamCurrentValue.setValue(value)
    def getBeamCurrent(self):
        try:
            self._beamCurrent = self.panel().beamCurrentValue.value()
        except:
            self.warning("The beam current cannot be readed from the widget: "\
                         "%s"%(e))
        return self._beamCurrent



def main():
    parser = argparse.get_taurus_parser()
    app = TaurusApplication(sys.argv, cmd_line_parser=parser,
                      app_name='ctrfdllrf_fdl', app_version='0.2',
                      org_domain='ALBA', org_name='ALBA')
    options = app.get_command_line_options()
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()