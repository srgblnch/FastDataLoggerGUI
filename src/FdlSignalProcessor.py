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
from FdlSignals import *

import traceback

#TODO: optimise, when one or more facade parameters change not all the 
#      calculations has to be repeated, only the involved.

class SignalProcessor(Logger,Qt.QObject):
    try:#normal way
        change = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        change = MyQtSignal('change')
    def __init__(self,facade=None,loopsSignals=None,diagSignals=None):
        Logger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.change._parent = self
        self.setFacade(facade)
        self._signals = {}
        if loopsSignals!=None:
            self.appendSignals(loopsSignals)
        if diagSignals!=None:
            self.appendSignals(diagSignals)
    def appendSignals(self,dictionary):
        if type(dictionary) == dict:
            for key in dictionary.keys():
                if key in self._signals.keys():
                    self.warning("Append an existing signal (%s) overwrite "\
                                 "old content."%(key))
                self._signals[key] = dictionary[key]
                self.info("Appending %s signal"%(key))
        else:
            raise TypeError("Unknown how append %s data type"%type(dictionary))
    def setFacade(self,facade):
        self._facade = facade
#        if self._facade:
#            try:#normal way
#                self._facade.updated.connect(self.process)
#            except:#backward compatibility to pyqt 4.4.3
#                Qt.QObject.connect(self._facade,
#                                   Qt.SIGNAL('updated'),
#                                   self.process)

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
        categories = self._splitInCategories()
        if self._doFacadeFits(categories):
            self.debug("After facade calculations %d signals ready: %s"
                       %(len(categories['ready']),categories['ready']))
        else:
            self.error("Aborting signal processing because facade fits "\
                       "cannot be satisfied")
            return False
        if self._doFormulaCalcs(categories):
            self.debug("After formula calculations %d signals ready: %s"
                       %(len(categories['ready']),categories['ready']))
        else:
            self.error("Aborting signal processing because formulas"\
                       "cannot be satisfied")
            return False
        self.change.emit()
        return True

    #--- First descendant level
    def _splitInCategories(self):
        doneSignals = []
        facadeFit = []
        withFormula = []
        orphan = []
        for signalName in SignalFields.keys():
            if self._isFileSignal(signalName) and signalName in self._signals.keys():
                #is an I or Q, or an amplitude
                doneSignals.append(signalName)
            elif self._isFacadeFit(signalName):
                facadeFit.append(signalName)
            elif self._isFormula(signalName):
                withFormula.append(signalName)
            else:
                orphan.append(signalName)
        self.debug("Nothing to do with the %d file parsed signals: %s"
                   %(len(doneSignals),doneSignals))
        self.debug("Found %d signals that requires facade fit calculation: %s"
                   %(len(facadeFit),facadeFit))
        self.debug("Found %d signals to be calculated using a formula: %s"
                   %(len(withFormula),withFormula))
        self.warning("Alert, found %d orphan signals: %s."
                     %(len(orphan),orphan))
        return {'ready':doneSignals,
                'facade':facadeFit,
                'formula':withFormula,
                'orphan':orphan}
    def _doFacadeFits(self,categories):
        facadeSignals = categories['facade']
        calculated = categories['ready']
        lastPendingFacadeSignals = [0]*len(facadeSignals)+[len(facadeSignals)]
        while len(facadeSignals) > 0 and \
              len(set(lastPendingFacadeSignals)) != 1:
            aSignal = facadeSignals.pop(0)
            try:
                dependencies = [SignalFields[aSignal][vble]]#Diff with formula
                unsatisfied = list(set(dependencies).difference(calculated))
                if len(unsatisfied) == 0:
                    try:
                        self._calculate(aSignal)
                        calculated.append(aSignal)
                        self.debug("Facade signal %s calculated"%(aSignal))
                    except Exception,e:
                        self.error("Exception calculating facade %s signal:"\
                                   " %s"%(aSignal,e))
                else:
                    #when it's unsatisfied, append to retry
                    facadeSignals.append(aSignal)
                    self.warning("Facade signal %s cannot be yet calculated "\
                                 "due to %d unsatisfied: %s"
                                 %(aSignal,len(unsatisfied),unsatisfied))
            except Exception,e:
                self.error("Exception with %s dependencies: %s"%(aSignal,e))
            else:
                lastPendingFacadeSignals.pop(0)
                lastPendingFacadeSignals.append(len(facadeSignals))
                self.debug("Three last loops facade pending signals: %s"
                           %(lastPendingFacadeSignals))
        if len(set(lastPendingFacadeSignals)) == 1:
            self.error("Process has not finished well. There are pending "\
                       "calculations: %s"%(facadeSignals))
            return False
        return True
    
    def _doFormulaCalcs(self,categories):
        formulaSignals = categories['formula']
        calculated = categories['ready']
        lastPendingFormulaSignals = [0]*len(formulaSignals)+[len(formulaSignals)]
        while formulaSignals != [] and \
              len(set(lastPendingFormulaSignals)) != 1:
            #while there are pending elements or 
            #last 3 loops didn't reduce the list
            aSignal = formulaSignals.pop(0)
            try:
                dependencies = SignalFields[aSignal][depend]
                unsatisfied = list(set(dependencies).difference(calculated))
                if len(unsatisfied) == 0:
                    try:
                        self._calculate(aSignal)
                        calculated.append(aSignal)
                        self.debug("Formula signal %s calculated"%(aSignal))
                    except Exception,e:
                        self.error("Exception calculating formula %s signal:"\
                                   " %s"%(aSignal,e))
                        traceback.print_exc()
                else:
                    #when it's unsatisfied, append to retry
                    formulaSignals.append(aSignal)
                    self.warning("Formula signal %s cannot be yet calculated "\
                                 "due to unsatisfied %s"%(aSignal,unsatisfied))
            except Exception,e:
                self.error("Exception with %s dependencies: %s"%(aSignal,e))
            else:
                lastPendingFormulaSignals.pop(0)
                lastPendingFormulaSignals.append(len(formulaSignals))
                self.debug("Three last loops formula pending signals: %s"
                           %(lastPendingFormulaSignals))
        if len(set(lastPendingFormulaSignals)) == 1:
            self.error("Process has not finished well. There are pending "\
                       "calculations: %s"%(formulaSignals))
            return False
        return True

    #--- Second descendant level
    def _calculate(self,signal):
        if self._isLinear(signal):
            self.info("Calculating linear fit on %s signal"%(signal))
            m,n = self._getFacadesMandNs(signal)
            self._signals[signal] = \
                               (self._signals[SignalFields[signal][vble]]- n)/m
        elif self._isQuadratic(signal):
            self.info("Calculating quadratic fit on %s signal"%(signal))
            c,o = self._getFacadesCandOs(signal)
            self._signals[signal] = \
                    (self._signals[SignalFields[signal][vble]]**2/10e8/10**c)-o
        elif self._isFormula(signal):
            self.info("Calculating %s using formula %s"
                      %(signal,SignalFields[signal][formula]))
            try:
                beamCurrent = self._getFacadesBeamCurrent()
                self._signals[signal] = eval(SignalFields[signal][formula],
                                   {'arcsin':arcsin,'pi':pi,
                                    'BeamCurrent':beamCurrent},
                                   self._signals)
            except RuntimeWarning,e:
                self.warning("Warning in %s eval: %s"%(signal,e))
            except Exception,e:
                self.error("Exception in %s eval: %s"%(signal,e))
        else:
            self.info("nothing to do with %s signal"%(signal))
            return
        self.debug("Made the calculation for the signal %s (%d values)"
                   %(signal,len(self._signals[signal])))

    #--- Third descendant level
    def _getFacadesMandNs(self,signal):
        if self._facade != None:
            return self._facade.getMandNs(signal)
        else:
            return (1,0)
    def _getFacadesCandOs(self,signal):
        if self._facade != None:
            return self._facade.getCandOs(signal)
        else:
            return (1,0)
    def _getFacadesBeamCurrent(self):
        if self._facade:
            return self._facade.getBeamCurrent()
        else:
            return 100.0
    def _isFileSignal(self,signal):
        hasFieldField = SignalFields[signal].has_key(field)
        hasI = SignalFields[signal].has_key(I)
        hasQ = SignalFields[signal].has_key(Q)
        return hasFieldField or (hasI and hasQ)
    def _isFacadeFit(self,signal):
        return self._isLinear(signal) or self._isQuadratic(signal)
    def _isLinear(self,signal):
        return SignalFields[signal].has_key(vble) and \
               SignalFields[signal].has_key(slope) and \
               SignalFields[signal].has_key(offset)
    def _isQuadratic(self,signal):
        return SignalFields[signal].has_key(vble) and \
               SignalFields[signal].has_key(couple) and \
               SignalFields[signal].has_key(offset)
    def _isFormula(self,signal):
        return SignalFields[signal].has_key(formula) and \
               SignalFields[signal].has_key(handler)

def fileLoader(fileName):
    import json
    import numpy as np
    try:
        with open(fileName,'r') as f:
            signals = json.loads(f.read())
            for key in signals.keys():
                signals[key] = np.array(signals[key])
        return signals
    except Exception,e:
        print("\nCannot understand the given file: %s\n"%(e))

if __name__ == "__main__":
    '''Given a json output from a FdlFileParser test (made by calling 
       FdlFilePartser tester with a '--file' last argument), this second 
       phase calculation will be performed.
    '''
    import sys,time
    if len(sys.argv) != 3:
        print("\nFor this test is necessary a first argument with the file"\
              "with json's data.\n and another second argument to know if "\
              "its Loops or Diag data\n")
        sys.exit(-1)
    fileName = sys.argv[1]
    data = fileLoader(fileName)
    incomming = data.keys()
    print("Load %s signals: %s"%(len(incomming),incomming))
    if sys.argv[2].lower() == 'loops':
        processor = SignalProcessor(loopsSignals=data)
    elif sys.argv[2].lower() == 'diag':
        processor = SignalProcessor(diagSignals=data)
    else:
        print("\nCannot understand the given data type (Loops,Diag)\n"%())
        sys.exit(-2)
    processor.setLogLevel(processor.Debug)
    if processor.process():
        outcomming = processor._signals.keys()
        diff = len(outcomming)-len(incomming)
        print("\nCalculation process has finished correctly with %d new "\
              "signals.\n"%(diff))
    else:
        print("\nUou! Not all the signals where calculated!\n")
