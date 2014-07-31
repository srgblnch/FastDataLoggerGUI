###############################################################################
## file :               FdlSignalProcessor.py
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

from numpy import arcsin,pi
from copy import copy

from taurus.core.util import Logger
try:#normal way
    from taurus.external.qt import Qt,QtCore
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt
    from FdlFileParser import MyQtSignal
from FdlSignals import SignalFields

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
                                   {'arcsin':arcsin,'pi':pi,
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
