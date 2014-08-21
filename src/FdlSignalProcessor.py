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

import numpy as np
from copy import copy

from FdlLogger import *
from FdlSignals import *

try:#normal way
    from taurus.external.qt import Qt,QtCore
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt

import threading
import traceback

#TODO: optimise, when one or more facade parameters change not all the 
#      calculations has to be repeated, only the involved.

class SignalProcessor(FdlLogger,Qt.QObject):
    try:#normal way
        oneProcessed = QtCore.pyqtSignal()
        allProcessed = QtCore.pyqtSignal()
        swapping = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        allProcessed = MyQtSignal('allProcessed')
        oneProcessed = MyQtSignal('oneProcessed')
        swapping = MyQtSignal('swapping')

    def __init__(self,facade=None):
        FdlLogger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.allProcessed._parent = self
            self.oneProcessed._parent = self
            self.swapping._parent = self
        self._standby = threading.Event()
        self._standby.clear()
        self.setFacade(facade)
        self._signals = {}
        self._signalsCalculated = 0
        self._signals2Calculate = 0

    def appendSignals(self,dictionary):
        if type(dictionary) == dict:
            for key in dictionary.keys():
                if key in self._signals.keys():
                    self.warning("Append an existing signal (%s) overwrite "\
                                 "old content."%(key))
                self._signals[key] = dictionary[key]
                self.debug("The addition of %s means %d kB"
                           %(key,self.getSubobjectSize(self._signals[key])))
        else:
            raise TypeError("Unknown how append %s data type"%type(dictionary))
        self.debug("Signals size %d kB"%(self.getSubobjectSize(self._signals)))
        self.memory()

    def setFacade(self,facade):
        self._facade = facade

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
        self._signalsCalculated = 0
        self._signals2Calculate = \
                           len(categories['facade'])+len(categories['formula'])
        if self._doCalculations(categories, 'facade'):
            self.debug("After facade calculations %d signals ready: %s"
                       %(len(categories['ready']),categories['ready']))
        else:
            self.error("Aborting signal processing because facade fits "\
                       "cannot be satisfied")
            return False
        if self._doCalculations(categories, 'formula'):
            self.debug("After formula calculations %d signals ready: %s"
                       %(len(categories['ready']),categories['ready']))
        else:
            self.error("Aborting signal processing because formulas"\
                       "cannot be satisfied")
            return False
        self.info("Signal processor is done.")
        self.allProcessed.emit()
        self.memory()
        return True
    @property
    def processPercentage(self):
        if self._signals2Calculate > 0:
            return int((self._signalsCalculated*100)/self._signals2Calculate)
        return 0

    #--- First descendant level
    def _splitInCategories(self):
        doneSignals = []
        facadeFit = []
        withFormula = []
        orphan = []
        for signalName in SignalFields.keys():
            if self._isFileSignal(signalName):
                #is an I or Q, or an amplitude
                doneSignals.append(signalName)
            elif self._isFacadeFit(signalName) and \
                 self._isVbleInOurSet(signalName):
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
    
    def _doCalculations(self,categories,inputTag):
        inputSignals = categories[inputTag]
        calculated = categories['ready']
        lastPendingSignals = [0]*len(inputSignals)+[len(inputSignals)]
        while len(inputSignals) > 0 and \
              len(set(lastPendingSignals)) != 1:
              #while there are signals to process and it's not stall with 
              #insatisfactible dependencies:
            aSignal = inputSignals.pop(0)
            try:
                dependencies = self._takeDepenedencies(aSignal)
                unsatisfied = list(set(dependencies).difference(calculated))
                if len(unsatisfied) == 0:
                    try:
                        self._calculate(aSignal)
                        calculated.append(aSignal)
                        self._signalsCalculated+=1
                        self.oneProcessed.emit()
                        self.debug("New %s signal %s calculated"
                                   %(inputTag,aSignal))
                    except Exception,e:
                        self.error("Exception calculating %s signal %s: %s"
                                   %(inputTag,aSignal,e))
                else:
                    #when dependencies are unsatisfied, append to the end 
                    #to retry it later. That's why there is another stopper in
                    #the loop when all signals has been check and the 
                    #dependencies will never be satisfied.
                    inputSignals.append(aSignal)
                    self.warning("The %s signal %s cannot be yet calculated "\
                                 "due to %d unsatisfied dependencies: %s"
                                 %(inputTag,aSignal,
                                   len(unsatisfied),unsatisfied))
            except Exception,e:
                self.error("Exception in %s with %s dependencies: %s"
                           %(inputTag,aSignal,e))
            else:
                lastPendingSignals.pop(0)
                lastPendingSignals.append(len(inputSignals))
                self.debug("%d of the last loops in %s pending signal:"
                           %(len(lastPendingSignals),lastPendingSignals))
        if len(set(lastPendingSignals)) < 1:
            self.error("Process has NOT finished well! There are pending "\
                       "calculations: %s"%(inputSignals))
            return False
        return True
        
    def _takeDepenedencies(self,signalName):
        if SignalFields[signalName].has_key(vble):
            return [SignalFields[signalName][vble]]
        elif SignalFields[signalName].has_key(depend):
            return SignalFields[signalName][depend]
        else:
            return []

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
            self.info("Calculating %s using formula '%s'"
                      %(signal,SignalFields[signal][formula]))
            try:
                beamCurrent = self._getFacadesBeamCurrent()
                self._signals[signal] = eval(SignalFields[signal][formula],
                                   {'arcsin':np.arcsin,
                                    'arctan':np.arctan,
                                    'pi':np.pi,
                                    'BeamCurrent':beamCurrent},
                                   self._signals)
            except RuntimeWarning,e:
                self.warning("Warning in %s eval: %s"%(signal,e))
            except Exception,e:
                self.error("Exception in %s eval: %s"%(signal,e))
        else:
            self.info("nothing to do with %s signal"%(signal))
            return
        self.debug("Made the calculation for the signal %s (%d values), "\
                   "extra %d kB"
                   %(signal,len(self._signals[signal]),
                     self.getSubobjectSize(self._signals[signal])))
        self.memory()
        if self.isProcessSwapping():
            self.swapping.emit()
            self._standby.set()
            while self._standby.isSet():
                time.sleep(1)

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
        if not self._isSignalInOurSet(signal):
            return False
        hasFieldField = SignalFields[signal].has_key(field)
        hasI = SignalFields[signal].has_key(I)
        hasQ = SignalFields[signal].has_key(Q)
        return hasFieldField or (hasI and hasQ)
    def _isSignalInOurSet(self,signal):
        return signal in self._signals.keys()
    def _isVbleInOurSet(self,signal):
        vbleName = SignalFields[signal][vble]
        if self._isFileSignal(vbleName) and \
           self._isSignalInOurSet(vbleName):
            return True
    def _isFacadeFit(self,signal):
        return self._isLinear(signal) or self._isQuadratic(signal)
    def _isLinear(self,signal):
        if SignalFields[signal].has_key(vble) and \
           self._isFileSignal(SignalFields[signal][vble]):
            return SignalFields[signal].has_key(slope) and \
                   SignalFields[signal].has_key(offset)
        return False
    def _isQuadratic(self,signal):
        if SignalFields[signal].has_key(vble) and \
           self._isFileSignal(SignalFields[signal][vble]):
            return SignalFields[signal].has_key(couple) and \
                   SignalFields[signal].has_key(offset)
        return False
    def _isFormula(self,signal):
        if SignalFields[signal].has_key(formula):
            #if any of the dependencies is NOT facade fit
            signalDependencies = copy(SignalFields[signal][depend])
            for i,aDependency in enumerate(signalDependencies):
                #FIXME: this is risky without a nesting control
                if self._isFormula(aDependency) or \
                   self._isFacadeFit(aDependency) or \
                   self._isFileSignal(aDependency):
                    signalDependencies[i] = True
                else:
                    signalDependencies[i] = False
            if all(signalDependencies):
                return True
        return False

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
