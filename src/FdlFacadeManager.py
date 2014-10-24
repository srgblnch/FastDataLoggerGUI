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
        updated = MyQtSignal('updated')
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
            {'CavVolt_kV':
                {SLOPE_: self._facadeAdjustments._ui.cavityVolts_kV_MValue,
                 OFFSET_:self._facadeAdjustments._ui.cavityVolts_kV_NValue},
             'FwCav_kW':
                {COUPLE_:self._facadeAdjustments._ui.FwCavCValue,
                 OFFSET_:self._facadeAdjustments._ui.FwCavOValue},
             'RvCav_kW':
                {COUPLE_:self._facadeAdjustments._ui.RvCavCValue,
                 OFFSET_:self._facadeAdjustments._ui.RvCavOValue},
             'FwLoad_kW':
                {COUPLE_:self._facadeAdjustments._ui.FwLoadCValue,
                 OFFSET_:self._facadeAdjustments._ui.FwLoadOValue},
            }
        self._prepareFacadeWidgets()
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

    def _prepareFacadeWidgets(self):
        for element in self._facadeAttrWidgets.keys():
            for parameter in [SLOPE_,COUPLE_,OFFSET_]:
                try:
                    if self._facadeAttrWidgets[element].has_key(parameter):
                        widget = self._facadeAttrWidgets[element][parameter]
                        widget.setRange(-100,100)
                except Exception,e:
                    print("\n"*10)
                    self.error("Exception %s"%(e))
                    print("\n"*10)

    def _prepareFacadeParams(self):
        self._fromFacade = {}
        for field in SignalFields.keys():
            self._fromFacade[field] = {}
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key(SLOPE_) and \
               SignalFields[field].has_key(OFFSET_):
                self._fromFacade[field][SLOPE_] = 1
                self._fromFacade[field][OFFSET_] = 0
            elif SignalFields[field].has_key(COUPLE_) and \
                 SignalFields[field].has_key(OFFSET_):
                self._fromFacade[field][COUPLE_] = 1
                self._fromFacade[field][OFFSET_] = 0
        self.debug("Prepared fromFacade structure: %s"
                   %(self._fromFacade.keys()))

    def populateFacadeParams(self):
        requiresFacadeAdjustments = False
        for field in SignalFields.keys():
            #FIXME: these ifs needs a refactoring
            if SignalFields[field].has_key(SLOPE_) and \
               SignalFields[field].has_key(OFFSET_):
                mAttr = SignalFields[field][SLOPE_]
                nAttr = SignalFields[field][OFFSET_]
                m = self.readAttr(mAttr)
                n = self.readAttr(nAttr)
                if m != None and n != None:
                    self.info("For signal %s: m = %g, n = %g"%(field,m,n))
                    self._fromFacade[field][SLOPE_] = m
                    self._fromFacade[field][OFFSET_] = n
                else:
                    requiresFacadeAdjustments = True
            elif SignalFields[field].has_key(COUPLE_) and \
                 SignalFields[field].has_key(OFFSET_):
                cAttr = SignalFields[field][COUPLE_]
                oAttr = SignalFields[field][OFFSET_]
                c = self.readAttr(cAttr)
                o = self.readAttr(oAttr)
                if c != None and o != None:
                    self.info("For signal %s: c = %g, o = %g"%(field,c,o))
                    self._fromFacade[field][COUPLE_] = c
                    self._fromFacade[field][OFFSET_] = o
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
        #use _fromFacade to populate widgets
        for field in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[field].has_key(SLOPE_) and \
               self._fromFacade[field].has_key(OFFSET_):
                m = self._fromFacade[field][SLOPE_]
                n = self._fromFacade[field][OFFSET_]
                self.debug("Information to the user, signal %s: m = %g, n = %g"
                           %(field,m,n))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field][SLOPE_].setValue(m)
                    self._facadeAttrWidgets[field][OFFSET_].setValue(n)
            if self._fromFacade[field].has_key(COUPLE_) and \
               self._fromFacade[field].has_key(OFFSET_):
                c = self._fromFacade[field][COUPLE_]
                o = self._fromFacade[field][OFFSET_]
                self.debug("Information to the user, signal %s: c = %g, o = %g"
                           %(field,c,o))
                if self._facadeAttrWidgets.has_key(field):
                    self._facadeAttrWidgets[field][COUPLE_].setValue(c)
                    self._facadeAttrWidgets[field][OFFSET_].setValue(o)
        self._facadeAdjustments.show()

    def getOkButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                              button(QtGui.QDialogButtonBox.Ok)
    def okFacade(self):
        #self.info("New parameters adjusted by hand by the user!")
        hasAnyoneChanged = False
        for field in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[field].has_key(SLOPE_) and \
               self._fromFacade[field].has_key(OFFSET_):
                m = float(self._facadeAttrWidgets[field][SLOPE_].value())
                n = float(self._facadeAttrWidgets[field][OFFSET_].value())
                if self._fromFacade[field][SLOPE_] != m or \
                   self._fromFacade[field][OFFSET_] != n:
                    self.info("Changes from the user, signal %s: m = %g, n = %g"
                              %(field,m,n))
                    self._fromFacade[field][SLOPE_] = m
                    self._fromFacade[field][OFFSET_] = n
                    hasAnyoneChanged = True
            elif self._fromFacade[field].has_key(COUPLE_) and \
                 self._fromFacade[field].has_key(OFFSET_):
                c = float(self._facadeAttrWidgets[field][COUPLE_].value())
                o = float(self._facadeAttrWidgets[field][OFFSET_].value())
                if self._fromFacade[field][COUPLE_] != c or \
                   self._fromFacade[field][OFFSET_] != o:
                    self.info("Changes from the user, signal %s: c = %g, o = %g"
                              %(field,c,o))
                    self._fromFacade[field][COUPLE_] = c
                    self._fromFacade[field][OFFSET_] = o
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

    def getMandNs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key(SLOPE_) and \
               self._fromFacade[signalName].has_key(OFFSET_):
                return (self._fromFacade[signalName][SLOPE_],
                        self._fromFacade[signalName][OFFSET_])
        else:
            raise Exception("signal %s hasn't M&N's"%(signalName))

    def getCandOs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key(COUPLE_) and \
               self._fromFacade[signalName].has_key(OFFSET_):
                return (self._fromFacade[signalName][COUPLE_],
                        self._fromFacade[signalName][OFFSET_])
        else:
            return (None,None)#FIXME

    def setBeamCurrent(self,value):
        self._beamCurrent = value

    def getBeamCurrent(self):
        return self._beamCurrent
