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

MAX_POINTS_IN_PLOT = 1e5

class Plotter(FdlLogger,Qt.QWidget):
    '''This class is responsible to plot in the gui a set of signals it 
       receives. The signals can be from the loops set or (exclusive) from the
       diagnostics set.
       With the signal information this class, using the sampling rate of loops
       and diagnostics, will calculate the range of the data in time space and 
       the lower level of the decimation (to avoid memory issues).
    '''
    #####
    #---# QtSignals area
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
    #####
    
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
        self.prepareAllPlots()

    #####
    #---# getters&setters and conversions
    def _getSampleTime(self,signalType=None,signalName=None):
        '''Based on signal type or its name, return the time between samples.
        '''
        if signalType.lower() == 'loops' or self._isLoopsSignal(signalName):
            return LoopsSampleTime
        elif signalType.lower() == 'diag' or \
                                         self._isDiagnosticsSignal(signalName):
            return DiagSampleTime
        return False
    
    def _getSignalsetTimeUpperBoundary(self,signalType):
        '''From the given signal type, of the already loaded signals set, get
           how much time is lapsed between the start to the end.
        '''
        signalSet = {}
        if signalType.lower() == 'loops':
            signalSet = self._loopsSignals
            sampleTime = LoopsSampleTime
        elif signalType.lower() == 'diag':
            signalSet = self._diagSignals
            sampleTime = DiagSampleTime
        if signalSet.keys() != []:
            listOfSizes = [len(signalSet[x]) for x in signalSet.keys()]
            if len(set(listOfSizes)) == 1:
                timeUpperBpundary = self._converFromIndexToTime(listOfSizes[0],
                                                                sampleTime)
                self.debug("%s upper boundary %g miliseconds"
                           %(signalType,timeUpperBpundary))
                return timeUpperBpundary
        return None
    
    def _getTimeUpperBoundary(self):
        '''Check the data stored in the object to define what's the time 
           representing the last value in those arrays.
        '''
        listOfSizes = []
        t4loops = self._getSignalsetTimeUpperBoundary('loops')
        t4diag = self._getSignalsetTimeUpperBoundary('diag')
        if t4loops != None or t4diag != None:
            return np.max([t4loops,t4diag])
        return False

    def _getDecimationLowerboundary(self):
        '''Knowing the an interval of time, calculate what's the lower 
           decimation boundary to restrict the number of samples plotted to a
           maximum of 1e5 points.
        '''
        lowerTime = self._getTimeStartValue()
        upperTime = self._getTimeEndValue()
        if self._loopsSignals != {}:
            loopsStart = self._convertFromTimeToIndex(lowerTime, LoopsSampleTime)
            loopsEnd = self._convertFromTimeToIndex(upperTime, LoopsSampleTime)
            loopsDiff = loopsEnd - loopsStart
        else:
            loopsStart,loopsEnd,loopsDiff = None,None,None
        if self._diagSignals != {}:
            diagStart = self._convertFromTimeToIndex(lowerTime, DiagSampleTime)
            diagEnd = self._convertFromTimeToIndex(upperTime, DiagSampleTime)
            diagDiff = diagEnd - diagStart
        else:
            diagStart,diagEnd,diagDiff = None,None,None
        self.debug("In time interval [%g,%g]: loops[%s:%s] (%s samples), "\
                   "diag[%s:%s] (%s samples)"
                   %(lowerTime,upperTime,loopsStart,loopsEnd,loopsDiff,
                     diagStart,diagEnd,diagDiff))
        if loopsDiff == None and diagDiff == None:
            return False
        biggestSet = np.max([loopsDiff,diagDiff])
        ret = int(biggestSet/MAX_POINTS_IN_PLOT)+1
        self.info("Minimum decimation threshold %d"%(ret))
        return ret

    def _converFromIndexToTime(self,idx,sampleTime):
        '''As the np.array talks in terms of an array index and the tools for
           time and decimation talks in terms of time, this method is made to
           convert an index position to its meaning in time domain.
        '''
        ret = idx*sampleTime/1e6 #ms
        self.debug("Converting index %d to %g miliseconds"%(idx,ret))
        return ret

    def _convertFromTimeToIndex(self,miliseconds,sampleTime):
        '''As the np.array talks in terms of an array index and the tools for
           time and decimation talks in terms of time, this method is made to
           convert a time value in miliseconds to the corresponding index 
           position in the array.
        '''
        ret = int(miliseconds/(sampleTime/1e6)) #idx
        self.debug("Converting %g miliseconds to %d index"%(miliseconds,ret))
        return ret

    def _getSignal(self,name):
        '''Return the raw data stored for the specified signal name. If doesn't
           exist, return an empty array.
        '''
        if self._isLoopsSignal(name):
            return self._loopsSignals[name]
        elif self._isDiagnosticsSignal(name):
            return self._diagSignals[name]
        return np.array([])

    def _getSignals(self,signalType):
        '''Return the data set by mention the data type wanted.
        '''
        if signalType.lower() == 'loops':
            return self._loopsSignals
        elif signalType.lower() == 'diag':
            return self._diagSignals
        return {}

    def _getTimeStartWidget(self):
        '''If a widget exist for time and decimation, return a reference to the
           widget of the start display of the sampling.
        '''
        if self._haveTimeAndDecimation():
            return self._parent.ui.timeAndDecimation._ui.startValue
        return None
    def _getTimeStartValue(self):
        '''If a widget exist for time and decimation, return the value written
           in the start display widget (updating an internal variable) and 
           return this internal value.
        '''
        if self._haveTimeAndDecimation():
            self._timeStartValue = self._getTimeStartWidget().value()
        return self._timeStartValue
    def _setTimeStartValue(self,value):
        '''If a widget exist for time and decimation, set its value from the 
           parameter passed to the start display widget.
        '''
        self.debug("Setting a new Start Time value %g (was %g)"
                   %(value,self._timeStartValue))
        self._timeStartValue = value
        if self._haveTimeAndDecimation():
            self._getTimeStartWidget().setValue(self._timeStartValue)

    def _getTimeStartLabelWidget(self):
        '''If a widget exist for time and decimation, return a reference to the
           widget with the end time label
        '''
        if self._haveTimeAndDecimation():
            return self._parent.ui.timeAndDecimation._ui.startLabel

    def _getTimeEndWidget(self):
        '''If a widget exist for time and decimation, return a reference to the
           widget of the end display of the sampling.
        '''
        if self._haveTimeAndDecimation():
            return self._parent.ui.timeAndDecimation._ui.endValue
    def _getTimeEndValue(self):
        '''If a widget exist for time and decimation, return the value written
           in the end display widget (updating an internal variable) and 
           return this internal value.
        '''
        if self._haveTimeAndDecimation():
            self._timeEndValue = self._getTimeEndWidget().value()
        return self._timeEndValue
    def _setTimeEndValue(self,value):
        '''If a widget exist for time and decimation, set its value from the 
           parameter passed to the end display widget.
        '''
        self.debug("Setting a new End Time value %g (was %g)"
                   %(value,self._timeEndValue))
        self._timeEndValue = value
        if self._haveTimeAndDecimation():
            self._getTimeEndWidget().setValue(self._timeEndValue)

    def _getTimeEndLabelWidget(self):
        '''If a widget exist for time and decimation, return a reference to the
           widget with the end time label
        '''
        if self._haveTimeAndDecimation():
            return self._parent.ui.timeAndDecimation._ui.stopLabel

    def _getDecimationWidget(self):
        '''If a widget exist for time and decimation, return a reference to the
           widget of the decimation display of the sampling.
        '''
        if self._haveTimeAndDecimation():
            return self._parent.ui.timeAndDecimation._ui.decimationValue
    def _getDecimationValue(self):
        '''If a widget exist for time and decimation, return the value written
           in the decimation display widget (updating an internal variable) and 
           return this internal value.
        '''
        if self._haveTimeAndDecimation():
            self._decimationValue = self._getDecimationWidget().value()
        return self._decimationValue
    def _setDecimationValue(self,value):
        '''If a widget exist for time and decimation, set its value from the 
           parameter passed to the decimation display widget.
        '''
        value = int(value)
        self.debug("Setting a new Decimation value %d (was %d)"
                   %(value,self._decimationValue))
        self._decimationValue = value
        if self._haveTimeAndDecimation():
            self._getDecimationWidget().setValue(self._decimationValue)

    def _getDecimationLabelWidget(self):
        '''If a widget exist for time and decimation, return a reference to the
           widget with the decimation label
        '''
        if self._haveTimeAndDecimation():
            return self._parent.ui.timeAndDecimation._ui.decimationLabel

    def _getPlotWidget(self,aTabName,aPlotName):
        '''Identify the plot object from given coordinates as the tab and
           the name of the plot.
        '''
        if hasattr(self._parent,'ui') and \
           hasattr(self._parent.ui,aTabName):
            aTab = getattr(self._parent.ui,aTabName)._ui
            if hasattr(aTab,aPlotName):
                return getattr(aTab,aPlotName)
        return None

    @property
    def processPercentage(self):
        nSignals = len(self._loopsSignals.keys())+len(self._diagSignals.keys())
        return int((self._plotted*100)/nSignals)
    #--- done getters&setters
    #####

    #####
    #---# signals
    def connectSpinBox(self,widget,callback):
        signal = Qt.SIGNAL('editingFinished()')
        if not self._buttonSignalsDone:
            Qt.QObject.connect(widget,signal,callback)
    def connectButton(self,widget,callback):
        signal = Qt.SIGNAL('clicked(bool)')
        if not self._buttonSignalsDone:
            Qt.QObject.connect(widget,signal,callback)
    def _hasChangedTimeStartValue(self):
        if self._haveTimeAndDecimation():
            if self._timeStartValue != self._getTimeStartWidget().value():
                self.debug("Start time value has changed!")
                self._getTimeStartValue()
                return True
        return False
    def _hasChangedTimeEndValue(self):
        if self._haveTimeAndDecimation():
            if self._timeEndValue != self._getTimeEndWidget().value():
                self.debug("End time value has changed!")
                self._getTimeEndValue()
                return True
        return False
    def _hasChangedDecimationValue(self):
        if self._haveTimeAndDecimation():
            if self._decimationValue != self._getDecimationWidget().value():
                self.debug("Start time value has changed!")
                self._getDecimationValue()
                return True
        return False
    #--- done signals
    #####

    #####
    #---# Checkers
    def _isPlottableSignal(self,name):
        '''Check if with this name, there is a signal defined in SignalFields 
           (from the FdlSignals file) with enough information to plot it.
        '''
        #First check if the name is in the SignalFields.keys()
        #Then if the name has a subdictionary for the gui settings
        #Finally check if this subdictionary has a description of the plotting 
        # location in the gui.
        return SignalFields.has_key(name) and \
               SignalFields[name].has_key(GUI_) and \
               SignalFields[name][GUI_].has_key(TAB_) and \
               SignalFields[name][GUI_].has_key(PLOT_)

    def _isLoopsSignal(self,name):
        '''Check if the signal is plottable from the side of the loops subset.
        '''
        return self._isPlottableSignal(name) and \
               SignalFields[name][GUI_][TAB_] in [Loops1,Loops2]

    def _isDiagnosticsSignal(self,name):
        '''Check if the signal is plottable from the side of the diagnostics 
           subset.
        '''
        return self._isPlottableSignal(name) and \
               SignalFields[name][GUI_][TAB_] in [Diag]

    def _haveTimeAndDecimation(self):
        '''Return a boolean depending on if a widget for time and decimation
           exist.
        '''
        if hasattr(self._parent,'ui'):
            if hasattr(self._parent.ui,'timeAndDecimation'):
                return True
        return False
    
    def _haveLoopsSignals(self):
        return self._loopsSignals != {}
    
    def _haveDiagSignals(self):
        return self._diagSignals != {}
    #--- done Checkers
    #####

    #####
    #---# Internal signal structures
    def appendSignals(self,signalsSet):
        '''Given a dictionary with the signals names as key and its np.arrays 
           as values, introduce them in the class to plot them.
           In case a key already exist, it's contents will be updated with the 
           new value.
        '''
        if type(signalsSet) == dict:
            self.debug("Received a data set with signals %s"
                       %(signalsSet.keys()))
            for signalName in signalsSet:
                if self._isPlottableSignal(signalName):
                    self._addSignal(signalName,signalsSet[signalName])
                else:
                    self.debug("Ignoring '%s' because is not plottable"
                               %(signalName))
#        if len(self._loopsSignals.keys()) != 0:
#            self._loopsRanges = self.calculateMaximalRanges('loops')
#            self.debug("Ranges for loops [min,max,dec] = %s"
#                       %(self._loopsRanges))
#        if len(self._diagSignals.keys()) != 0:
#            self._diagRanges = self.calculateMaximalRanges('diag')
#            self.debug("Ranges for diagnostics [min,max,dec] = %s"
#                       %(self._diagRanges))
        self._timeAndDecimationBoundaries()
        #self.debug("Global ranges [min,max,dec] = %s"%(self._globalRanges))

    def cleanSignals(self):
        '''Proceed removing all the buffers storing raw data and clean up
           anything that can be changed based on this data.
        '''
        self._loopsSignals = {}
        self._diagSignals = {}
        #time & decimation
        self._timeStartValue = 0.0
        self._timeEndValue = MAX_FILE_TIME
        self._decimationValue = 1
        if self._haveTimeAndDecimation():
            self._getTimeStartWidget().setMinimum(self._timeStartValue)
            self._getTimeStartWidget().setMaximum(self._timeEndValue)
            self._setTimeStartValue(self._timeStartValue)
            self._getTimeEndWidget().setMinimum(self._timeStartValue)
            self._getTimeEndWidget().setMaximum(self._timeEndValue)
            self._setTimeEndValue(self._timeEndValue)
            self._updateEndUpperBoundaryChange()
            #self._getDecimationWidget().setMinimum(1)
            self._updateDecimationLowerBoundaryChange()
            self._getDecimationWidget().setMaximum(1000)
            self._setDecimationValue(1)
        

    def _addSignal(self,signalName,signalValue):
        '''This is an internal method made to append one single signal.
           The arguments are an string with the signal name and a np.array with
           its values.
        '''
        if signalName in self._loopsSignals.keys() + self._diagSignals.keys():
            #check if it's already there
            self.warning("append '%s' when already exist. Updating "\
                         "with new data provided."%(signalName))
        if type(signalValue) != list:
            #list is when data is not ready, but it's cheaper than
            #compare it it's some kind of np.array
            #FIXME: would be isinstance(signalValue,np.ndarray) ?
            if self._isLoopsSignal(signalName):
                self.debug("Adding '%s' signal, and tag as loops (%d samples)"
                           %(signalName,len(signalValue)))
                self._loopsSignals[signalName] = signalValue
            elif self._isDiagnosticsSignal(signalName):
                self.debug("Adding '%s' signal, and tag as diagnostics "\
                           "(%d samples)"%(signalName,len(signalValue)))
                self._diagSignals[signalName] = signalValue
            else:
                return#don't append the signal if it's not loops or diag
    #--- done Internal signal structures
    #####
    
    #####
    #---# Time and decimation
    def _timeAndDecimationBoundaries(self):
        '''After load a new set of signals this method shall be called to 
           reconfigure the values and limits for the Time upper and lower range
           and also the lower limit of the decimation to avoid plotting more
           than 100.000 points.
        '''
        self._setTimeStartValue(0)
        if self._updateEndUpperBoundaryChange() and \
           self._getTimeEndWidget().maximum() < self._getTimeEndValue():
            self._setTimeEndValue(self._getTimeEndWidget().maximum())
#        decimationLowerBoundary = self._getDecimationLowerboundary()
#        if decimationLowerBoundary > self._getDecimationValue():
#            self._setDecimationValue(decimationLowerBoundary)
        if self._haveTimeAndDecimation():
            self._updateDecimationLowerBoundaryChange()
            #connect signals to interact with the gui
            self.connectSpinBox(self._getTimeStartWidget(),self.doPlots)
            self.connectSpinBox(self._getTimeEndWidget(),self.doPlots)
            self.connectSpinBox(self._getDecimationWidget(),self.doPlots)
            if not self._buttonSignalsDone:
                self.connectButton(self._parent.ui.replotButton,
                                   self._forcePlot)
                self._buttonSignalsDone = True
    #--- done Time and decimation
    #####
    
    #####
    #---# plot and clean
    def prepareAllPlots(self,group=None):
        '''Iterate along all the plot widgets the first time to configure them
           in the same way
        '''
        #FIXME: distinguish between clean 'loops' or 'diag'
        for aTab in allPlots.keys():
            for aPlot in allPlots[aTab]:
                widget = self._getPlotWidget(aTab,aPlot)
                #to show y2 scale
                widget.autoShowYAxes()
                #legend position
                widget.setLegendPosition(Qwt5.QwtPlot.BottomLegend)
                #always show legend
                widget.showLegend(show=True,forever=True)
    
    def showAllAxes(self,group=None):
        '''Iterate along all the plot widgets to show the Y2 axis
        '''
        #FIXME: distinguish between clean 'loops' or 'diag'
        for aTab in allPlots.keys():
            for aPlot in allPlots[aTab]:
                widget = self._getPlotWidget(aTab,aPlot)
                #to show y2 scale
                widget.autoShowYAxes()
    
    def cleanAllPlots(self,group=None):
        '''Iterate along all the plot widgets and remove all raw data.
        '''
        #FIXME: distinguish between clean 'loops' or 'diag'
        for aTab in allPlots.keys():
            for aPlot in allPlots[aTab]:
                widget = self._getPlotWidget(aTab,aPlot)
                widget.clearAllRawData()
        self._plotted = 0
        self.memory()

    def doPlots(self,force=False):
        '''If there is something that has to be plotted, do the redraw. Also
           this operation can be forced.
        '''
        isNeeded = force or self._hasChangedTimeStartValue or \
                            self._hasChangedTimeEndValue   or \
                            self._hasChangedDecimationValue
        if isNeeded:
            self._forcePlot()

    def _updateEndUpperBoundaryChange(self):
        '''Recalculate the upper boundary of the end time to know if it has
           be updated the maximum value in the gui.
        '''
        try:
            TimeUpperBoundary = self._getTimeUpperBoundary()
            if TimeUpperBoundary == False:
                self.debug("Not yet data to upper time limit!")
                self._getTimeStartLabelWidget().setText("Start Display [0,%d]"\
                                                           " ms"%MAX_FILE_TIME)
                self._getTimeEndLabelWidget().setText("End Display [0,%d] ms"
                                                              %(MAX_FILE_TIME))
                return True
            if TimeUpperBoundary != \
                                      self._getTimeEndWidget().maximum():
                self._getTimeStartLabelWidget().setText("Start Display [0,%d]"\
                                                       " ms"%TimeUpperBoundary)
                self._getTimeEndLabelWidget().setText("End Display [0,%d] ms"
                                                          %(TimeUpperBoundary))
                self._getTimeEndWidget().setMaximum(TimeUpperBoundary)
                self.info("Newer upper time limit: %s"%(TimeUpperBoundary))
                return True
        except Exception,e:
            self.warning("Wasn't possible to calculate upper time limit:"\
                         " [%s] %s"%(e.__class__.__name__,e))
        return False

    def _updateDecimationLowerBoundaryChange(self):
        '''Recalculate the lower boundary of the decimation to know if it has
           be updated the minimum value in the gui.
        '''
        try:
            decimationLowerBoundary = self._getDecimationLowerboundary()
            if decimationLowerBoundary == False:
                self.debug("Not yet data to decimation lower limit!")
                self._getDecimationLabelWidget().setText("Decimation [1,1000]")
            if decimationLowerBoundary != \
                                      self._getDecimationWidget().minimum():
                self._getDecimationLabelWidget().setText("Decimation [%d,1000]"
                                                    %(decimationLowerBoundary))
                self._getDecimationWidget().setMinimum(decimationLowerBoundary)
                self.info("Newer lower decimation limit: %s"
                          %(decimationLowerBoundary))
                return True
        except Exception,e:
            self.warning("Wasn't possible to calculate lower decimation "\
                         "limit: [%s] %s"%(e.__class__.__name__,e))
        return False

    def _forcePlot(self):
        '''Force a (re)drawing of all the information stored on the TaurusPlot
           widgets as raw data.
        '''
        self.cleanAllPlots()
        self._updateDecimationLowerBoundaryChange()
        startTime = self._getTimeStartValue()
        endTime = self._getTimeEndValue()
        decimation = self._getDecimationValue()
        if self._haveLoopsSignals():
            self.debug("Starting a plotting procedure for LOOPS (with %s keys"
                       %(self._loopsSignals.keys()))
            lower = self._convertFromTimeToIndex(startTime,
                                                 LoopsSampleTime)
            upper = self._convertFromTimeToIndex(endTime,
                                                 LoopsSampleTime)
            self._plotSignals(self._loopsSignals,[lower,upper],decimation)
        if self._haveDiagSignals():
            self.debug("Starting a plotting procedure for DIAG (with %s keys"
                       %(self._diagSignals.keys()))
            lower = self._convertFromTimeToIndex(startTime,
                                                 DiagSampleTime)
            upper = self._convertFromTimeToIndex(endTime,
                                                 DiagSampleTime)
            self._plotSignals(self._diagSignals,[lower,upper],decimation)
        self.showAllAxes()
        self.allPlotted.emit()
    
    def _plotSignals(self,descriptor,ranges,decimation=1):
        '''Iterate with in a descriptor and plot on their TaurusPlot widgets
           the subset of data in the interval parameter.
        '''
        for signalName in descriptor.keys():
            self.debug("Signal %s will be plotted"%(signalName))
            if self._plotSingleSignal(signalName,
                                      descriptor[signalName],
                                      ranges,decimation):
                self._plotted+=1
                self.onePlotted.emit()

    def _plotSingleSignal(self,name,values,ranges,decimation):
        '''Given one single signal (name and raw data) together with the 
           interval to be plotted and the decimation to apply, attach to the
           corresponding TaurusPlot widget.
        '''
        if not self._isPlottableSignal(name):
            return False
        try:
            lower = ranges[0]
            upper = ranges[1]
            startTime = self._getTimeStartValue()
            endTime = self._getTimeEndValue()
            self.debug("%s[%d:%d:%d]"%(name,lower,upper,decimation))
            y = values[lower:upper:decimation]
            self.debug("linspace(%g,%g,%d)"%(startTime,endTime,y.size))
            x = np.linspace(startTime,endTime,y.size)
            signal = {'title':name,'x':x,'y':y}
            destinationTab = SignalFields[name][GUI_][TAB_]
            destinationPlot = SignalFields[name][GUI_][PLOT_]
            plotColor = SignalFields[name][GUI_][COLOR_]
            destinationAxis =  SignalFields[name][GUI_][AXIS_]
            curveProp = CurveAppearanceProperties(lColor=Qt.QColor(plotColor),
                                                  yAxis=destinationAxis)
            widget = self._getPlotWidget(destinationTab,destinationPlot)
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
    #--- done plot and clean
    #####



if __name__ == "__main__":
    '''When this file is called from the command line a test is performed (but 
       no plot anywhere).
    '''
    from taurus.qt.qtgui.application import TaurusApplication
    import random
    app = TaurusApplication()
    loopsLenght = random.randint(1e6,2e6)
    diagLenght = random.randint(1e6,2e6)
    plotter = Plotter()
    plotter.setLogLevel(plotter.Debug)
    print("TEST: append only one signal (one type)")
    plotter.appendSignals({'BeamPhase':np.random.randn(loopsLenght)})
    print("TEST: append more signals (both types)")
    signals = {'BeamPhase':np.random.randn(loopsLenght),  #loops plot
               'FwCircOut_Q':np.random.randn(diagLenght),#diag plot
               'CavVolt_I':np.random.randn(loopsLenght),  #non plottable
               'bar':np.random.randn(loopsLenght)         #non existing
               }
    plotter.appendSignals(signals)
    #print("loops: %s"%(plotter._loopsSignals.keys()))
    #print("diag: %s"%(plotter._diagSignals.keys()))
