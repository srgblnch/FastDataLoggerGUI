###############################################################################
## file :               FdlFileParser.py
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
import numpy as np
import scipy as sp
try:#normal way
    from taurus.external.qt import Qt,QtGui,QtCore,Qwt5
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt,QtGui,QtCore,Qwt5
from threading import Thread,Event
from math import sqrt
from copy import copy
import traceback
from time import time

from Signals import *

from Signals import *

SEPARATOR = 0x7FFF
LOAD_ERROR_RATE = 0.01

class MyQtSignal(Logger):
    '''This class is made to emulate the pyqtSignals for too old pyqt versions.
    '''
    def __init__(self,name,parent=None):
        Logger.__init__(self,parent)
        self._parent = parent
        self._name = name
        self._cb = []
    def emit(self):
        self.info("Signal %s emit (%s)"%(self._name,self._cb))
#        for i,cb in enumerate(self._cb):
#            try:
#                cb()
#            except Exception,e:
#                self.error("Cannot do the %dth callback for %s: %s"
#                           %(i,self._name,e))
#                traceback.print_exc()
        Qt.QObject.emit(self._parent,Qt.SIGNAL(self._name))
    def connect(self,callback):
        self.error("Trying a connect on MyQtSignal(%s)"%(self._name))
        raise Exception("Invalid")
        #self._cb.append(callback)

class nditer(Logger):
    '''This class is made to emulate np.nditer for too old numpy versions.
    '''
    def __init__(self,data):
        self._data = data
        self.iterindex = 0
#    @property
#    def iterindex(self):
#        return self._index
    @property
    def itersize(self):
        return len(self._data)
    @property
    def value(self):
        return self._data[self.iterindex]
    def next(self):
        self.iterindex+=1
        try:
            return self._data[self.iterindex]
        except:
            raise StopIteration("Out of range")

class FdlFile(Logger,Qt.QObject):
    try:#normal way
        step = QtCore.pyqtSignal()
        done = QtCore.pyqtSignal()
        aborted = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        step = MyQtSignal('step')
        done = MyQtSignal('done')
        aborted = MyQtSignal('aborted')
    
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        Logger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.step._parent = self
            self.done._parent = self
            self.aborted._parent = self
        self._filename = filename
        self._loadErrorRate=loadErrorRate
        self._signals = {}
        try:
            self._nsignals = len(self._fields.keys())-1
        except:
            raise Exception("This is an pure abstract class!")
        self._prepare()
        self.load()
        self._completeSignalSets = 0
        self._anomalies = []
        self._percentage = 0
        self._processThread = None
        self._t0 = None
        self._interrupt = Event()
        self._interrupt.clear()

    ####
    #--- preparation area
    def load(self):
        with open(self._filename,'rb') as file:
            raw = file.read()
            #as the contents are elements of 16 bits:
        size = len(raw)/2
        self.info("Read %s, found %d elements"%(self._filename,size))
        self._values = np.ndarray(buffer=raw,
                                  shape=size,
                                  dtype=np.int16)
        try:#normal way
            self._iterator = np.nditer(self._values)
        except:#backward compatibility to numpy 1.3.0
            self._iterator = nditer(self._values)
        self._offset = self._nextSeparator()
        self.info("First tag found in position %d. Sets size %d "\
                  "(including the separator)"
                  %(self._offset,self._nsignals+1))
    
    def _prepare(self):
        self.prepareSignalSet()
    
    def hasI(self,name):
        '''Check if with the given name, in the SignalFields dictionary there
           is a key with 'I' and it points to a field known of this type 
           (Loops or diag).
        '''
        return SignalFields[name].has_key('I') and \
               SignalFields[name]['I'] in self._fields.keys()
    def hasQ(self,name):
        '''Check if with the given name, in the SignalFields dictionary there
           is a key with 'Q' and it points to a field known of this type 
           (Loops or diag).
        '''
        return SignalFields[name].has_key('Q') and \
               SignalFields[name]['Q'] in self._fields.keys()
    def prepareSignalSet(self):
        for keyName in SignalFields.keys():
            if self.hasI(keyName) and self.hasQ(keyName):
                self._signals[keyName] = []
        self.debug("prepared the signal set: %s"%(self._signals.keys()))
    #--- done preparation area
    ####
    
    ####
    #--- processing area
    def process(self):
        if self._processThread != None and \
           self._processThread.isAlive() == True:
            self.warning("received a process command when it's "\
                         "already in progress")
            return
        if self._processThread == None:
            self._processThread = Thread(target=self.doProcessThreading,
                                         name=self._name+"Thread")
        if self._interrupt.isSet():
            self._interrupt.clear()
        self._processThread.start()
    
    def doProcessThreading(self):
        self._t0 = time()
        self._percentage = 0
        self.step.emit()
        try:
            while not (self._isEndOfFile() or self._interrupt.isSet()):
                if self._isCompleteSignalSet():
                    self._completeSignalSets += 1
                    self.processSignalSet()
                    self._nextSeparator()
                else:
                    prevSeparator = self._iterator.iterindex
                    nextSeparator = self._nextSeparator()
                    if nextSeparator == -1:
                        break
                    distance = nextSeparator-prevSeparator
                    self._offset = (self._offset+distance)%(self._nsignals+1)
                    self.warning("found an anomaly in %d: distance %d != %d "\
                                 "(new offset %d)"
                                 %(prevSeparator,distance,
                                   self._nsignals,self._offset))
                    self._anomalies.append(distance)
                    #Anomalies are discarded 
                    #(nothing to do with the set of signals.
                
                #FIXME:this is for debug, to be eliminated
                if self._iterator.iterindex%1e6 == self._offset:
                    current = self._iterator.iterindex
                    total = float(self._iterator.itersize)
                    self._percentage = int((current/total)*100)
                    #but it may be used to emit signals about 
                    #the progress of the process
                    self.info("we are at %d%% (%d of %d)"
                              %(self._percentage,self._iterator.iterindex,
                                self._iterator.itersize))
                    self.step.emit()
            self.rate
            self.step.emit()
            if self._isEndOfFile():
                self._percentage = 100
                self.postprocess()
                self.done.emit()
                self.info("Process file completed: 100%")
            else:
                self.aborted.emit()
                self.warning("Process aborted: %d%%"%(self._percentage))
            self.info("Process has take %g seconds"%(time()-self._t0))
            return True
        except Exception,e:
            self.error("file process cannot be completed! Exception: %s"%(e))
            traceback.print_exc()
            self.aborted.emit()
            return False
    #--- done processing area
    ####
    
    ####
    #--- post processing area
    def abort(self):
        self.warning("Process interruption received!")
        self._interrupt.set()
    
    def postprocess(self):
        for signal in self._signals.keys():
            if SignalFields[signal].has_key('I') and \
                                             SignalFields[signal].has_key('Q'):
                self._signals[signal] = np.array(self._signals[signal])

    def getSignal(self,key):
        if not key in self._signals.keys():
            raise Exception("Unknown signal")
        if type(self._signals[key]) == list:
            raise Exception("Data not yet available")
        return copy(self._signals[key])
    #--- done postprocessing area
    ####
    
    ####
    #--- auxiliar resources area
    @property
    def percentage(self):
        self.info("Percentage requested: %d%%"%(self._percentage))
        return self._percentage
    
    @property
    def anomalies(self):
        return self._anomalies
    
    @property
    def rate(self):
        nAnomalies = len(self._anomalies)
        total = float(nAnomalies+self._completeSignalSets)
        if total > 0:
            rate = nAnomalies/total
            self.info("At percentage %d%% found %d anomalies (rate=%2.4f%%)"
                      %(self._percentage,nAnomalies,rate))
            return rate
        return 0
    def isProcessing(self):
        return self._processThread.isAlive() and not self._percentage == 100
    #--- done auxiliar resources area
    ####
    
    ####
    #--- internal area
    def _nextSeparator(self):
        #when this method is called from a separator, move next. do-while like
        if self._iterator.value == SEPARATOR:
            #check if next can be where is expected
            if self._isCompleteSignalSet():
                self._iterator.iterindex += self._nsignals+1
                return self._iterator.iterindex
            else:
                self._iterator.next()
        #iterate until found the next
        while not self._iterator.value == SEPARATOR:
            try:
                self._iterator.next()
            except StopIteration,e:
                #this means that the end of the array has been reached
                return -1
            except Exception,e:
                self.error("Exception searching next separator")
                return -1
        return self._iterator.iterindex
    
    def _isCompleteSignalSet(self):
        nextExpectedSeparator = self._iterator.iterindex+self._nsignals+1
        try:
            if self._values[nextExpectedSeparator] == SEPARATOR:
                return True
            return False
        except Exception,e:
            return False
    
    def _isEndOfFile(self):
        try:
            return self._iterator.iterindex + self._nsignals \
                                                      > self._iterator.itersize
        except ValueError,e:
            if e == 'Iterator is past the end':
                self.debug("End of File with known exception")
            else:
                self.warning("Iterator value error: %s"%(e))
        except Exception,e:
            self.error("Exception checking EoF: %s"%(e))
        return True
    #--- done internal area
    ####

class LoopsFile(FdlFile):
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        self._fields = LoopsFields
        FdlFile.__init__(self,filename)
        self._name = 'Loops'

    ####
    #--- preparation area
    def prepareSignalSet(self):
        for keyName in SignalFields.keys():
            if self.hasI(keyName) and self.hasQ(keyName):
                self._signals[keyName] = []
        self.debug("prepared the signal set: %s"%(self._signals.keys()))
    def processSignalSet(self):
        for keyName in self._signals.keys():
            I_tag = SignalFields[keyName]['I']
            I = self._values[self._iterator.iterindex+LoopsFields[I_tag]]
            Q_tag = SignalFields[keyName]['Q']
            Q = self._values[self._iterator.iterindex+LoopsFields[Q_tag]]
            Ampl = (sqrt((I**2)+(Q**2)))/32767*1000
            self._signals[keyName].append(Ampl)
    #--- done preparation area
    ####

class DiagnosticsFile(FdlFile):
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        self._fields = DiagFields
        FdlFile.__init__(self,filename,loadErrorRate)
        self._name = 'Diag'
    def hasI(self,name):
        return SignalFields[name].has_key('I') and \
               SignalFields[name]['I'] in DiagFields.keys()
    def hasQ(self,name):
        return SignalFields[name].has_key('Q') and \
               SignalFields[name]['Q'] in DiagFields.keys()
    ####
    #--- preparation area

    def processSignalSet(self):
        for keyName in self._signals.keys():
            I_tag = SignalFields[keyName]['I']
            I = self._values[self._iterator.iterindex+DiagFields[I_tag]]
            Q_tag = SignalFields[keyName]['Q']
            Q = self._values[self._iterator.iterindex+DiagFields[Q_tag]]
            Ampl = (sqrt((I**2)+(Q**2)))/32767*1000
            self._signals[keyName].append(Ampl)
    #--- done preparation area
    ####

####
#---Test area

from pylab import *
def plotter():
    '''This is NOT a taurus gui plotter, that's for testing purposes to plot
       using matplotlib.
    '''
    from matplotlib.pyplot import draw, figure, show
    f1 = figure()
    af1 = f1.add_subplot(111)
    for k in descriptor._signals.keys():
        x = []
        for i,e in enumerate(descriptor._signals[k]):
            x.append(i)
        af1.plot(descriptor._signals[k])
        xlabel('Time')
        ylabel(k)
    plt.title("Test")

if __name__ == "__main__":
    import sys,time
    if len(sys.argv) != 2:
        print("Give a path to a sample file as paramenter")
        sys.exit(-1)
    if sys.argv[1].split('/')[-1].startswith('Loops'):
        descriptor = LoopsFile(sys.argv[1])
    elif sys.argv[1].split('/')[-1].startswith('Diag'):
        descriptor = DiagnosticsFile(sys.argv[1])
    else:
        print("Unrecognized file")
        sys.exit(-2)
    descriptor.process()
    while not descriptor.percentage == 100:
        print("Main thread waiting file process (%d%%)"
              %(descriptor.percentage))
        descriptor.rate
        time.sleep(10)
    plotter()
    print("Well done! Test completed. Exiting...")
    sys.exit(0)
