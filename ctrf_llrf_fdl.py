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

#The widgets are stored in a subdirectory and 
#needs to be added to the pythonpath
linacWidgetsPath = os.environ['PWD']+'/widgets'
if not linacWidgetsPath in sys.path:
    sys.path.append(linacWidgetsPath)

from taurus.external.qt import Qt,QtGui,QtCore
from taurus.core.util import argparse,Logger
from taurus.qt.qtgui.application import TaurusApplication
from taurus.qt.qtgui.container import TaurusMainWindow
from taurus.qt.qtgui.base.taurusbase import TaurusBaseComponent
from taurus.qt.qtgui.resource import getIcon, getThemeIcon
from taurus.qt.qtgui.plot import CurveAppearanceProperties
import taurus


from ui_MainView import Ui_FastDataLoggerDLLRF
from fileloader import fileLoader
from FdlFileParser import LoopsFile,DiagnosticsFile,FacadeAttrs
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
        self._activeParser = None
        self._facadaAdjustments = None
        self._facade = None
        self.splashScreen().finish(self)
    def initComponents(self):
        self.setWindowTitle("RF DLLRF FDL Taurus User Interface")
        self.centralwidget = self.ui.generalScrollArea
        self.setCentralWidget(self.centralwidget)
        #Remove the perspectives bar (meaning less in this gui)
        self.perspectivesToolBar.clear()
        #prepare button reactions
        Qt.QObject.connect(self.ui.loadButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self.loadFile)
        Qt.QObject.connect(self.ui.cancelButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self.cancell)
        #Like the button add also the loadFile to the menu
        self.loadFileAction = Qt.QAction(getThemeIcon("document-open"),
                                         'Open Files...',self)
        self.connect(self.loadFileAction, Qt.SIGNAL("triggered()"),
                     self.loadFile)
        self.fileMenu.addAction(self.loadFileAction)#TODO: sort this menu
        self._enableWidgets(True)
        #adjustments on the facade configuration
        self.facadeAction = Qt.QAction('Facade fits',self)
        self.facadeAction.setEnabled(False)
        self.toolsMenu.addAction(self.facadeAction)
        
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
                if self._facade != None:
                    self._facade.cancelFacade()
                event.accept()
            else:
                self.warning("User cancelled the close event!")
                event.ignore()
        else:
            self.info("close event, without pending task: "\
                      "no confirmation required.")
            event.accept()
    
    ####
    #--- Load file section
    def loadFile(self):
        self.info("Load file clicked")
        self._loader = LoadFileDialog(self)
        self._loader.closeApp.connect(self.closeLoaderWidget)
        #Qt.QObject.connect(self._loader,Qt.SIGNAL("closeApp"),self.cancelled)
        self._loader.selectionDone.connect(self.prepare)
        #Qt.QObject.connect(self._loader,Qt.SIGNAL("selectionDone"),
        #                   self.prepare)
        self._loader.show()
    def closeLoaderWidget(self):
        self.info("closeLoaderWidget()")
        self._loader.hide()
        self._loader = None
    def prepare(self):
        self.info("prepare()")
        selection = self._loader.getSelection()
        self.info("prepare(): "%(selection))
        self._loader.hide()
        self._loader = None
        #build a FdlFileParser objects
        self.prepareProgressBar()
        if len(selection['Loops']) > 0:
            self._loopsParser = LoopsFile(selection['Loops'])
            self._loopsParser.step.connect(self.updateProgressBar)
            self._loopsParser.done.connect(self.endProgressBar)
            self._loopsParser.process()
        elif len(selection['Diag']) > 0:
            self._diagParser = DiagnosticsFile(selection['Diag'])
            self._diagParser.step.connect(self.updateProgressBar)
            self._diagParser.done.connect(self.endProgressBar)
            self._diagParser.process()
        #facade and plotting:
        self.facadeManagerBuilder(selection['facade'])
        if self._facade.populateFacadeParams():
            self._facade.doFacadeAdjusments()
        self.plotManagerBuilder()
    def cancell(self):
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
        self.ui.progressBar.setValue(value)
    def endProgressBar(self):
        if (self._loopsParser == None or not self._loopsParser.isProcessing())\
           and\
           (self._diagParser == None  or not  self._diagParser.isProcessing()):
            self._enableWidgets(True)
            self.ui.progressBar.setValue(100)
        #TODO: report the anomalities rate in the statusBar
        self.ui
        self._plotter.doPlots()
        #FIXME: the action to plot should be a reaction to a signal emitted 
        #       when both parsing processes finishes
    #--- done progress bar tools
    ####
    
    ####
    #--- facade information area
    def facadeManagerBuilder(self,instanceName):
        if self._facade != None and self._facade.instanceName != instanceName:
            del self._facade
            self._facade = None
        if self._facade == None:
            self._facade = FacadeManager(instanceName)
        self.facadeAction.setEnabled(True)
        self.connect(self.facadeAction, Qt.SIGNAL("triggered()"),
                     self._facade.doFacadeAdjusments)
    #--- done facade information area
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
        self._plant = None
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
                     'facade':self._plant.facadeInstanceName}
        self.debug("selection: %s"%(selection))
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

class FacadeManager(Logger,Qt.QObject):
    change = QtCore.pyqtSignal()
    def __init__(self,facadeInstanceName):
        Logger.__init__(self)
        Qt.QObject.__init__(self, parent=None)
        self._facadeInstanceName = facadeInstanceName
        self._facadeAdjustments = facadeAdjustments()
        self._facadeAttrWidgets = \
            {'CavityVolts':
                {'m':self._facadeAdjustments._ui.cavityVoltsMValue,
                 'n':self._facadeAdjustments._ui.cavityVoltsNValue}
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
        for field in FacadeAttrs.keys():
            self._fromFacade[field] = {}
            if FacadeAttrs[field].has_key('m') and \
               FacadeAttrs[field].has_key('n'):
                self._fromFacade[field]['m'] = 1
                self._fromFacade[field]['n'] = 0
            #TODO: quadratics

    def populateFacadeParams(self):
        requiresFacadeAdjustments = False
        for field in FacadeAttrs.keys():
            if FacadeAttrs[field].has_key('m') and \
               FacadeAttrs[field].has_key('n'):
                mAttr = FacadeAttrs[field]['m']
                nAttr = FacadeAttrs[field]['n']
                try:
                    m = self.facadeDev[mAttr].value
                    n = self.facadeDev[nAttr].value
                except Exception,e:
                    self.warning("Wasn't possible to get the facade fits: "\
                                 "%s"%(e))
                    #tag it to allow the user to manually adjust
                    requiresFacadeAdjustments = True
                else:
                    self.info("For signal %s: m = %g, n = %g"%(field,m,n))
                    self._fromFacade[field]['m'] = m
                    self._fromFacade[field]['n'] = n
        return requiresFacadeAdjustments

    def doFacadeAdjusments(self):
        if self._facadeAdjustments == None:
            self._facadeAdjustments = facadeAdjustments()
        self._facadeAdjustments.setWindowTitle("Facade's parameters")
        Qt.QObject.connect(self.getOkButton(),
                           Qt.SIGNAL('clicked(bool)'),self.okFacade)
        Qt.QObject.connect(self.getCancelButton(),
                           Qt.SIGNAL('clicked(bool)'),self.cancelFacade)
        #TODO: use _fromFacade to populate widgets
        for field in self._fromFacade.keys():
            m = self._fromFacade[field]['m']
            n = self._fromFacade[field]['n']
            self.debug("Information to the user, signal %s: m = %g, n = %g"
                       %(field,m,n))
            self._facadeAttrWidgets[field]['m'].setValue(m)
            self._facadeAttrWidgets[field]['n'].setValue(n)
        self._facadeAdjustments.show()
    
    def getOkButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                              button(QtGui.QDialogButtonBox.Ok)
    def okFacade(self):
        self.info("New parameters adjusted by hand by the user!")
        for field in self._fromFacade.keys():
            m = float(self._facadeAttrWidgets[field]['m'].value())
            n = float(self._facadeAttrWidgets[field]['n'].value())
            self.info("Changes from the user, signal %s: m = %g, n = %g"
                      %(field,m,n))
            self._fromFacade[field]['m'] = m
            self._fromFacade[field]['n'] = n
        self.change.emit()
        self._facadeAdjustments.hide()
    def getCancelButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                          button(QtGui.QDialogButtonBox.Cancel)
    def cancelFacade(self):
        self.info("Canceled parameter adjusted by hand by the user!")
        self._facadeAdjustments.hide()
    

    def getMandNs(self,signalName):
        if signalName in self._fromFacade.keys():
            if self._fromFacade[signalName].has_key('m') and \
               self._fromFacade[signalName].has_key('n'):
                return (self._fromFacade[signalName]['m'],
                        self._fromFacade[signalName]['n'])
        else:
            return (None,None)#FIXME
    #TODO: couple and offset for quadratic fits

TOTAL_TIME = 411.00#ms

class Plotter(Logger):
    def __init__(self,parent,loopsSignals=None,diagSignals=None):
        Logger.__init__(self)
        self._parent = parent
        self._facade = parent._facade
        self._loops = loopsSignals
        self._diag = diagSignals
        self._facade.change.connect(self.doPlots)
        self._startDisplay = self.startDisplay
        self._endDisplay = self.endDisplay
        self._decimation = self.decimation
        Qt.QObject.connect(self._parent.ui.replotButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self.doPlots)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.startValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.endValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.decimationValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        #Remember to populate this with exactly the same keys than the parsed
        self.SignalPlots = {'CavityVolts':
                            {'plot':self._parent.ui.loops1Plots._ui.topLeft,
                             'curveProperties':CurveAppearanceProperties(
                                                      lColor=Qt.QColor('Blue'))
                            }
                           }
    @property
    def startDisplay(self):
        return self._parent.ui.timeAndDecimation._ui.startValue.value()
    @property
    def endDisplay(self):
        return self._parent.ui.timeAndDecimation._ui.endValue.value()
    @property
    def decimation(self):
        return self._parent.ui.timeAndDecimation._ui.decimationValue.value()
    def doPlots(self):
        self.info("starting plotting procedure")
        self._startDisplay = self.startDisplay
        self._endDisplay = self.endDisplay
        self._decimation = self.decimation
        if self._loops != None:
            self.plotLoops()
        if self._diag != None:
            self.plotDiag()
    
    def plotLoops(self):
        for signalName in self._loops.keys():
            if type(self._loops[signalName]) == list:
                self.warning("Signal %s not ready to be plotted"%(signalName))
            else:
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
                y = self._loops[signalName][startPoint:endPoint:self._decimation]
                x = np.linspace(self._startDisplay,self._endDisplay,y.size)
                signal = {'title':signalName,'x':x,'y':y}
                m,n = self._facade.getMandNs(signalName)
                if m != None and n != None:
                    y = (y-n)/m
                    signal = {'title':signalName,'x':x,'y':y}
                self.SignalPlots[signalName]['plot'].attachRawData(signal,
                               self.SignalPlots[signalName]['curveProperties'])
    def plotDiag(self):
        pass

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