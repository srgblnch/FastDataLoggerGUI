###############################################################################
## file :               FdlPlotter.py
##
## description :        This file has been made to provide interface FDL files.
##
## project :            Taurus
##
## author(s) :          S.Blanch-Torn\'e
##
## Copyright (C) :      2014
##                      CELLS / ALBA Synchrotron,
##                      08290 Bellaterra,
##                      Spain
##
## This file is part of Taurus.
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
## along with Taurus.  If not, see <http:##www.gnu.org/licenses/>.
##
###############################################################################

from FdlLogger import *
from FdlSignals import *

try:#normal way
    from taurus.external.qt import Qt,QtGui,QtCore
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt,QtGui

from taurus.qt.qtgui.plot import CurveAppearanceProperties
import numpy as np
import threading
import time
import traceback

DecimationThreshold = 100

class Plotter(FdlLogger,Qt.QWidget):
    '''This class is responsible to plot in the gui a set of signals it 
       receives. The signals can be from the loops set or (exclusive) from the
       diagnostics set.
       With the signal information this class, using the sampling rate of loops
       and diagnostics, will calculate the range of the data in time space and 
       the lower level of the decimation (to avoid memory issues).
    '''
    ####
    #--- QtSignals area
    # The onePlotted and allPlotted are used to communicate with the MainWindow
    # the information about the plotting progress.
    try:#normal way
        onePlotted = QtCore.pyqtSignal()
        allPlotted = QtCore.pyqtSignal()
        #swapping = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        onePlotted = MyQtSignal('onePlotted')
        allPlotted = MyQtSignal('allPlotted')
        #swapping = MyQtSignal('swapping')
    #--- done qtSignals
    ####
    
    def __init__(self,parent=None):
        FdlLogger.__init__(self)
        try:#normal way
            Qt.QWidget.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QWidget.__init__(self)
            self.onePlotted._parent = self
            self.allPlotted._parent = self
            #self.swapping._parent = self
        self._parent = parent
        self.cleanSignals()
        self._buttonSignalsDone = False

    ####
    #--- Signal's data area
    def cleanSignals(self):
        #Dictionary with np.arrays where each key means a signal to be plotted
        #ranges array is 3 element [min,max,decimation]
        self._globalRanges = [None]*3
        self._loopsSignals = {}
        self._loopsRanges = [None]*3
        self._diagSignals = {}
        self._diagRanges = [None]*3

    def appendSignals(self,signalsSet):
        '''Given a dictionary with the signals names as key and its np.arrays 
           as values, introduce them in the class to plot them.
           In case a key already exist, it's contents will be updated with the 
           new value.
        '''
        if type(signalsSet) == dict:
            for signalName in signalsSet:
                if self._isPlottableSignal(signalName):
                    self._addSignal(signalName,signalsSet[signalName])
        if len(self._loopsSignals.keys()) != 0:
            self._loopsRanges = self.calculateRanges('loops')
            self.debug("Ranges for loops [min,max,dec] = %s"
                       %(self._loopsRanges))
        if len(self._diagSignals.keys()) != 0:
            self._diagRanges = self.calculateRanges('diag')
            self.debug("Ranges for diagnostics [min,max,dec] = %s"
                       %(self._diagRanges))
        self.prepareTimeAndDecimation()
        self.debug("Global ranges [min,max,dec] = %s"%(self._globalRanges))

    def _addSignal(self,signalName,signalValue):
        if signalName in self._loopsSignals.keys() + self._diagSignals.keys():
            #check if it's already there
            self.warning("append %s when already exist. Updating "\
                         "with new data provided."%(signalName))
        if type(signalValue) != list:
            #list is when data is not ready, but it's cheaper than
            #compare it it's some kind of np.array
            #FIXME: would be isinstance(signalValue,np.ndarray) ?
            if self._isLoopsSignal(signalName):
                self.debug("Adding %s signal, and tag as loops (%d samples)"
                           %(signalName,len(signalValue)))
                self._loopsSignals[signalName] = signalValue
            elif self._isDiagnosticsSignal(signalName):
                self.debug("Adding %s signal, and tag as diagnostics "\
                           "(%d samples)"%(signalName,len(signalValue)))
                self._diagSignals[signalName] = signalValue
            else:
                return#don't append the signal if it's not loops or diag
    # done signal's data area
    ####
    
    ####
    #--- Range's area
    def prepareTimeAndDecimation(self):
        #select the global min max and decimation 
        #(being the decimation the smallest case)
        self._globalRanges[0] = np.min([self._loopsRanges[0],self._diagRanges[0]])
        self._globalRanges[1] = np.max([self._loopsRanges[1],self._diagRanges[1]])
        self._globalRanges[2] = np.max([self._loopsRanges[2],self._diagRanges[2]])
        if hasattr(self._parent,'ui'):
            if hasattr(self._parent.ui,'timeAndDecimation'):
                #start
                startValue = self._parent.ui.timeAndDecimation._ui.startValue
                self.setWidgetRanges(startValue,self._globalRanges[0],
                                                self._globalRanges[1],
                                                self._globalRanges[0])
                self.connectSpinBox(startValue, self.doPlots)
                self._startDisplay = self.startDisplayWidgetValue
                #end
                endValue = self._parent.ui.timeAndDecimation._ui.endValue
                self.setWidgetRanges(endValue,self._globalRanges[0],
                                              self._globalRanges[1],
                                              self._globalRanges[1])
                self.connectSpinBox(endValue, self.doPlots)
                self._endDisplay = self.endDisplayWidgetValue
                #decimation
                decimationValue = self._parent.ui.timeAndDecimation._ui.\
                                                                decimationValue
                self.setWidgetRanges(decimationValue,self._globalRanges[1],
                                                     1000,
                                                     self._globalRanges[1])
                self.connectSpinBox(decimationValue, self.doPlots)
                self._decimation = self.decimationWidgetValue
                #replot
                if not self._buttonSignalsDone:
                    self.connectButton(self._parent.ui.replotButton,
                                       self._forcePlot)
                    self._buttonSignalsDone = True

    def calculateRanges(self,signalType):
        if signalType.lower() == 'loops':
            signals = self._loopsSignals
            ranges = self._loopsRanges
            SampleTime = LoopsSampleTime
        elif signalType.lower() == 'diag':
            signals = self._diagSignals
            ranges = self._diagRanges
            SampleTime = DiagSampleTime
        else:
            return [None]*3
        listOfSizes = [len(signals[x]) for x in signals.keys()]
        if len(set(listOfSizes))==1:#all have the same length
            samples = listOfSizes[0]
            #starting from 0, with N samples and each means LoopsSampleTime ns
            last = samples*SampleTime/1e6 #ms
            #to only plot around 100kpoint as maximum, approximate the 
            #decimation.
            decimation = int(samples/1e5)
            ranges = [0,last,decimation]
            return ranges
        return [None]*3
    
    def _getRangeInIndexes(self,signalType):
        if signalType.lower() == 'loops':
            ranges = self._loopsRanges
            SampleTime = LoopsSampleTime
        if signalType.lower() == 'diag':
            ranges = self._diagRanges
            SampleTime = DiagSampleTime
        lower = ranges[0]/(SampleTime/1e6)
        upper = ranges[1]/(SampleTime/1e6)
        return lower,upper
    
    def setWidgetRanges(self,widget,minimum,maximum,value):
        try:
            if minimum != None:
                widget.setMinimum(minimum)
            if maximum != None:
                widget.setMaximum(maximum)
            if value != None:
                widget.setValue(value)
        except Exception,e:
            self.warning("Cannot set min/max in %s due to: %s"%(widget,e))
            
    def connectSpinBox(self,widget,callback):
        signal = Qt.SIGNAL('editingFinished()')
        if not self._buttonSignalsDone:
            Qt.QObject.connect(widget,signal,callback)
    def connectButton(self,widget,callback):
        signal = Qt.SIGNAL('clicked(bool)')
        if not self._buttonSignalsDone:
            Qt.QObject.connect(widget,signal,callback)
    
    @property
    def startDisplayWidgetValue(self):
        '''Get the value in the spinbox in the gui
        '''
        if hasattr(self._parent,'ui') and \
           hasattr(self._parent.ui,'timeAndDecimation'):
            return self._parent.ui.timeAndDecimation._ui.startValue.value()
    @property
    def startDisplayValueHasChange(self):
        '''Compare in-class stored value and widget value
        '''
        if self._startDisplay != self.startDisplayWidgetValue:
            self.debug("startDisplayChange: %s,%s"
                   %(self._startDisplay,self.startDisplayWidgetValue))
            self._startDisplay = self.startDisplayWidgetValue
            return True
        return False
    @property
    def endDisplayWidgetValue(self):
        '''Get the value in the spinbox in the gui
        '''
        if hasattr(self._parent,'ui') and \
           hasattr(self._parent.ui,'timeAndDecimation'):
            return self._parent.ui.timeAndDecimation._ui.endValue.value()
    @property
    def endDisplayValueHasChange(self):
        '''Compare in-class stored value and widget value
        '''
        if self._endDisplay != self.endDisplayWidgetValue:
            self.debug("startDisplayChange: %s,%s"
                   %(self._endDisplay,self.endDisplayWidgetValue))
            self._endDisplay = self.endDisplayWidgetValue
            return True
        return False
    @property
    def decimationWidgetValue(self):
        '''Get the value in the spinbox in the gui
        '''
        if hasattr(self._parent,'ui') and \
           hasattr(self._parent.ui,'timeAndDecimation'):
            return self._parent.ui.timeAndDecimation._ui.decimationValue.value()
    @property
    def decimationValueHasChange(self):
        '''Compare in-class stored value and widget value
        '''
        if self._decimation != self.decimationWidgetValue:
            self.debug("startDisplayChange: %s,%s"
                   %(self._decimation,self.decimationWidgetValue))
            self._decimation = self.decimationWidgetValue
            return True
        return False
    # done range's area
    ####


    ####
    #--- plotting area
    def _isPlottableSignal(self,name):
        '''Check if with this name, there is a signal defined in SignalFields 
           (from the FdlSignals file) with enough information to plot it.
        '''
        #First check if the name is in the SignalFields.keys()
        #Then if the name has a subdictionary for the gui settings
        #Finally check if this subdictionary has a description of the plotting 
        # location in the gui.
        return SignalFields.has_key(name) and \
               SignalFields[name].has_key(gui) and \
               SignalFields[name][gui].has_key(tab) and \
               SignalFields[name][gui].has_key(plot)
    
    def _isLoopsSignal(self,name):
        '''Check if the signal is plottable from the side of the loops subset.
        '''
        return self._isPlottableSignal(name) and \
               SignalFields[name][gui][tab] in [Loops1,Loops2]

    def _isDiagnosticsSignal(self,name):
        '''Check if the signal is plottable from the side of the diagnostics 
           subset.
        '''
        return self._isPlottableSignal(name) and \
               SignalFields[name][gui][tab] in [Diag]
    def getPlotWidget(self,aTabName,aPlotName):
        if hasattr(self._parent,'ui') and \
           hasattr(self._parent.ui,aTabName):
            aTab = getattr(self._parent.ui,aTabName)._ui
            if hasattr(aTab,aPlotName):
                return getattr(aTab,aPlotName)
        return None

    def cleanAllPlots(self):
        #FIXME: distinguish between clean 'loops' or 'diag'
        allPlots = {Loops1:['topLeft','topRight',
                                   'middleLeft','middleRight',
                                   'bottomLeft','bottomRight'],
                    Loops2:['topLeft','topRight',
                                   'middleLeft','middleRight',
                                   'bottomLeft','bottomRight'],
                    Diag:['topLeft','topRight',
                          'middleUpLeft','middleUpRight',
                          'middleDownLeft','middleDownRight',
                          'bottomLeft','bottomRight']}
        for aTab in allPlots.keys():
            for aPlot in allPlots[aTab]:
                widget = self.getPlotWidget(aTab,aPlot)
                widget.clearAllRawData()
        self._plotted = 0
        self.memory()
        
    def doPlots(self,force=False):
        isNeeded = force or self.startDisplayValueHasChange or \
                            self.endDisplayValueHasChange   or \
                            self.decimationValueHasChange
        if isNeeded:
            self._forcePlot()
    
    def _forcePlot(self):
        self.cleanAllPlots()
        if len(self._loopsSignals.keys()) != 0:
            self.debug("starting loops plotting procedure: %s"
                       %(self._loopsSignals.keys()))
            lower,upper = self._getRangeInIndexes('loops')
            self._plotSignals(self._loopsSignals,[lower,upper])
        if len(self._diagSignals.keys()) != 0:
            self.debug("starting diagnostics plotting procedure: %s"
                       %(self._diagSignals.keys()))
            lower,upper = self._getRangeInIndexes('diag')
            self._plotSignals(self._diagSignals,[lower,upper])
        self.allPlotted.emit()

    def _plotSignals(self,descriptor,ranges):
        for signalName in descriptor.keys():
            self.debug("Signal %s will be plotted"%(signalName))
            if self._plotSingleSignal(signalName,
                                      descriptor[signalName],
                                      ranges):
                self._plotted+=1
                self.onePlotted.emit()

    def _plotSingleSignal(self,name,values,ranges):
        if not self._isPlottableSignal(name):
            return False
        try:
            lower = ranges[0]
            upper = ranges[1]
            dec = self._globalRanges[2]
            y = values[lower:upper:dec]
            self.debug("linspace(%g,%g,%d)"
                       %(self._startDisplay,self._endDisplay,y.size))
            x = np.linspace(self._startDisplay,self._endDisplay,y.size)
            signal = {'title':name,'x':x,'y':y}
            destinationTab = SignalFields[name][gui][tab]
            destinationPlot = SignalFields[name][gui][plot]
            plotColor = SignalFields[name][gui][color]
            destinationAxis =  SignalFields[name][gui][axis]
            curveProp = CurveAppearanceProperties(lColor=Qt.QColor(plotColor),
                                                  yAxis=destinationAxis)
            widget = self.getPlotWidget(destinationTab,destinationPlot)
            if widget == None:
                self.error("Not found a widget for curve %s"%(name))
                return False
            widget.attachRawData(signal,curveProp)
            self.memory()
            return True
        except Exception,e:
            self.error("Exception trying to plot %s: %s"%(name,e))
            traceback.print_exc()
            return False

    @property
    def processPercentage(self):
        nSignals = len(self._loopsSignals.keys())+len(self._diagSignals.keys())
        return int((self._plotted*100)/nSignals)
    # done plotting area
    ####


if __name__ == "__main__":
    '''When this file is called from the command line a test is performed (but 
       no plot anywhere).
    '''
    from taurus.qt.qtgui.application import TaurusApplication
    import random
    app = TaurusApplication()
    lenght = 1e6
    plotter = FdlPlotter()
    plotter.setLogLevel(plotter.Debug)
    signals = {'BeamPhase':np.random.randn(random.randint(1e6,2e6)),  #loops plot
               'FwCircOut_Q':np.random.randn(random.randint(1e6,2e6)),#diag plot
               'CavVolt_I':np.random.randn(random.randint(1e6,2e6)),  #non plottable
               'bar':np.random.randn(random.randint(1e6,2e6))         #non existing
               }
    plotter.appendSignals(signals)
    plotter.appendSignals({'BeamPhase':np.random.randn(lenght)})
    print("loops: %s"%(plotter._loopsSignals.keys()))
    print("diag: %s"%(plotter._diagSignals.keys()))
