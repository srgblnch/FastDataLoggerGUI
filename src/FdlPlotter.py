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
    from FdlFileParser import MyQtSignal

from taurus.qt.qtgui.plot import CurveAppearanceProperties
from numpy import linspace,array
import threading
import time

DecimationThreshold = 100

TOTAL_TIME = 411.00#ms
#FIXME: It's assumend that all the files have the same time, when what would 
# be assumed if that each sample set has a fix size in time.
#pointTime = 0.000195981#ms 
#totalTime = pointTime*self._loops[signalName].size

class Plotter(FdlLogger,Qt.QWidget):
    try:#normal way
        onePlotted = QtCore.pyqtSignal()
        allPlotted = QtCore.pyqtSignal()
        swapping = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        onePlotted = MyQtSignal('onePlotted')
        allPlotted = MyQtSignal('allPlotted')
        swapping = MyQtSignal('swapping')
    def __init__(self,parent):
        FdlLogger.__init__(self)
        try:#normal way
            Qt.QWidget.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QWidget.__init__(self)
            self.onePlotted._parent = self
            self.allPlotted._parent = self
            self.swapping._parent = self
        self._standby = threading.Event()
        self._standby.clear()
        self._parent = parent
        self._processor = parent._postProcessor
        self._signals = {}
        self._plotted = 0
#        try:#normal way
#            self._processor.change.connect(self._forcePlot)
#        except:#backward compatibility to pyqt 4.4.3
#            Qt.QObject.connect(self._processor,
#                               Qt.SIGNAL('change'),
#                               self._forcePlot)
        self.prepareTimeAndDecimation()
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
    def prepareTimeAndDecimation(self):
        self._startDisplay = self.startDisplay
        self._endDisplay = self.endDisplay
        self._decimation = self.decimation
        Qt.QObject.connect(self._parent.ui.replotButton,
                           Qt.SIGNAL('clicked(bool)'),
                           self._forcePlot)
        self._parent.ui.timeAndDecimation._ui.startValue\
                                                    .setKeyboardTracking(False)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.startValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        self._parent.ui.timeAndDecimation._ui.endValue\
                                                    .setKeyboardTracking(False)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.endValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
        self._parent.ui.timeAndDecimation._ui.decimationValue\
                                                    .setKeyboardTracking(False)
        Qt.QObject.connect(self._parent.ui.timeAndDecimation._ui.decimationValue,
                           Qt.SIGNAL('editingFinished()'),
                           self.doPlots)
    def cleanAllPlots(self):
        #FIXME: distinguish between clean 'loops' or 'diag'
        for aTab in self._widgetsMap.keys():
            for aPlot in self._widgetsMap[aTab].keys():
                self._widgetsMap[aTab][aPlot].clearAllRawData()
        self._plotted = 0
        self.memory()
    def appendSignals(self,dictionary):
        self.memory()
        if type(dictionary) == dict:
            for key in dictionary.keys():
                if self._isPlottableSignal(key):
                    if key in self._signals.keys():
                        self.warning("Append an existing %s signal overrides "\
                                     "the content!"%(key))
                    if type(dictionary[key]) == list:
                        self._signals[key] = array(dictionary[key])
                    else:
                        self._signals[key] = dictionary[key]
                    self.debug("Appending %s signal"%(key))
                else:
                    self.warning("Excluding %s signal because doesn't have "\
                                 "plotting information."%(key))
            self.debug("Currently there are %s signals to plot"
                       %(len(self._signals.keys())))
        else:
            raise TypeError("Unknown how append %s data type"%type(dictionary))
        self.memory()
    def cleanSignals(self):
        self._signals = {}
    def _isPlottableSignal(self,name):
        return SignalFields.has_key(name) and \
               SignalFields[name].has_key(gui)
    @property
    def startDisplay(self):
        return self._parent.ui.timeAndDecimation._ui.startValue.value()
    @property
    def startDisplayChange(self):
        '''Compare in-class stored value and widget value
        '''
        if self._startDisplay != self.startDisplay:
            self.debug("startDisplayChange: %s,%s"
                   %(self._startDisplay,self.startDisplay))
            self._startDisplay = self.startDisplay
            return True
        return False
    @property
    def endDisplay(self):
        return self._parent.ui.timeAndDecimation._ui.endValue.value()
    @property
    def endDisplayChange(self):
        '''Compare in-class stored value and widget value
        '''
        
        if self._endDisplay != self.endDisplay:
            self.debug("endDisplayChange: %s,%s"
                   %(self._endDisplay,self.endDisplay))
            self._endDisplay = self.endDisplay
            return True
        return False
    @property
    def decimation(self):
        return self._parent.ui.timeAndDecimation._ui.decimationValue.value()
    @property
    def decimationChange(self):
        '''Compare in-class stored value and widget value
        '''
        if self._decimation != self.decimation and \
           self.checkDecimationThreshold():
            self.debug("decimationChange: %s,%s"
                    %(self._decimation,self.decimation))
            self._decimation = self.decimation
            return True
        return False
    def checkDecimationThreshold(self):
        '''Alert the user in case the value is below a hundred.
        '''
        if self.decimation < DecimationThreshold:
            title = "Alert decimation threshold"
            msg = "Go below %d in decimation can cause memory problems.\n"\
                  "Are you sure?"\
                  %(DecimationThreshold)
            reply = QtGui.QMessageBox.warning(self,title,msg,
                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                                          QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.No:
                self._parent.ui.timeAndDecimation._ui.decimationValue.\
                                                  setValue(self._decimation)
                return False
        return True
    def doPlots(self,force=False):
        self.debug("*"*20+"doplots()")
        isNeeded = force or self.startDisplayChange or \
                            self.endDisplayChange   or \
                            self.decimationChange
        if isNeeded:
            self._forcePlot()
    
    def _forcePlot(self):
        self.debug("starting plotting procedure: %s"%(self._signals.keys()))
        #FIXME: this must be smarter
        self.cleanAllPlots()
        for signalName in self._signals.keys():
            self.debug("Signal %s will be plotted"%(signalName))
            self._plotSignal(signalName)
            self._plotted+=1
            self.onePlotted.emit()
            time.sleep(.1)#FIXME: remove that!!
            if self.isProcessSwapping():
                self.swapping.emit()
                self._standby.set()
                while self._standby.isSet():
                    time.sleep(1)
        self.allPlotted.emit()
    
    @property
    def processPercentage(self):
        return (self._plotted*100)/len(self._signals.keys())
    
    def _plotSignal(self,signalName):
        #TODO: sampling rate is different for Loops than diad
        try:
            y = self._signals[signalName]
            pointTime = TOTAL_TIME/y.size
            startPoint = int(self._startDisplay/pointTime)
            endPoint = int(self._endDisplay/pointTime)
            #apply the time&decimation
            y = y[startPoint:endPoint:self._decimation]
            x = linspace(self._startDisplay,self._endDisplay,y.size)
            #TaurusPlot structure
            signal = {'title':signalName,'x':x,'y':y}
            #locate in the possible TaurusPlots
            destinationTab = SignalFields[signalName][gui][tab]
            destinationPlot = SignalFields[signalName][gui][plot]
            plotColor = SignalFields[signalName][gui][color]
            destinationAxis =  SignalFields[signalName][gui][axis]
            curveProp = CurveAppearanceProperties(lColor=Qt.QColor(plotColor),
                                                  yAxis=destinationAxis)
            self._widgetsMap[destinationTab][destinationPlot].\
                                                attachRawData(signal,curveProp)
            if destinationAxis == y2:
                self._widgetsMap[destinationTab][destinationPlot].\
                                                                autoShowYAxes()
            self.memory()
        except Exception,e:
            self.error("Exception trying to plot %s: %s"%(signalName,e))

