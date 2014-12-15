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
    from FdlFileParser import MyQtSignal
from PyTango import DevFailed

from FdlSignals import *
from facadeadjustments import facadeAdjustments
import traceback
import numpy as np
import sys

FACADES_SERVERNAME = 'LLRFFacade'

class FacadeManager(FdlLogger,Qt.QWidget):#Object):
    try:#normal way
        updated = QtCore.pyqtSignal()
    except:#backward compatibility to pyqt 4.4.3
        updated = MyQtSignal('updated')
    def __init__(self,facadeInstanceName,beamCurrent=100,
                 shuntImpedance='2*3.3*1e6'):
        FdlLogger.__init__(self)
        try:#normal way
            Qt.QWidget.__init__(self, parent=None)
            #Qt.QObject.__init__(self, parent=None)
        except:#backward compatibility to pyqt 4.4.3
            Qt.QWidget.__init__(self)
            #Qt.QObject.__init__(self)
            self.updated._parent = self
        self._facadeInstanceName = facadeInstanceName
        self._facadeAdjustments = facadeAdjustments()
        self._beamCurrent = beamCurrent#mA
        self._shuntImpedance = shuntImpedance#an string representation 
                                             #like '2*3.3*1e6'
        self._facadeAttrWidgets = \
            {'CavVolt_kV':
                {SLOPE_: self._facadeAdjustments._ui.cavityVolts_kV_MValue,
                 OFFSET_:self._facadeAdjustments._ui.cavityVolts_kV_NValue,
                 FORMULA_:self._facadeAdjustments._ui.cavityVolts_kV_Formula},
             'FwCav_kW':
                {COUPLE_:self._facadeAdjustments._ui.FwCavCValue,
                 OFFSET_:self._facadeAdjustments._ui.FwCavOValue,
                 FORMULA_:self._facadeAdjustments._ui.FwCavFormula},
             'RvCav_kW':
                {COUPLE_:self._facadeAdjustments._ui.RvCavCValue,
                 OFFSET_:self._facadeAdjustments._ui.RvCavOValue,
                 FORMULA_:self._facadeAdjustments._ui.RvCavFormula},
             'FwLoad_kW':
                {COUPLE_:self._facadeAdjustments._ui.FwLoadCValue,
                 OFFSET_:self._facadeAdjustments._ui.FwLoadOValue,
                 FORMULA_:self._facadeAdjustments._ui.FwLoadFormula},
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
        self.info("Populate Facade's parameters")
        requiresFacadeAdjustments = False
        for field in SignalFields.keys():
            #FIXME: these ifs needs a refactoring
            if self.hasMandNs(field):
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
                self._populateFormula(field)
            elif self.hasCandOs(field):
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
                self._populateFormula(field)
        return requiresFacadeAdjustments

    def _populateFormula(self,field):
        try:
            if SignalFields[field].has_key(FORMULA_):
                formula = SignalFields[field][FORMULA_]
                if self._facadeAttrWidgets.has_key(field):
                    widget = self._facadeAttrWidgets[field][FORMULA_]
                    if formula != str(widget.text()):
                        widget.setText(formula)
        except Exception,e:
            self.error("It wasn't possible to check if the facade signal %s "\
                       "has an specific formula: %s"%(field,e))
            
    def _verifyFormula(self,field):
        #FIXME: this would raise an exception to prevent the user.
        if self._facadeAttrWidgets.has_key(field):
            widget = self._facadeAttrWidgets[field][FORMULA_]
            formula = str(widget.text())
            if not SignalFields[field].has_key(FORMULA_):
                #case there is not explicit formula for it
                SignalFields[field][FORMULA_] = formula
                return True
            elif formula != SignalFields[field][FORMULA_]:
                self.info("%s formula has changed from '%s' to '%s'"
                          %(field,SignalFields[field][FORMULA_],formula))
                if not self.__formulaBeginWith(formula):
                    raise Exception("Formula has to start with 'y = '.")
                if not self.__formulaHasX(formula):
                    raise Exception("Formula requires at least one time the "\
                                    "variable 'x'")
                    return False
                if self.hasMandNs(field) and \
                                      not self.__formulaHasMandNs(formula):
                    raise Exception("Formula requires the slope tagged as 'm'"\
                                    " and the offset with an 'n'.")
                if self.hasCandOs(field) and \
                                      not self.__formulaHasCandOs(formula):
                    raise Exception("Formula requires the couple tagged as "\
                                    "'c' and the offset with an 'o'.")
                try:
                    self.__testFormulaEval(formula,field)
                except SyntaxError,e:
                    raise Exception("Formula could not be evaluated due to a "\
                                    "syntax error.")
                except Exception,e:
                    raise Exception("Formula could not be evaluated. %s"%(e))
                SignalFields[field][FORMULA_] = formula
                return True
            else:
                self.info("%s formula hasn't change, still '%s'"
                          %(field,formula))
                return False

    def __formulaBeginWith(self,formula):
        return formula.startswith("y =")
    def __formulaHasX(self,formula):
        return bool(formula.count('x'))
    def __formulaHasMandNs(self,formula):
        return bool(formula.count('m')) and bool(formula.count('n'))
    def __formulaHasCandOs(self,formula):
        return bool(formula.count('c')) and bool(formula.count('o'))
    def __testFormulaEval(self,formula,field):
        if self.__formulaHasMandNs(formula):
            m = 1;n = 0
        elif self.__formulaHasCandOs(formula):
            c = 1;n = 0
        x = np.array([0.,1,2,3])#very simple test vector
        formula.split('=')[1].strip()
        res = eval(formula)

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
        #connect signals for the buttons
        Qt.QObject.connect(self.getResetButton(),
                       Qt.SIGNAL('clicked(bool)'),self.getFacadeValues2widgets)
        Qt.QObject.connect(self.getOkButton(),
                           Qt.SIGNAL('clicked(bool)'),self.okFacade)
        Qt.QObject.connect(self.getApplyButton(),
                           Qt.SIGNAL('clicked(bool)'),self.applyFacade)
        Qt.QObject.connect(self.getCancelButton(),
                           Qt.SIGNAL('clicked(bool)'),self.cancelFacade)
        #connect signals for the QLineEdits and the QSpinBoxes
        #to apply when press enter
        listOfLineEdits = [self._facadeAdjustments._ui.ShuntImpedanceValue,
                           self._facadeAdjustments._ui.cavityVolts_kV_Formula,
                           self._facadeAdjustments._ui.FwCavFormula,
                           self._facadeAdjustments._ui.RvCavFormula,
                           self._facadeAdjustments._ui.FwLoadFormula]
        for widget in listOfLineEdits:
            Qt.QObject.connect(widget,\
                               Qt.SIGNAL('returnPressed()'),self.applyFacade)
        listOfSpinBoxes = [self._facadeAdjustments._ui.cavityVolts_kV_MValue,
                           self._facadeAdjustments._ui.cavityVolts_kV_NValue,
                           self._facadeAdjustments._ui.FwCavCValue,
                           self._facadeAdjustments._ui.FwCavOValue,
                           self._facadeAdjustments._ui.RvCavCValue,
                           self._facadeAdjustments._ui.RvCavOValue,
                           self._facadeAdjustments._ui.FwLoadCValue,
                           self._facadeAdjustments._ui.FwLoadOValue]
        for widget in listOfSpinBoxes:
            Qt.QObject.connect(widget,\
                               Qt.SIGNAL('editingFinished()'),self.applyFacade)

        self.getFacadeValues2widgets()
        self._facadeAdjustments.show()

    def getApplyButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                           button(QtGui.QDialogButtonBox.Apply)
    def applyFacade(self):
        #self.info("New parameters adjusted by hand by the user!")
        hasAnyoneChanged = False
        formulaExceptions = {}
        for field in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self.hasMandNs(field):
                m = float(self._facadeAttrWidgets[field][SLOPE_].value())
                n = float(self._facadeAttrWidgets[field][OFFSET_].value())
                if self._fromFacade[field][SLOPE_] != m or \
                   self._fromFacade[field][OFFSET_] != n:
                    self.info("Changes from the user, signal %s: "\
                              "m = %g, n = %g"%(field,m,n))
                    self._fromFacade[field][SLOPE_] = m
                    self._fromFacade[field][OFFSET_] = n
                    hasAnyoneChanged = True
                try:
                    if self._verifyFormula(field):
                        hasAnyoneChanged = True
                    self.info("%s formula ok"%(field))
                except Exception,e:
                    formulaExceptions[field] = e
                    self.warning("%s formula exception: %s"%(field,e))
            elif self.hasCandOs(field):
                c = float(self._facadeAttrWidgets[field][COUPLE_].value())
                o = float(self._facadeAttrWidgets[field][OFFSET_].value())
                if self._fromFacade[field][COUPLE_] != c or \
                   self._fromFacade[field][OFFSET_] != o:
                    self.info("Changes from the user, signal %s: "\
                              "c = %g, o = %g"%(field,c,o))
                    self._fromFacade[field][COUPLE_] = c
                    self._fromFacade[field][OFFSET_] = o
                    hasAnyoneChanged = True
                try:
                    if self._verifyFormula(field):
                        hasAnyoneChanged = True
                    self.info("%s formula ok"%(field))
                except Exception,e:
                    formulaExceptions[field] = e
                    self.warning("%s formula exception: %s"%(field,e))
                    traceback.print_exc()
        ShuntImpedance =self._facadeAdjustments._ui.ShuntImpedanceValue.text()
        if ShuntImpedance != self.getShuntImpedance():
            self.info("Changed the Shunt Impedance from %s to %s"
                      %(self.getShuntImpedance(),ShuntImpedance))
            self.setShuntImpedance(ShuntImpedance)
            hasAnyoneChanged = True
        if len(formulaExceptions.keys()) > 0:
            title = "Not all the formulas can be verified!"
            msg = "Review formula(s):\n"
            for field in formulaExceptions.keys():
                msg = "".join("%s- %s: %s\n"
                              %(msg,field,formulaExceptions[field]))
            QtGui.QMessageBox.warning(self,title,msg)
        else:
            if hasAnyoneChanged:
                self.updated.emit()
            return True
        return False

    def getOkButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                              button(QtGui.QDialogButtonBox.Ok)
    def okFacade(self):
        if self.applyFacade():
            self._facadeAdjustments.hide()
    def getCancelButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                          button(QtGui.QDialogButtonBox.Cancel)
    def cancelFacade(self):
        self.info("Canceled parameter adjusted by hand by the user!")
        if hasattr(self,'_facadeAdjustments') and \
           self._facadeAdjustments != None:
            self._facadeAdjustments.hide()
            
    def getResetButton(self):
        return self._facadeAdjustments._ui.buttonBox.\
                                           button(QtGui.QDialogButtonBox.Reset)

    def getFacadeValues2widgets(self):
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
        self._facadeAdjustments._ui.ShuntImpedanceValue.setText(\
                                                      self.getShuntImpedance())

    def hasMandNs(self,signalName):
        return SignalFields[signalName].has_key(SLOPE_) and \
                 SignalFields[signalName].has_key(OFFSET_)

    def getMandNs(self,signalName):
        if signalName in self._fromFacade.keys():
            #FIXME: these ifs needs a refactoring
            if self._fromFacade[signalName].has_key(SLOPE_) and \
               self._fromFacade[signalName].has_key(OFFSET_):
                return (self._fromFacade[signalName][SLOPE_],
                        self._fromFacade[signalName][OFFSET_])
        else:
            raise Exception("signal %s hasn't M&N's"%(signalName))

    def hasCandOs(self,signalName):
        return SignalFields[signalName].has_key(COUPLE_) and \
                 SignalFields[signalName].has_key(OFFSET_)

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
    
    def setShuntImpedance(self,strvalue):
        self._shuntImpedance = strvalue
    
    def getShuntImpedance(self):
        return self._shuntImpedance

