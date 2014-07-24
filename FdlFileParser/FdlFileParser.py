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
from taurus.external.qt import Qt,QtGui,QtCore
from threading import Thread,Event
from math import sqrt

SEPARATOR = 0x7FFF
LOAD_ERROR_RATE = 0.01

class FdlFile(Logger,Qt.QObject):
    step = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal()
    
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        Logger.__init__(self)
        Qt.QObject.__init__(self, parent=None)
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
        self._interrupt = Event()
        self._interrupt.clear()

    def load(self):
        with open(self._filename,'rb') as file:
            raw = file.read()
            #as the contents are elements of 16 bits:
        size = len(raw)/2
        self.info("Read %s, found %d elements"%(self._filename,size))
        self._values = np.ndarray(buffer=raw,
                                  shape=size,
                                  dtype=np.int16)
        self._iterator = np.nditer(self._values)
        self._offset = self._nextSeparator()
        self.info("First tag found in position %d. Sets size %d (including the separator)"
                  %(self._offset,self._nsignals+1))
    
    def _prepare(self):
        self.prepareSignalSet()
        #for i in range(1,self._nsignals):
        #    self._signals[self._fields[i]] = []#FIXME: better a np structure
    
    def process(self):
        if self._processThread != None and self._processThread.isAlive() == True:
            self.warning("received a process command when it's "\
                         "already in progress")
            return
        if self._processThread == None:
            self._processThread = Thread(target=self.doProcessThreading)
        if self._interrupt.isSet():
            self._interrupt.clear()
        self._processThread.start()
    
    def abort(self):
        self._interrupt.set()
    
    def doProcessThreading(self):
        self._percentage = 0
        self.step.emit()
        while not self._isEndOfFile() or self._interrupt.isSet():
            if self._isCompleteSignalSet():
                self._completeSignalSets += 1
                #for i in range(1,self._nsignals):
                #    self._signals[self._fields[i]].\
                #              append(self._values[self._iterator.iterindex+i])
                #    #FIXME: This eats the memory!!!
                self.processSignalSet()
                self._nextSeparator()
            else:
                prevSeparator = self._iterator.iterindex
                nextSeparator = self._nextSeparator()
                distance = nextSeparator-prevSeparator
                self._offset = self._offset+distance%(self._nsignals+1)
                self.warning("found an anomaly in %d: distance %d != %d "\
                             "(new offset %d)"
                             %(prevSeparator,distance,self._nsignals,self._offset))
                self._anomalies.append(distance)
                #Anomalies are discarded (nothing to do with the set of signals.
            
            #FIXME:this is for debug, to be eliminated
            if self._iterator.iterindex%1e6 == self._offset:
                current = self._iterator.iterindex
                total = float(self._iterator.itersize)
                self._percentage = int((current/total)*100)
                #but it may be used to emit signals about the progress of the process
                self.info("we are at %d%% (%d of %d)"
                          %(self._percentage,self._iterator.iterindex,
                            self._iterator.itersize))
                self.step.emit()
        self._percentage = 100
        self.rate
        self.step.emit()
        self.complete.emit()
        self.info("Process file completed: 100%")
        return True
    
    @property
    def percentage(self):
        self.info("Percentage requested: %d%%"%(self._percentage))
        return self._percentage
    
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
    
    def _nextSeparator(self):
        #when this method is called from a separator, move next. do-while like
        if self._iterator.value == SEPARATOR:
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
        return self._iterator.iterindex
    
    def _isCompleteSignalSet(self):
        nextExpectedSeparator = self._iterator.iterindex+self._nsignals+1
        if self._values[nextExpectedSeparator] == SEPARATOR:
            return True
        return False
    
    def _isEndOfFile(self):
        return self._iterator.iterindex + self._nsignals > self._iterator.itersize

#Correspondence of signals structure. 
#Section 6.1 table 5 of the documentation v2 from 20140620
LoopsFields = {'separator':     0,'FwCavPhase':    1,#0
               'FwIOT1_I':      2,'FwIOT1_Q':      3,#1
               'FwIOT2_I':      4,'FwIOT2_Q':      5,#2
               'RvCircIn_I':    6,'RvCircIn_Q':    7,#3
               'FwLoad_I':      8,'FwLoad_Q':      9,#4
               'RvCav_I':      10,'RvCav_Q':      11,#5
               'MO_I':         12,'MO_Q':         13,#6
               'CavFiltered_I':14,'CavFiltered_Q':15,#7
               'AmpCell2':     16,'AmpCell4':     17,#8
               'Cav_I':        18,'Cav_Q':        19,#9
               'Control_I':    20,'Control_Q':    21,#10
               'Error_I':      22,'Error_Q':      23,#11
               'ErroAccum_I':  24,'ErrorAccum_Q': 25,#12
               'FwCav_I':      26,'FwCav_Q':      27,#13
               'TuningDephase':28,'CavityPhase':  29,#14
               'Reference_I':  30,'Reference_Q':  31}#15
#for elements with I&Q, its amplitude must be calculated: sqrt(I^2+Q^2)
#for elements with Facade conversion, its formula must be applied.
SignalFields = ['CavVolt_kV']

class LoopsFile(FdlFile):
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        self._fields = LoopsFields
        FdlFile.__init__(self,filename)
    def prepareSignalSet(self):
        self._signals['CavVolt_kV'] = []
        #TODO: more signals
    def processSignalSet(self):
        self._signals['CavVolt_kV'].append(self.CavVolt_kV())
        #TODO: more signals
    def CavVolt_kV(self):
        #start with Amp_mV = sqrt(Cav_I**2 + Cav_Q**2)
        Cav_I = self._values[self._iterator.iterindex+LoopsFields['Cav_I']]
        Cav_Q = self._values[self._iterator.iterindex+LoopsFields['Cav_Q']]
        Amp_mV = sqrt((Cav_I**2)+(Cav_Q**2))/32767*1000
        #TODO: get facades m&n
        m = 1.334
        n = 3.7903
        return (Amp_mV-n)/m

#Correspondence of signals structure. 
#Section 6.1 table 6 of the documentation v2 from 20140620
DiagFields = { 0:'separator',   1:'??',         #0  #FIXME: what about this position 1!!
               2:'SSA1Input_I', 3:'SSA1Input_Q',#1
               4:'SSA2Input_I', 5:'SSA2Input_Q',#2
               6:'FwCircIn_I',  7:'FwCircIn_Q', #3
               8:'FwCircOut_I', 9:'FwCircOut_Q',#4
              10:'RvCircOut_I',11:'RvCircOut_Q',#5
              12:'RvLoad_I',   13:'RvLoad_Q',   #6
              14:'RvIOT1_I',   15:'RvIOT1_Q',   #7
              16:'RvIOT2_I',   17:'RvIOT2_Q'    #8
             }

class DiagnosticsFile(FdlFile):
    def __init__(self,filename,loadErrorRate=LOAD_ERROR_RATE):
        self._fields = DiagFields
        FdlFile.__init__(self,filename,loadErrorRate)
    def prepareSignalSet(self):
        pass
    def processSignalSet(self):
        pass

####
#---Test area

from pylab import *
def plotter():
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
        #print("Main thread waiting file process (%d%%)"%(descriptor.percentage))
        descriptor.rate
        time.sleep(10)
    plotter()
    print("Well done! Test completed. Exiting...")
    sys.exit(0)
