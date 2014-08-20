###############################################################################
## file :               FdlLogger.py
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

from os import getloadavg
from sys import getsizeof
from taurus.core.util import Logger
import numpy
import types
import resource
import gc

class MemoryProfile:
    def __init__(self):
        self._unitsSort = ['B','KB','MB','GB']
        self._unitsDict = {'GB': 1073741824, 'MB': 1048576, 'KB': 1024}

    def getProcessMemoryUse(self,unit='kB'):
        memUse_in_kB = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if unit.upper() == 'KB':
            return memUse_in_kB
        else:
            return self._convert2binaryPrefix(memUse_in_kB*1024,unit)

    def getProcessSwapUse(self,unit='kB'):
        #FIXME: this is always returning a 0, even in /proc/`pid`/status is 
        #       shown a positive number
        swapUse_in_kB = resource.getrusage(resource.RUSAGE_SELF).ru_nswap
        if unit.upper() == 'KB':
            return swapUse_in_kB
        else:
            return self._convert2binaryPrefix(swapUse_in_kB*1024,unit)

    def isProcessSwapping(self):
        #FIXME: as the method used to get the swap used size is not working,
        #       this method is useless until it's fix.
        return bool(self.getProcessSwapUse())

    def getMachineLoad(self):
        return getloadavg()

    def callCarbageCollector(self):
        gc.collect()

    def _convert2binaryPrefix(self,bytes,unit='kB'):
        '''given a value of Bytes, convert to some binary prefix'''
        try:
            return bytes / self._unitsDict[unit.upper()]
        except Exception,e:
            print(".. %s"%(e))
            raise Exception("Unit must be in %s, not %s"
                            %(self._unitsSort,unit))
    def biggestBinaryPrefix(self,value,unit='B'):
        '''given a value in some binary prefix of bytes, convert to the highest
           non zero prefix.
        '''
        #from unit to any upper
        unit = unit.upper()
        value = float(value)
        if not unit in self._unitsSort:
            raise Exception("Unit must be in %s, not %s"
                            %(self._unitsSort,unit))
        baseUnitIdx = self._unitsSort.index(unit)
        while baseUnitIdx < len(self._unitsSort):
            if int(value/1024) == 0:
                return value,self._unitsSort[baseUnitIdx]
            else:
                value = float(value)/1024
                baseUnitIdx+=1
        return value*1024,self._unitsSort[baseUnitIdx-1]

    def getObjectSize(self,unit='kB'):
        accumulated = 0
        for attribute in dir(self):
            try:
                if not attribute.startswith('__'):
                    obj = getattr(self,attribute)
                    accumulated += self._getsizeof(obj)
            except:
                pass
        return self._convert2binaryPrefix(accumulated,unit)
    def getSubobjectSize(self,obj,unit='kB'):
        accumulated = self._getsizeof(obj)
        return self._convert2binaryPrefix(accumulated, unit)

    def _getsizeof(self,attribute):
        if type(attribute) == types.DictionaryType:
            return self._dict_size_(attribute)
        elif type(attribute) == numpy.ndarray:
            return attribute.nbytes
        elif type(attribute) == types.FunctionType:
            return 0
        else:
            return getsizeof(attribute)

    def _dict_size_(self,dictionary):
        accumulated = 0
        for key in dictionary.keys():
            accumulated += self._getsizeof(dictionary[key])
        return accumulated

class FdlLogger(Logger,MemoryProfile):
    def __init__(self):
        Logger.__init__(self)
        MemoryProfile.__init__(self)

    def memory(self):
        if self.getLogLevel() == Logger.Debug:
            objSize,objUnit = self.biggestBinaryPrefix(self.getObjectSize(),
                                                       'kB')
            procMem = self.getProcessMemoryUse()
            procSize,procUnit = self.biggestBinaryPrefix(procMem,'kB')
            swapUse = self.getProcessSwapUse()
            swapSize,swapUnit = self.biggestBinaryPrefix(swapUse,'kB')
            gcCounts = gc.get_count()
            gcThreshold = gc.get_threshold()
            load = "%1.1f,%1.1f,%1.1f"%(self.getMachineLoad())
            if swapSize > 0:
                stdoutput = self.warning
            else:
                stdoutput = self.debug
            stdoutput("self size %2.2f %s, Process %2.2f %s (swap %2.2f %s) "\
                       "(gc counts %s, threshold %s) (load:%s)"
                       %(objSize,objUnit,procSize,procUnit,swapSize,swapUnit,
                         gcCounts,gcThreshold,load))
