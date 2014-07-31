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
from copy import copy

#The widgets are stored in a subdirectory and 
#needs to be added to the pythonpath
linacWidgetsPath = os.environ['PWD']+'/widgets'
if not linacWidgetsPath in sys.path:
    sys.path.append(linacWidgetsPath)

try:#normal way
    from taurus.external.qt import Qt,QtGui,QtCore
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt,QtGui,QtCore
    from FdlFileParser import MyQtSignal
from taurus.core.util import argparse,Logger
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus.qt.qtgui.base.taurusbase import TaurusBaseComponent
from taurus.qt.qtgui.resource import getIcon, getThemeIcon
from taurus.qt.qtgui.plot import CurveAppearanceProperties
import taurus
from PyTango import DevFailed


from ui_MainView import Ui_FastDataLoggerDLLRF
from fileloader import fileLoader
from FdlFileParser import LoopsFile,DiagnosticsFile
from FdlSignals import SignalFields,y2
from facadeadjustments import facadeAdjustments

FACADES_SERVERNAME = 'LLRFFacade'

class MainWindow(TaurusMainWindow):
    def __init__(self, parent=None):
        TaurusMainWindow.__init__(self)
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
        self.splashScreen().finish(self)
    def initComponents(self):
        self.setWindowTitle("RF DLLRF FDL Taurus User Interface")
        self.centralwidget = self.ui.generalScrollArea
        self.setCentralWidget(self.centralwidget)
        #Remove the perspectives bar (meaning less in this gui)
        self.perspectivesToolBar.clear()
        self.prepareTimeAndDecimation()
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
        #try:#normal way
        #    self.connect(self.loadFileAction, Qt.SIGNAL("triggered()"),
        #                 self.loadFile)
        #except:#backward compatibility to pyqt 4.4.3
        Qt.QObject.connect(self.loadFileAction, Qt.SIGNAL("triggered()"),
                           self.loadFile)
        self.fileMenu.addAction(self.loadFileAction)#TODO: sort this menu
        self._enableWidgets(True)
        #adjustments on the facade configuration
        self.facadeAction = Qt.QAction('Facade fits',self)
        self.facadeAction.setEnabled(False)
        self.toolsMenu.addAction(self.facadeAction)
    
    def prepareTimeAndDecimation(self):
        #start Value
        self.ui.timeAndDecimation._ui.startValue.setMinimum(0.0)
        self.ui.timeAndDecimation._ui.startValue.setMaximum(411.0)
        self.ui.timeAndDecimation._ui.startValue.setSuffix(' ms')
        self.ui.timeAndDecimation._ui.startValue.setMinimumWidth(100)
        #endValue
        self.ui.timeAndDecimation._ui.endValue.setMinimum(0.0)
        self.ui.timeAndDecimation._ui.endValue.setMaximum(411.0)
        self.ui.timeAndDecimation._ui.endValue.setSuffix(' ms')
        self.ui.timeAndDecimation._ui.endValue.setValue(411.0)
        #decimation
        self.ui.timeAndDecimation._ui.decimationValue.setMinimum(1)
        self.ui.timeAndDecimation._ui.decimationValue.setMaximum(1000)
        self.ui.timeAndDecimation._ui.decimationValue.setValue(1)
        #progress bar initial value
        self.ui.progressBar.setValue(100)
    
    def _enableWidgets(self,enable):
        #buttons
        self.ui.loadButton.setEnabled(enable)
        if enable:
            self.ui.cancelButton.hide()
        else:
            self.ui.cancelButton.show()
        #self.ui.cancelButton.setEnabled(not enable)
        self.ui.replotButton.setEnabled(enable)
        #progressBar
        self.ui.progressBar.setEnabled(not enable)
        #configuration integers
        #self.ui.timeAndDecimation._ui.startValue.setEnabled(enable)
        #self.ui.timeAndDecimation._ui.endValue.setEnabled(enable)
        #self.ui.timeAndDecimation._ui.decimationValue.setEnabled(enable)
        
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
        self.info("Load file clicked")
        if self._loader == None:
            self._loader = LoadFileDialog(self)
            try:#normal way
                self._loader.closeApp.connect(self.closeLoaderWidget)
            except:#backward compatibility to pyqt 4.4.3
                self.warning("Connecting closeApp in the old way")
                Qt.QObject.connect(self._loader,
                                   Qt.SIGNAL("closeApp"),
                                   self.closeLoaderWidget)
            try:#normal way
                self._loader.selectionDone.connect(self.prepare)
            except:#backward compatibility to pyqt 4.4.3
                self.warning("Connecting selectionDone in the old way")
                Qt.QObject.connect(self._loader,Qt.SIGNAL("selectionDone"),
                                   self.prepare)
        self._loader.show()
    def closeLoaderWidget(self):
        self.info("closeLoaderWidget()")
        self._loader.hide()
        self._loader = None
    def prepare(self):
        selection = self._loader.getSelection()
        self.info("prepare(): %s"%(str(selection)))
        self._loader.hide()
        #build a FdlFileParser objects
        self.prepareProgressBar()
        if len(selection['Loops']) > 0:
            self._loopsParser = LoopsFile(selection['Loops'])
            try:#normal way
                self._loopsParser.step.connect(self.updateProgressBar)
            except:#backward compatibility to pyqt 4.4.3
                Qt.QObject.connect(self._loopsParser,
                                   Qt.SIGNAL('step'),
                                   self.updateProgressBar)
            try:#normal way
                self._loopsParser.done.connect(self.endProgressBar)
            except:#backward compatibility to pyqt 4.4.3
                Qt.QObject.connect(self._loopsParser,
                                   Qt.SIGNAL('done'),
                                   self.endProgressBar)
            self._loopsParser.process()
        if len(selection['Diag']) > 0:
            self._diagParser = DiagnosticsFile(selection['Diag'])
            try:#normal way
                self._diagParser.step.connect(self.updateProgressBar)
            except:#backward compatibility to pyqt 4.4.3
                Qt.QObject.connect(self._diagParser,
                                   Qt.SIGNAL('step'),
                                   self.updateProgressBar)
            try:#normal way
                self._diagParser.done.connect(self.endProgressBar)
            except:#backward compatibility to pyqt 4.4.3
                Qt.QObject.connect(self._diagParser,
                                   Qt.SIGNAL('done'),
                                   self.endProgressBar)
            self._diagParser.process()
        #facade and plotting:
        self.facadeManagerBuilder(selection['facade'],selection['beamCurrent'])
        if self._facade.populateFacadeParams():
            self._facade.doFacadeAdjusments()
        self.signalProcessorBuilder()
        self.plotManagerBuilder()
        self._loader = None
    def cancel(self):
        if self._loopsParser != None:
            self._loopsParser.abort()
        if self._diagParser != None:
            self._diagParser.abort()
        self._enableWidgets(True)
    #--- done load file section
    ####
    
    ####
    #--- progress bar tools
    def prepareProgressBar(self):
        self._enableWidgets(False)
        self.ui.progressBar.setValue(0)
    def updateProgressBar(self):
        value = 0
        if self._loopsParser != None:
            value = self._loopsParser.percentage
        if self._diagParser != None:
            if value != 0:
                value = (value+self._diagParser.percentage)/2
            else:
                value = self._diagParser.percentage
        self.debug("new progress bar value %g"%(value))
        self.ui.progressBar.setValue(int(value))
    def endProgressBar(self):
        if (self._loopsParser == None or not self._loopsParser.isProcessing())\
           and\
           (self._diagParser == None  or not  self._diagParser.isProcessing()):
            self._enableWidgets(True)
            self.ui.progressBar.setValue(100)
        #TODO: report the anomalities rate in the statusBar
        #...
        #postprocess
        self._postProcessor.process()
        #FIXME: report the user if something wasn't possible to be calculated
        #plotting:
        self._plotter.doPlots(force=True)
        #FIXME: the action to plot should be a reaction to a signal emitted 
        #       when both parsing processes finishes
    #--- done progress bar tools
    ####
    
    ####
    #--- facade information area
    def facadeManagerBuilder(self,instanceName,beamCurrent):
        if self._facade != None and self._facade.instanceName != instanceName:
            del self._facade
            self._facade = None
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
        if self._loopsParser != None:
            loopsSignals=self._loopsParser._signals
        else:
            loopsSignals=None
        if self._diagParser != None:
            diagSignals=self._diagParser._signals
        else:
            diagSignals=None
        self._postProcessor = SignalProcessor(self,loopsSignals,diagSignals)
    #---
    ####

    ####
    #--- plotting section
    def plotManagerBuilder(self):
        if self._loopsParser != None:
            loopsSignals=self._loopsParser._signals
        else:
            loopsSignals=None
        if self._diagParser != None:
            diagSignals=self._diagParser._signals
        else:
            diagSignals=None
        self._plotter = Plotter(self,loopsSignals,diagSignals)
    #--- done plotting section
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
        self.info("Selected: %s"%(fileName))
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
        self.info("Current combo text: %s at %d"
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
        self.info("given the known plants (%s) and the current selected "\
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
        
        self.info("selection: %s"%(selection))
        return selection

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

class FacadeManager(Logger,Qt.QObject):
    try:#normal way
        change = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        change = MyQtSignal('change')
    def __init__(self,facadeInstanceName,beamCurrent=100):
        Logger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.change._parent = self
        self._facadeInstanceName = facadeInstanceName
        self._facadeAdjustments = facadeAdjustments()
        self._beamCurrent = beamCurrent#mA
        self._facadeAttrWidgets = \
            {'CavVolt_mV':
                {'m':self._facadeAdjustments._ui.cavityVolts_mV_MValue,
                 'n':self._facadeAdjustments._ui.cavityVolts_mV_NValue},
             'CavVolt_kV':
                {'m':self._facadeAdjustments._ui.cavityVolts_kV_MValue,
                 'n':self._facadeAdjustments._ui.cavityVolts_kV_NValue},
             'FwCav_kW':
                {'c':self._facadeAdjustments._ui.FwCavCValue,
                 'o':self._facadeAdjustments._ui.FwCavOValue},
             'RvCav_kW':
                {'c':self._facadeAdjustments._ui.RvCavCValue,
                 'o':self._facadeAdjustments._ui.RvCavOValue}
            }
        try:
            dServerName = str('dserver/'+\
                              FACADES_SERVERNAME+'/'+\
                              facadeInstanceName)
            self.debug("Facade's device server name: %s"%(dServerName))
            facadeDevName = taurus.Device(dServerName).\
                                          QueryDevice()[0].split('::')[1]
            self.debug("Facade's device name: %s"%(facadeDevName))
            self.facadeDev = taurus.Device(facadeDevName)
        except Exception,e:
            self.error("Cannot prepare the facade information due to an "\
                       "exception: %s"%(e))
            return
        self._prepareFacadeParams()

    @property
    def instanceName(self):
        return self._facadeInstanceName

    def _prepareFacadeParams(self):
        self._fromFacade = {}
        for field in SignalFields.keys():
            self._fromFacade[field] = {}
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key('m') and \
               SignalFields[field].has_key('n'):
                self._fromFacade[field]['m'] = 1
                self._fromFacade[field]['n'] = 0
            elif SignalFields[field].has_key('c') and \
                 SignalFields[field].has_key('o'):
                self._fromFacade[field]['c'] = 1
                self._fromFacade[field]['o'] = 0
            #TODO: quadratics

    def populateFacadeParams(self):
        requiresFacadeAdjustments = False
        for field in SignalFields.keys():
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key('m') and \
               SignalFields[field].has_key('n'):
                mAttr = SignalFields[field]['m']
                nAttr = SignalFields[field]['n']
                m = self.readAttr(mAttr)
                n = self.readAttr(nAttr)
                if m != None and n != None:
                    self.info("For signal %s: m = %g, n = %g"%(field,m,n))
                    self._fromFacade[field]['m'] = m
                    self._fromFacade[field]['n'] = n
                else:
                    requiresFacadeAdjustments = True
            elif SignalFields[field].has_key('c') and \
                 SignalFields[field].has_key('o'):
                cAttr = SignalFields[field]['c']
                oAttr = SignalFields[field]['o']
                c = self.readAttr(cAttr)
                o = self.readAttr(oAttr)
                if c != None and o != None:
                    self.info("For signal %s: c = %g, o = %g"%(field,c,o))
                    self._fromFacade[field]['c'] = c
                    self._fromFacade[field]['o'] = o
                else:
                    requiresFacadeAdjustments = True
        return requiresFacadeAdjustments

    def readAttr(self,attrName):
        try:
            return self.facadeDev[attrName].value
        except DevFailed,e:
            if len(e.args) == 2:
                msg = e[1].desc
            else:
                msg = e[0].desc
            self.warning("Not possible to read %s's value (%s)"%(attrName,msg))
        except Exception,e:
            self.error("Wasn't possible to get the facade's attribute %s: "\
                                 "%s"%(attrName,e))
        return None

    def doFacadeAdjusments(self):
        if self._facadeAdjustments == None:
            self._facadeAdjustments = facadeAdjustments()
        self._facadeAdjustments.setWindowTitle("Facade's parameters")
        Qt.QObject.connect(self.getOkButton(),
                           Qt.SIGNAL('clicked(bool)'),self.okFacade)
        Qt.QObject.connect(self.getCancelButton(),
                           Qt.SIGNAL('clicked(bool)'),self.cancelFacade)
#        self.prepareBeamCurrent()
        #use _fromFacade to populate widgets
        for field in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[field].has_key('m') and \
               self._fromFacade[field].has_key('n'):
                m = self._fromFacade[field]['m']
                n = self._fromFacade[field]['n']
                self.debug("Information to the user, signal %s: m = %g, n = %g"
                           %(field,m,n))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field]['m'].setValue(m)
                    self._facadeAttrWidgets[field]['n'].setValue(n)
            if self._fromFacade[field].has_key('c') and \
               self._fromFacade[field].has_key('o'):
                c = self._fromFacade[field]['c']
                o = self._fromFacade[field]['o']
                self.debug("Information to the user, signal %s: c = %g, o = %g"
                           %(field,c,o))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field]['c'].setValue(c)
                    self._facadeAttrWidgets[field]['o'].setValue(o)
        self._facadeAdjustments.show()
    
#    def prepareBeamCurrent(self):
#        self._facadeAdjustments._ui.beamCurrentValue.setValue(self._beamCurrent)
    def getBeamCurrent(self):
#        try:
#            if self._beamCurrent != self._facadeAdjustments._ui.\
#                                                      beamCurrentValue.value():
#                self._beamCurrent = self._facadeAdjustments._ui.\
#                                                       beamCurrentValue.value()
#        except Exception,e:
#            self.warning("Error getting the beam current: %s"%(e))
        return self._beamCurrent
    
    def getOkButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                              button(QtGui.QDialogButtonBox.Ok)
    def okFacade(self):
        #self.info("New parameters adjusted by hand by the user!")
#        self.getBeamCurrent()
        hasAnyoneChanged = False
        for field in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[field].has_key('m') and \
               self._fromFacade[field].has_key('n'):
                m = float(self._facadeAttrWidgets[field]['m'].value())
                n = float(self._facadeAttrWidgets[field]['n'].value())
                if self._fromFacade[field]['m'] != m or \
                   self._fromFacade[field]['n'] != n:
                    self.info("Changes from the user, signal %s: m = %g, n = %g"
                              %(field,m,n))
                    self._fromFacade[field]['m'] = m
                    self._fromFacade[field]['n'] = n
                    hasAnyoneChanged = True
            elif self._fromFacade[field].has_key('c') and \
                 self._fromFacade[field].has_key('o'):
                c = float(self._facadeAttrWidgets[field]['c'].value())
                o = float(self._facadeAttrWidgets[field]['o'].value())
                if self._fromFacade[field]['c'] != c or \
                   self._fromFacade[field]['o'] != o:
                    self.info("Changes from the user, signal %s: c = %g, o = %g"
                              %(field,c,o))
                    self._fromFacade[field]['c'] = c
                    self._fromFacade[field]['o'] = o
                    hasAnyoneChanged = True
        if hasAnyoneChanged:
            self.change.emit()
        self._facadeAdjustments.hide()
    def getCancelButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                          button(QtGui.QDialogButtonBox.Cancel)
    def cancelFacade(self):
        self.info("Canceled parameter adjusted by hand by the user!")
        if hasattr(self,'_facadeAdjustments') and \
           self._facadeAdjustments != None:
            self._facadeAdjustments.hide()
            self._facadeAdjustments = None

    def getMandNs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key('m') and \
               self._fromFacade[signalName].has_key('n'):
                return (self._fromFacade[signalName]['m'],
                        self._fromFacade[signalName]['n'])
        else:
            raise Exception("signal %s hasn't M&N's"%(signalName))

    def getCandOs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key('c') and \
               self._fromFacade[signalName].has_key('o'):
                return (self._fromFacade[signalName]['c'],
                        self._fromFacade[signalName]['o'])
        else:
            return (None,None)#FIXME

class SignalProcessor(Logger,Qt.QObject):
    try:#normal way
        change = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        change = MyQtSignal('change')
    def __init__(self,parent,loopsSignals=None,diagSignals=None):
        Logger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.change._parent = self
        self._parent = parent
        self._facade = parent._facade
        self._loops = loopsSignals
        self._diag = diagSignals
        try:#normal way
            self._facade.change.connect(self.process)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.connect(self._facade,
                               Qt.SIGNAL('change'),
                               self.process)
    def process(self):
        '''collect all signal keys splitting in 3 categories
           1.- pure file signals
           2.- facade fits
           3.- formulas
               3.1.- sort by dependencies
           do the calculation for the facade fit signals
           do the calculation of the formulas
        '''
        #TODO: perhaps the progress bar can be be also used.
        doneSignals = []
        facadeSignals = []
        formulaSignals = []
        orphaneSignals = []
        for signal in SignalFields.keys():
            if self.isFileSignal(signal):
                doneSignals.append(signal)
            elif self.isLinear(signal) or self.isQuadratic(signal):
                facadeSignals.append(signal)
            elif self.isFormula(signal):
                formulaSignals.append(signal)
            else:
                orphaneSignals.append(signal)
        self.debug("nothing to do with the %d pure file signals: %s"
                   %(len(doneSignals),doneSignals))
        self.debug("%d signals to be calculated using facade parameters: %s"
                   %(len(facadeSignals),facadeSignals))
        self.debug("%d signals to be calculated using a formula: %s"
                   %(len(formulaSignals),formulaSignals))
        self.warning("%d orphane signals: %s"
                     %(len(orphaneSignals),orphaneSignals))
        lastPendingFacadeSignals = [0]*len(facadeSignals)+[len(facadeSignals)]
        #FIXME: refactoring those two loops, they are now almost the same
        while facadeSignals != [] and len(set(lastPendingFacadeSignals)) != 1:
            signal = facadeSignals[0]
            try:
                dependencies = [SignalFields[signal]['x']]#Diff with formula
                unsatisfied = list(set(dependencies).difference(doneSignals))
                if len(unsatisfied) == 0:
                    try:
                        self.calculate(signal)
                        facadeSignals.pop(facadeSignals.index(signal))
                        doneSignals.append(signal)
                    except Exception,e:
                        self.error("Exception calculating %s: %s"%(signal,e))
                    else:
                        self.debug("%d signals calculated: %s"
                                   %(len(doneSignals),doneSignals))
                else:
                    #move to the last to retry
                    facadeSignals.append(facadeSignals.pop(0))
                    self.warning("formula signal %s cannot be yet calculated "\
                                 "due to unsatisfied %s"%(signal,unsatisfied))
            except Exception,e:
                self.error("Exception with %s dependencies: %s"%(signal,e))
                break
            else:
                lastPendingFacadeSignals.pop(0)
                lastPendingFacadeSignals.append(len(facadeSignals))
                self.debug("Three last loops formula pernding signals: %s"
                           %(lastPendingFacadeSignals))
        lastPendingFormulaSignals = [0]*len(formulaSignals)+[len(formulaSignals)]
        while formulaSignals != [] and \
              len(set(lastPendingFormulaSignals)) != 1:
            #while there are pending elements or 
            #last 3 loops didn't reduce the list
            signal = formulaSignals[0]
            try:
                dependencies = SignalFields[signal]['d']
                unsatisfied = list(set(dependencies).difference(doneSignals))
                if len(unsatisfied) == 0:
                    try:
                        self.calculate(signal)
                        formulaSignals.pop(formulaSignals.index(signal))
                        doneSignals.append(signal)
                    except Exception,e:
                        self.error("Exception calculating %s: %s"%(signal,e))
                else:
                    #move to the last to retry
                    formulaSignals.append(formulaSignals.pop(0))
                    self.warning("formula signal %s cannot be yet calculated "\
                                 "due to unsatisfied %s"%(signal,unsatisfied))
            except Exception,e:
                self.error("Exception with %s dependencies: %s"%(signal,e))
                break
            else:
                lastPendingFormulaSignals.pop(0)
                lastPendingFormulaSignals.append(len(formulaSignals))
                self.debug("Three last loops formula pernding signals: %s"
                           %(lastPendingFormulaSignals))
        if len(set(lastPendingFormulaSignals)) == 1:
            self.error("process has not finished well. There are pending "\
                       "calculations: %s"%(formulaSignals))
            return False
        self.change.emit()
        return True
    def calculate(self,signal):
        if self.isLinear(signal):
            self.info("Calculating linear fit on %s signal"%(signal))
            m,n = self._facade.getMandNs(signal)
            handler = self.getSignalHandler(signal)
            handler[signal] = (handler[SignalFields[signal]['x']]- n)/m
        elif self.isQuadratic(signal):
            self.info("Calculating quadratic fit on %s signal"%(signal))
            c,o = self._facade.getCandOs(signal)
            handler = self.getSignalHandler(signal)
            handler[signal] = \
                       (handler[SignalFields[signal]['x']]**2/10e8/10**c-o)
        elif self.isFormula(signal):
            self.info("Calculating %s using formula %s"
                      %(signal,SignalFields[signal]['f']))
            sources = self.mergeHandlers()
            #self.debug("Data sources: %s"%(sources.keys()))
            handler = self.getSignalHandler(signal)
            try:
                beamCurrent = self._facade.getBeamCurrent()
                handler[signal] = eval(SignalFields[signal]['f'],
                                   {'arcsin':np.arcsin,'pi':np.pi,
                                    'BeamCurrent':beamCurrent},
                                   sources)
            except RuntimeWarning,e:
                self.warning("Warning in %s eval: %s"%(signal,e))
            except Exception,e:
                self.error("Exception in %s eval: %s"%(signal,e))
        else:
            self.info("nothing to do with %s signal"%(signal))
            return
        self.debug("Made the calculation for the signal %s (%d values)"
                   %(signal,len(handler[signal])))
    
    def getSignalHandler(self,signal):
        #FIXME: these ifs needs a refactoring
        if self.isLinear(signal) or self.isQuadratic(signal):
            if self._loops.has_key(SignalFields[signal]['x']) :
                return self._loops
            elif self._diag.has_key(SignalFields[signal]['x']):
                return self._diag
        elif self.isFormula(signal):
            if SignalFields[signal]['h'] == 'loops':
                return self._loops
            elif SignalFields[signal]['h'] == 'diag':
                return self._diag
        else:
            return None#FIXME
    def mergeHandlers(self):
        if self._loops != None:
            merged = copy(self._loops)
        else:
            merged = {}
        if self._diag != None:
            merged.update(self._diag)
        return merged
    def isFileSignal(self,signal):
        return SignalFields[signal].has_key('I') and \
               SignalFields[signal].has_key('Q')
    def isLinear(self,signal):
        return SignalFields[signal].has_key('x') and \
               SignalFields[signal].has_key('m') and \
               SignalFields[signal].has_key('n')
    def isQuadratic(self,signal):
        return SignalFields[signal].has_key('x') and \
               SignalFields[signal].has_key('c') and \
               SignalFields[signal].has_key('o')
    def isFormula(self,signal):
        return SignalFields[signal].has_key('f') and \
               SignalFields[signal].has_key('h')

TOTAL_TIME = 411.00#ms
#TODO: It's assumend that all the files have the same time, when what would 
# be assumed if that each sample set has a fix size in time.
#pointTime = 0.000195981#ms 
#totalTime = pointTime*self._loops[signalName].size

class Plotter(Logger):
    def __init__(self,parent,loopsSignals=None,diagSignals=None):
        Logger.__init__(self)
        self._parent = parent
        self._processor = parent._postProcessor
        self._loops = loopsSignals
        self._diag = diagSignals
        try:#normal way
            self._processor.change.connect(self.forcePlot)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.connect(self._processor,
                               Qt.SIGNAL('change'),
                               self.forcePlot)
        self._startDisplay = self.startDisplay
        self._endDisplay = self.endDisplay
        self._decimation = self.decimation
        Qt.QObject.connect(self._parent.ui.replotButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self.forcePlot)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.startValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.endValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.decimationValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        #once created the object and with access to the patent's widgets
        #a map with the locations can be set up
        loops1 = self._parent.ui.loops1Plots._ui
        loops2 = self._parent.ui.loops2Plots._ui
        diag = self._parent.ui.diagnosticsPlots._ui
        self._widgetsMap = {'Loops1':{'topLeft':loops1.topLeft,
                                      'topRight':loops1.topRight,
                                      'middleLeft':loops1.middleLeft,
                                      'middleRight':loops1.middleRight,
                                      'bottomLeft':loops1.bottomLeft,
                                      'bottomRight':loops1.bottomRight},
                            'Loops2':{'topLeft':loops2.topLeft,
                                      'topRight':loops2.topRight,
                                      'middleLeft':loops2.middleLeft,
                                      'middleRight':loops2.middleRight,
                                      'bottomLeft':loops2.bottomLeft,
                                      'bottomRight':loops2.bottomRight},
                            'Diag':{'topLeft':diag.topLeft,
                                    'topRight':diag.topRight,
                                    'middleUpLeft':diag.middleUpLeft,
                                    'middleUpRight':diag.middleUpRight,
                                    'middleDownLeft':diag.middleDownLeft,
                                    'middleDownRight':diag.middleDownRight,
                                    'bottomLeft':diag.bottomLeft,
                                    'bottomRight':diag.bottomRight}
                            }
        #Those locations must correspond with FdlFileParser.SignalFields
        #within each signal the key 'gui' must have a 'tab' and 'plot' keys
        #that indicates a widget on this dictionary
        
        
#        #Remember to populate this with exactly the same keys than the parsed
#        self.SignalPlots = {'CavityVolts':
#                            {'plot':self._parent.ui.loops1Plots._ui.topLeft,
#                             'curveProperties':CurveAppearanceProperties(
#                                                      lColor=Qt.QColor('Blue'))
#                            }
#                           }
    @property
    def startDisplay(self):
        return self._parent.ui.timeAndDecimation._ui.startValue.value()
    @property
    def startDisplayChange(self):
        '''Compare in-class stored value and widget value
        '''
        self.debug("startDisplayChange: %s,%s"
                   %(self._startDisplay,self.startDisplay))
        hasChanged = self._startDisplay != self.startDisplay
        if hasChanged:
            self.debug("StartDisplay value has changed")
        self._startDisplay = self.startDisplay
        return hasChanged
    @property
    def endDisplay(self):
        return self._parent.ui.timeAndDecimation._ui.endValue.value()
    @property
    def endDisplayChange(self):
        '''Compare in-class stored value and widget value
        '''
        self.debug("endDisplayChange: %s,%s"
                   %(self._endDisplay,self.endDisplay))
        hasChanged = self._endDisplay != self.endDisplay
        if hasChanged:
            self.debug("EndDisplay value has changed")
        self._endDisplay = self.endDisplay
        return hasChanged
    @property
    def decimation(self):
        return self._parent.ui.timeAndDecimation._ui.decimationValue.value()
    @property
    def decimationChange(self):
        '''Compare in-class stored value and widget value
        '''
        self.debug("decimationChange: %s,%s"
                   %(self._decimation,self.decimation))
        hasChanged = self._decimation != self.decimation
        if hasChanged:
            self.debug("Decimation value has changed")
        self._decimation = self.decimation
        return hasChanged
    def doPlots(self,force=False):
        isNeeded = force or self.startDisplayChange or \
                            self.endDisplayChange   or \
                            self.decimationChange
        if isNeeded:
            self.forcePlot()
        else:
            self.debug("ignore plotting because it hasn't change")
    
    def forcePlot(self):
        self.debug("starting plotting procedure")
        if self._loops != None:
            self.plotLoops()
        if self._diag != None:
            self.plotDiag()
    
    def plotLoops(self):
        self.debug("preparing to plot 'Loops': %s"%(self._loops.keys()))
        for signalName in self._loops.keys():
            if type(self._loops[signalName]) == list:
                self.warning("Signal %s not ready to be plotted"%(signalName))
            elif not SignalFields[signalName].has_key('gui'):
                self.debug("Signal %s is not configured to be plotted."
                           %(signalName))
            else:
                self.debug("Signal %s will be plotted"%(signalName))
                try:
                    #cut the incomming signal by the [start:end] delimiters
                    pointTime = TOTAL_TIME/self._loops[signalName].size
                    self.debug("Each sample point means %g ms (%d points)"
                              %(pointTime,self._loops[signalName].size))
                    startPoint = int(self._startDisplay/pointTime)
                    self.debug("With a start display at %g ms, "\
                              "point %d the first displayed"
                              %(self._startDisplay,startPoint))
                    endPoint = int(self._endDisplay/pointTime)
                    self.debug("With a end display at %g ms, "\
                              "point %d the last displayed"
                              %(self._endDisplay,endPoint))
                    y = self._loops[signalName]\
                                         [startPoint:endPoint:self._decimation]
                    x = np.linspace(self._startDisplay,self._endDisplay,y.size)
                    signal = {'title':signalName,'x':x,'y':y}
                    tab = SignalFields[signalName]['gui']['tab']
                    plot = SignalFields[signalName]['gui']['plot']
                    color = SignalFields[signalName]['gui']['color']
                    axis =  SignalFields[signalName]['gui']['axis']
                    curveProp = CurveAppearanceProperties(\
                                                       lColor=Qt.QColor(color),
                                                                    yAxis=axis)
                    self._widgetsMap[tab][plot].attachRawData(signal,curveProp)
                    if axis == y2:
                        self._widgetsMap[tab][plot].autoShowYAxes()
                except Exception,e:
                    self.error("Exception plotting %s: %s"%(signalName,e))
    def plotDiag(self):
        self.debug("preparing to plot 'Diag': %s"%(self._diag.keys()))
        for signalName in self._diag.keys():
            if type(self._diag[signalName]) == list:
                self.warning("Signal %s not ready to be plotted"%(signalName))
            elif not SignalFields[signalName].has_key('gui'):
                self.debug("Signal %s is not configured to be plotted."
                           %(signalName))
            else:
                self.debug("Signal %s will be plotted"%(signalName))
                try:
                    #cut the incomming signal by the [start:end] delimiters
                    pointTime = TOTAL_TIME/self._diag[signalName].size
                    self.debug("Each sample point means %g ms (%d points)"
                              %(pointTime,self._diag[signalName].size))
                    startPoint = int(self._startDisplay/pointTime)
                    self.debug("With a start display at %g ms, "\
                              "point %d the first displayed"
                              %(self._startDisplay,startPoint))
                    endPoint = int(self._endDisplay/pointTime)
                    self.debug("With a end display at %g ms, "\
                              "point %d the last displayed"
                              %(self._endDisplay,endPoint))
                    y = self._diag[signalName]\
                                         [startPoint:endPoint:self._decimation]
                    x = np.linspace(self._startDisplay,self._endDisplay,y.size)
                    signal = {'title':signalName,'x':x,'y':y}
                    tab = SignalFields[signalName]['gui']['tab']
                    plot = SignalFields[signalName]['gui']['plot']
                    color = SignalFields[signalName]['gui']['color']
                    axis =  SignalFields[signalName]['gui']['axis']
                    curveProp = CurveAppearanceProperties(\
                                                       lColor=Qt.QColor(color),
                                                                    yAxis=axis)
                    self._widgetsMap[tab][plot].attachRawData(signal,curveProp)
                except Exception,e:
                    self.error("Exception plotting %s: %s"%(signalName,e))

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