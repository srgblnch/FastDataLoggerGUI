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

from FdlLogger import *
from FdlSignals import *

import numpy as np
import scipy as sp
from threading import Thread,Event
from math import sqrt
from copy import copy
import traceback
import time

try:#normal way
    from taurus.external.qt import Qt,QtGui,QtCore,Qwt5
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt,QtGui,QtCore,Qwt5

SEPARATOR = 0x7FFF
LOAD_ERROR_RATE = 0.01 # as a %
#in 128MB file there are ~67e6 samples, and this (unused) threshold 
#means 6e3 errors in a single file.

class FdlFile(FdlLogger,Qt.QObject):
    try:#normal way
        step = QtCore.pyqtSignal()
        done = QtCore.pyqtSignal()
        aborted = QtCore.pyqtSignal()
        swapping = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        step = MyQtSignal('step')
        done = MyQtSignal('done')
        aborted = MyQtSignal('aborted')
        swapping = MyQtSignal('swapping')
    
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        FdlLogger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.step._parent = self
            self.done._parent = self
            self.aborted._parent = self
            self.swapping._parent = self
        self._standby = Event()
        self._standby.clear()
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
        self.info("Read %s, found %d elements (%d bytes)"
                  %(self._filename,size,self._getsizeof(raw)))
        self._values = np.ndarray(buffer=raw,
                                  shape=size,
                                  dtype=np.int16)
        del raw
        self.debug("load data converted to a np.ndarray: %d bytes"
                   %(self._getsizeof(self._values)))
        try:#normal way
            self._iterator = np.nditer(self._values)
        except:#backward compatibility to numpy 1.3.0
            self._iterator = nditer(self._values)
        self._offset = self._nextSeparator()
        self.info("First tag found in position %d. Sets size %d "\
                  "(including the separator)"
                  %(self._offset,self._nsignals+1))
        self.memory()
    
    def sizeofSignals(self):
        self.debug("%s signals mean %d kB"
                   %(len(self._signals.keys()),
                     self._getsizeof(self._signals)/1024))
    
    def _prepare(self):
        self.prepareSignalSet()
    
    def hasFileField(self,name):
        '''Check if the given name has a field item in the SignalFields 
           dictionary and it's also present in the fields for this type of 
           FDL file (Loops|Diag).
        '''
        return SignalFields.has_key(name) and \
               SignalFields[name].has_key(FIELD_) and \
               SignalFields[name][FIELD_] in self._fields.keys()

    def hasIandQ(self,name):
        '''Check if the given name has a pair of items in the SignalFields 
           dictionary describing I&Q to calculate an amplitude from Is&Qs 
           collected on this FDL file type (Loops|Diag).
        '''
        hasI = SignalFields[name].has_key(I_) and \
               self._signals.has_key(SignalFields[name][I_])
        hasQ = SignalFields[name].has_key(Q_) and \
               self._signals.has_key(SignalFields[name][Q_])
        #self.debug("signal %s hasI=%s and hasQ=%s"%(name,hasI,hasQ))
        return hasI and hasQ

    def prepareSignalSet(self):
        for keyName in SignalFields.keys():
            if self.hasFileField(keyName):
                self._signals[keyName] = []
        self.info("prepared the signal set (%d): %s"
                  %(len(self._signals.keys()),self._signals.keys()))
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
    
    def isProcessing(self):
        return self._processThread.isAlive() and not self._percentage == 100
    
    def doProcessThreading(self):
        self._t0 = time.time()
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
                #but it may be used to emit signals about 
                #the progress of the process
                current = self._iterator.iterindex
                total = float(self._iterator.itersize)
                if self._percentage != int((current*100)/total):
                    self._percentage = int((current*100)/total)
                    #if True: #self._iterator.iterindex%1e6 == self._offset:
                    self.info("we are at %d%% (%d of %d with %d offset)"
                              %(self._percentage,self._iterator.iterindex,
                                self._iterator.itersize,self._offset))
                    self.sizeofSignals()
                    self.step.emit()
                    self.memory()
                    if self.isProcessSwapping():
                        self.swapping.emit()
                        self._standby.set()
                        while self._standby.isSet():
                            time.sleep(1)
            self.rate
            self.step.emit()
            if self._isEndOfFile():
                self._percentage = 100
                self.postprocess()
                self.done.emit()
                self.debug("Process file completed: 100%")
            else:
                self.aborted.emit()
                self.warning("Process aborted: %d%%"%(self._percentage))
            self.info("Process has take %g seconds"%(time.time()-self._t0))
            self.memory()
            return True
        except Exception,e:
            self.error("file process cannot be completed! Exception: %s"%(e))
            traceback.print_exc()
            self.aborted.emit()
            return False
        
    def processSignalSet(self):
        for keyName in self._signals.keys():
            fieldName = SignalFields[keyName][FIELD_]
            value = self._values[self._iterator.iterindex+self._fields[fieldName]]
            value = float(value)/32767*1000
            if SignalFields[keyName].has_key(TWOCOMPLEMENT_):
                if value > 512: value -= 1024
            self._signals[keyName].append(value)
    #--- done processing area
    ####
    
    ####
    #--- post processing area
    def abort(self):
        self.warning("Process interruption received!")
        self._interrupt.set()
    
    def postprocess(self):
        self.debug("clean values array (%d kB)"
                   %(self._getsizeof(self._values)/1024))
        self._values = None
        self.info("Start post-processing %d signals"%(len(self._signals.keys())))
        #Convert the collected data to numpy.array
        for signal in self._signals.keys():
            asList = self._getsizeof(self._signals[signal])
            self._signals[signal] = np.array(self._signals[signal])
            asArray = self._getsizeof(self._signals[signal])
            self.debug("Converted %s list (%d bytes) to array (%d bytes)"
                       %(signal,asList,asArray))
        #check the signal descriptors that have an amplitude conversion
        for keyName in SignalFields.keys():
            if self.hasIandQ(keyName):
                Itag = SignalFields[keyName][I_]
                Isignal = self._signals[Itag]
                Qtag = SignalFields[keyName][Q_]
                Qsignal = self._signals[Qtag]
                self.info("Signal %s has I (%s) and Q (%s)"%(keyName,Itag,Qtag))
                self._signals[keyName] = np.sqrt((Isignal**2)+(Qsignal**2))
        self.debug("Post-processed signal set (%d): %s"
                   %(len(self._signals.keys()),self._signals.keys()))
        self.sizeofSignals()
        self.memory()
    #--- done postprocessing area
    ####
    
    ####
    #--- auxiliar resources area
    @property
    def percentage(self):
        #self.debug("Percentage requested: %d%%"%(self._percentage))
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

class DiagnosticsFile(FdlFile):
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        self._fields = DiagFields
        FdlFile.__init__(self,filename,loadErrorRate)
        self._name = 'Diag'

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
        x = np.linspace(0,411,descriptor._signals[k].size)
        af1.plot(x,descriptor._signals[k])
        xlabel('Time')
        ylabel(k)
#    k = descriptor._signals.keys()[0]
#    x = np.linspace(0,411,descriptor._signals[k].Amplitude.size)
#    af1.plot(x,descriptor._signals[k].I)
#    af1.plot(x,descriptor._signals[k].Q)
#    af1.plot(x,descriptor._signals[k].Amplitude)
    xlabel('Time')
    ylabel(k)
    plt.title("Test")
    plt.show()

import json
def write2file(dictionary):
    fileName = ("%s_FdlFileParser.json"%(time.strftime("%Y%m%d_%H%M%S")))
    for key in dictionary:
        dictionary[key] = dictionary[key].tolist()
    with open(fileName,'w') as f:
        f.write(json.dumps(dictionary))

if __name__ == "__main__":
    import sys,time
    if len(sys.argv) < 2:
        print("\nGive a path to a sample file as first parameter\n"\
              "a second optional --file parameter will use json to drop data\n")
        sys.exit(-1)
    if sys.argv[1].split('/')[-1].startswith('Loops'):
        descriptor = LoopsFile(sys.argv[1])
    elif sys.argv[1].split('/')[-1].startswith('Diag'):
        descriptor = DiagnosticsFile(sys.argv[1])
    else:
        print("Unrecognized file")
        sys.exit(-2)
    descriptor.setLogLevel(descriptor.Debug)
    descriptor.process()
    while descriptor.isProcessing():
        print("Main thread waiting file process (%d%%)"
              %(descriptor.percentage))
        descriptor.rate
        time.sleep(10)
    plotter()
    if sys.argv[2] == '--file':
        write2file(descriptor._signals)
    print("Well done! Test completed. Exiting...")
    sys.exit(0)
