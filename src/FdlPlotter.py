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

from taurus.core.util import Logger
try:#normal way
    from taurus.external.qt import Qt
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt
from taurus.qt.qtgui.plot import CurveAppearanceProperties
from numpy import linspace
from FdlSignals import SignalFields,y2


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
                    x = linspace(self._startDisplay,self._endDisplay,y.size)
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
