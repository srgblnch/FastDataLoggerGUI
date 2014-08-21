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
from FdlLogger import *
try:#normal way
    from taurus.external.qt import Qt,QtGui,QtCore
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qt,QtGui
from PyTango import DevFailed

from FdlSignals import *
from facadeadjustments import facadeAdjustments

FACADES_SERVERNAME = 'LLRFFacade'

class FacadeManager(FdlLogger,Qt.QObject):
    try:#normal way
        updated = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        updated = MyQtSignal('change')
    def __init__(self,facadeInstanceName,beamCurrent=100):
        FdlLogger.__init__(self)
        try:#normal way
            Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QObject.__init__(self)
            self.updated._parent = self
        self._facadeInstanceName = facadeInstanceName
        self._facadeAdjustments = facadeAdjustments()
        self._beamCurrent = beamCurrent#mA
        self._facadeAttrWidgets = \
            {'CavVolt_mV':
                {slope: self._facadeAdjustments._ui.cavityVolts_mV_MValue,
                 offset:self._facadeAdjustments._ui.cavityVolts_mV_NValue},
             'CavVolt_kV':
                {slope: self._facadeAdjustments._ui.cavityVolts_kV_MValue,
                 offset:self._facadeAdjustments._ui.cavityVolts_kV_NValue},
             'FwCav_kW':
                {couple:self._facadeAdjustments._ui.FwCavCValue,
                 offset:self._facadeAdjustments._ui.FwCavOValue},
             'RvCav_kW':
                {couple:self._facadeAdjustments._ui.RvCavCValue,
                 offset:self._facadeAdjustments._ui.RvCavOValue}
            }
        try:
            dServerName = str('dserver/'+\
                              FACADES_SERVERNAME+'/'+\
                              facadeInstanceName)
            self.debug("Facade's device server name: %s"%(dServerName))
            dServer = taurus.Device(dServerName)
            facadeDevName = dServer.QueryDevice()[0].split('::')[1]
            self.debug("Facade's device name: %s"%(facadeDevName))
            self.facadeDev = taurus.Device(facadeDevName)
        except Exception,e:
            self.error("Cannot prepare the facade information due to an "\
                       "exception: %s"%(e))
            self.facadeDev = None
        self._prepareFacadeParams()

    @property
    def instanceName(self):
        return self._facadeInstanceName

    def _prepareFacadeParams(self):
        self._fromFacade = {}
        for field in SignalFields.keys():
            self._fromFacade[field] = {}
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key(slope) and \
               SignalFields[field].has_key(offset):
                self._fromFacade[field][slope] = 1
                self._fromFacade[field][offset] = 0
            elif SignalFields[field].has_key(couple) and \
                 SignalFields[field].has_key(offset):
                self._fromFacade[field][couple] = 1
                self._fromFacade[field][offset] = 0
            #TODO: quadratics

    def populateFacadeParams(self):
        requiresFacadeAdjustments = False
        for field in SignalFields.keys():
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key(slope) and \
               SignalFields[field].has_key(offset):
                mAttr = SignalFields[field][slope]
                nAttr = SignalFields[field][offset]
                m = self.readAttr(mAttr)
                n = self.readAttr(nAttr)
                if m != None and n != None:
                    self.info("For signal %s: m = %g, n = %g"%(field,m,n))
                    self._fromFacade[field][slope] = m
                    self._fromFacade[field][offset] = n
                else:
                    requiresFacadeAdjustments = True
            elif SignalFields[field].has_key(couple) and \
                 SignalFields[field].has_key(offset):
                cAttr = SignalFields[field][couple]
                oAttr = SignalFields[field][offset]
                c = self.readAttr(cAttr)
                o = self.readAttr(oAttr)
                if c != None and o != None:
                    self.info("For signal %s: c = %g, o = %g"%(field,c,o))
                    self._fromFacade[field][couple] = c
                    self._fromFacade[field][offset] = o
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
            if self._fromFacade[field].has_key(slope) and \
               self._fromFacade[field].has_key(offset):
                m = self._fromFacade[field][slope]
                n = self._fromFacade[field][offset]
                self.debug("Information to the user, signal %s: m = %g, n = %g"
                           %(field,m,n))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field][slope].setValue(m)
                    self._facadeAttrWidgets[field][offset].setValue(n)
            if self._fromFacade[field].has_key(couple) and \
               self._fromFacade[field].has_key(offset):
                c = self._fromFacade[field][couple]
                o = self._fromFacade[field][offset]
                self.debug("Information to the user, signal %s: c = %g, o = %g"
                           %(field,c,o))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field][couple].setValue(c)
                    self._facadeAttrWidgets[field][offset].setValue(o)
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
            if self._fromFacade[field].has_key(slope) and \
               self._fromFacade[field].has_key(offset):
                m = float(self._facadeAttrWidgets[field][slope].value())
                n = float(self._facadeAttrWidgets[field][offset].value())
                if self._fromFacade[field][slope] != m or \
                   self._fromFacade[field][offset] != n:
                    self.info("Changes from the user, signal %s: m = %g, n = %g"
                              %(field,m,n))
                    self._fromFacade[field][slope] = m
                    self._fromFacade[field][offset] = n
                    hasAnyoneChanged = True
            elif self._fromFacade[field].has_key(couple) and \
                 self._fromFacade[field].has_key(offset):
                c = float(self._facadeAttrWidgets[field][couple].value())
                o = float(self._facadeAttrWidgets[field][offset].value())
                if self._fromFacade[field][couple] != c or \
                   self._fromFacade[field][offset] != o:
                    self.info("Changes from the user, signal %s: c = %g, o = %g"
                              %(field,c,o))
                    self._fromFacade[field][couple] = c
                    self._fromFacade[field][offset] = o
                    hasAnyoneChanged = True
        if hasAnyoneChanged:
            self.updated.emit()
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
            if self._fromFacade[signalName].has_key(slope) and \
               self._fromFacade[signalName].has_key(offset):
                return (self._fromFacade[signalName][slope],
                        self._fromFacade[signalName][offset])
        else:
            raise Exception("signal %s hasn't M&N's"%(signalName))

    def getCandOs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key(couple) and \
               self._fromFacade[signalName].has_key(offset):
                return (self._fromFacade[signalName][couple],
                        self._fromFacade[signalName][offset])
        else:
            return (None,None)#FIXME
        
