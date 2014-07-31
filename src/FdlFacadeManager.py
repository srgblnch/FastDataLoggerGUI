###############################################################################
## file :               FdlFacadeManager.py
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

import taurus
from taurus.core.util import Logger
try:#normal way
    from taurus.external.qt import Qt,QtGui,QtCore
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt,QtGui
    from FdlFileParser import MyQtSignal
from PyTango import DevFailed

from FdlSignals import SignalFields
from facadeadjustments import facadeAdjustments

FACADES_SERVERNAME = 'LLRFFacade'

class FacadeManager(Logger,Qt.QObject):
    try:#normal way
        change = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        change = MyQtSignal('change')
    def __init__(self,facadeInstanceName,beamCurrent=100):
        Logger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.change._parent = self
        self._facadeInstanceName = facadeInstanceName
        self._facadeAdjustments = facadeAdjustments()
        self._beamCurrent = beamCurrent#mA
        self._facadeAttrWidgets = \
            {'CavVolt_mV':
                {'m':self._facadeAdjustments._ui.cavityVolts_mV_MValue,
                 'n':self._facadeAdjustments._ui.cavityVolts_mV_NValue},
             'CavVolt_kV':
                {'m':self._facadeAdjustments._ui.cavityVolts_kV_MValue,
                 'n':self._facadeAdjustments._ui.cavityVolts_kV_NValue},
             'FwCav_kW':
                {'c':self._facadeAdjustments._ui.FwCavCValue,
                 'o':self._facadeAdjustments._ui.FwCavOValue},
             'RvCav_kW':
                {'c':self._facadeAdjustments._ui.RvCavCValue,
                 'o':self._facadeAdjustments._ui.RvCavOValue}
            }
        try:
            dServerName = str('dserver/'+\
                              FACADES_SERVERNAME+'/'+\
                              facadeInstanceName)
            self.debug("Facade's device server name: %s"%(dServerName))
            facadeDevName = taurus.Device(dServerName).\
                                          QueryDevice()[0].split('::')[1]
            self.debug("Facade's device name: %s"%(facadeDevName))
            self.facadeDev = taurus.Device(facadeDevName)
        except Exception,e:
            self.error("Cannot prepare the facade information due to an "\
                       "exception: %s"%(e))
            return
        self._prepareFacadeParams()

    @property
    def instanceName(self):
        return self._facadeInstanceName

    def _prepareFacadeParams(self):
        self._fromFacade = {}
        for field in SignalFields.keys():
            self._fromFacade[field] = {}
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key('m') and \
               SignalFields[field].has_key('n'):
                self._fromFacade[field]['m'] = 1
                self._fromFacade[field]['n'] = 0
            elif SignalFields[field].has_key('c') and \
                 SignalFields[field].has_key('o'):
                self._fromFacade[field]['c'] = 1
                self._fromFacade[field]['o'] = 0
            #TODO: quadratics

    def populateFacadeParams(self):
        requiresFacadeAdjustments = False
        for field in SignalFields.keys():
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key('m') and \
               SignalFields[field].has_key('n'):
                mAttr = SignalFields[field]['m']
                nAttr = SignalFields[field]['n']
                m = self.readAttr(mAttr)
                n = self.readAttr(nAttr)
                if m != None and n != None:
                    self.info("For signal %s: m = %g, n = %g"%(field,m,n))
                    self._fromFacade[field]['m'] = m
                    self._fromFacade[field]['n'] = n
                else:
                    requiresFacadeAdjustments = True
            elif SignalFields[field].has_key('c') and \
                 SignalFields[field].has_key('o'):
                cAttr = SignalFields[field]['c']
                oAttr = SignalFields[field]['o']
                c = self.readAttr(cAttr)
                o = self.readAttr(oAttr)
                if c != None and o != None:
                    self.info("For signal %s: c = %g, o = %g"%(field,c,o))
                    self._fromFacade[field]['c'] = c
                    self._fromFacade[field]['o'] = o
                else:
                    requiresFacadeAdjustments = True
        return requiresFacadeAdjustments

    def readAttr(self,attrName):
        try:
            return self.facadeDev[attrName].value
        except DevFailed,e:
            if len(e.args) == 2:
                msg = e[1].desc
            else:
                msg = e[0].desc
            self.warning("Not possible to read %s's value (%s)"%(attrName,msg))
        except Exception,e:
            self.error("Wasn't possible to get the facade's attribute %s: "\
                                 "%s"%(attrName,e))
        return None

    def doFacadeAdjusments(self):
        if self._facadeAdjustments == None:
            self._facadeAdjustments = facadeAdjustments()
        self._facadeAdjustments.setWindowTitle("Facade's parameters")
        Qt.QObject.connect(self.getOkButton(),
                           Qt.SIGNAL('clicked(bool)'),self.okFacade)
        Qt.QObject.connect(self.getCancelButton(),
                           Qt.SIGNAL('clicked(bool)'),self.cancelFacade)
#        self.prepareBeamCurrent()
        #use _fromFacade to populate widgets
        for field in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[field].has_key('m') and \
               self._fromFacade[field].has_key('n'):
                m = self._fromFacade[field]['m']
                n = self._fromFacade[field]['n']
                self.debug("Information to the user, signal %s: m = %g, n = %g"
                           %(field,m,n))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field]['m'].setValue(m)
                    self._facadeAttrWidgets[field]['n'].setValue(n)
            if self._fromFacade[field].has_key('c') and \
               self._fromFacade[field].has_key('o'):
                c = self._fromFacade[field]['c']
                o = self._fromFacade[field]['o']
                self.debug("Information to the user, signal %s: c = %g, o = %g"
                           %(field,c,o))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field]['c'].setValue(c)
                    self._facadeAttrWidgets[field]['o'].setValue(o)
        self._facadeAdjustments.show()
    
#    def prepareBeamCurrent(self):
#        self._facadeAdjustments._ui.beamCurrentValue.setValue(self._beamCurrent)
    def getBeamCurrent(self):
#        try:
#            if self._beamCurrent != self._facadeAdjustments._ui.\
#                                                      beamCurrentValue.value():
#                self._beamCurrent = self._facadeAdjustments._ui.\
#                                                       beamCurrentValue.value()
#        except Exception,e:
#            self.warning("Error getting the beam current: %s"%(e))
        return self._beamCurrent
    
    def getOkButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                              button(QtGui.QDialogButtonBox.Ok)
    def okFacade(self):
        #self.info("New parameters adjusted by hand by the user!")
#        self.getBeamCurrent()
        hasAnyoneChanged = False
        for field in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[field].has_key('m') and \
               self._fromFacade[field].has_key('n'):
                m = float(self._facadeAttrWidgets[field]['m'].value())
                n = float(self._facadeAttrWidgets[field]['n'].value())
                if self._fromFacade[field]['m'] != m or \
                   self._fromFacade[field]['n'] != n:
                    self.info("Changes from the user, signal %s: m = %g, n = %g"
                              %(field,m,n))
                    self._fromFacade[field]['m'] = m
                    self._fromFacade[field]['n'] = n
                    hasAnyoneChanged = True
            elif self._fromFacade[field].has_key('c') and \
                 self._fromFacade[field].has_key('o'):
                c = float(self._facadeAttrWidgets[field]['c'].value())
                o = float(self._facadeAttrWidgets[field]['o'].value())
                if self._fromFacade[field]['c'] != c or \
                   self._fromFacade[field]['o'] != o:
                    self.info("Changes from the user, signal %s: c = %g, o = %g"
                              %(field,c,o))
                    self._fromFacade[field]['c'] = c
                    self._fromFacade[field]['o'] = o
                    hasAnyoneChanged = True
        if hasAnyoneChanged:
            self.change.emit()
        self._facadeAdjustments.hide()
    def getCancelButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                          button(QtGui.QDialogButtonBox.Cancel)
    def cancelFacade(self):
        self.info("Canceled parameter adjusted by hand by the user!")
        if hasattr(self,'_facadeAdjustments') and \
           self._facadeAdjustments != None:
            self._facadeAdjustments.hide()
            self._facadeAdjustments = None

    def getMandNs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key('m') and \
               self._fromFacade[signalName].has_key('n'):
                return (self._fromFacade[signalName]['m'],
                        self._fromFacade[signalName]['n'])
        else:
            raise Exception("signal %s hasn't M&N's"%(signalName))

    def getCandOs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key('c') and \
               self._fromFacade[signalName].has_key('o'):
                return (self._fromFacade[signalName]['c'],
                        self._fromFacade[signalName]['o'])
        else:
            return (None,None)#FIXME
        
