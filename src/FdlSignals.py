###############################################################################
## file :               FdlSignals.py
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

'''General description of the signals. This wants to be a single point 
   configuration place. This dictionary contains all the output key names, and
   their item contents are dictionaries also, with:
    - signals with I&Q keys: calculate sqrt(I^2+Q^2) where items in I&Q are 
        file fields (LoopsFiels/DiagFields)
    - signals with 'x' and m&n keys: 
        - calculate (x-n)/m
            where 'x' is another signal and m&n facades attr names this 
            calculation will be made in the gui
    - signals with 'x' and c&o keys (couple and offset): 
        - calculate x**2/10e8/10**(c)+o where 'x' is another signal and c&o 
            facades attr names this calculation will be made in the gui
    - signals with FORMULA_, and DEPEND_:
        - calculate using a formula with other fields. It also has a 
            dependency list with a list of other keys it need to correctly 
            do its own calculation.
    - signals with GUI_' key: its items describes locations (TAB_,PLOT_ and 
        'y' axis) and colour to plot this signal in the interface.
    Even this module doesn't know about the gui, this last key has been set up
    here in order to have a single point key naming to know where to modify if
    user request any change.
'''

try:#normal way
    from taurus.external.qt import Qwt5
    backward = False
except:#backward compatibility to pyqt 4.4.3
    from taurus.qt import Qwt5
    backward = True

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
               'ErroAccum_I':  24,'ErroAccum_Q':  25,#12
               'FwCav_I':      26,'FwCav_Q':      27,#13
               'TuningDephase':28,'CavityPhase':  29,#14
               'Reference_I':  30,'Reference_Q':  31}#15

#Correspondence of signals structure. 
#Section 6.1 table 6 of the documentation v2 from 20140620
#FIXME: what about this position 1!!
DiagFields = {'separator':   0,'??':          1,#0  
              'SSA1Input_I': 2,'SSA1Input_Q': 3,#1
              'SSA2Input_I': 4,'SSA2Input_Q': 5,#2
              'FwCircIn_I':  6,'FwCircIn_Q':  7,#3
              'FwCircOut_I': 8,'FwCircOut_Q': 9,#4
              'RvCircOut_I':10,'RvCircOut_Q':11,#5
              'RvLoad_I':   12,'RvLoad_Q':   13,#6
              'RvIOT1_I':   14,'RvIOT1_Q':   15,#7
              'RvIOT2_I':   16,'RvIOT2_Q':   17}#8

#As explained in section 6.2
LoopsSampleTime = 200.0 #ns, 12.5 ms * 16
DiagSampleTime = 112.5 #ns, 12.5 ms * 9
MAX_FILE_TIME = 419.4304 #ms 128MB*2**20*8/2/16*12.5/1e6

SignalFields = {}

####
#--- Dictionary keywords:
#TODO: change those constant names to upper case
#      (an perhaps in between _*_ to tag them better)
#pure file signal description fields and their amplitude components
FIELD_='field'
I_ = 'I'
Q_ = 'Q'
PHASE_ = 'Phase'
#signals with linear of quadratic fits using facade's attrs
VBLE_ = 'x'
SLOPE_ = 'm'
OFFSET_ = 'n'
COUPLE_ = 'c'
#formula evaluation signals
FORMULA_ = 'f'
DEPEND_ = 'd'
#descriptions for the graphical interface
GUI_ = 'gui'
TAB_ = 'tab'
PLOT_ = 'plot'
AXIS_ = 'axis'
COLOR_='color'
#allowed strings: 'Black','Red','Blue','Magenta','Green','Cyan','Yellow'
Y1_ = Qwt5.QwtPlot.Axis(0)
Y2_ = Qwt5.QwtPlot.Axis(1)
#--- done dictionary keywords
####

def newSignal(name,fieldName,Phase=None):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    SignalFields[name] = {}
    SignalFields[name][FIELD_] = fieldName
    if Phase:
        SignalFields[name][PHASE_] = True
        
def newPhase(name,fieldName):
    newSignal(name,fieldName,Phase=True)

def newAmplitude(name,Iname,Qname):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    SignalFields[name] = {}
    SignalFields[name][I_] = Iname
    SignalFields[name][Q_] = Qname

def fittedSignal(name,vbleName,slopeName=None,coupleName=None,offsetName=None,
                 formula=None):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    if (slopeName == None and coupleName == None) or \
       (slopeName != None and coupleName != None):
        raise Exception("fitted signal %s requires a slope or a couple! "\
                        "(exclusive or)"%(name))
    SignalFields[name] = {}
    SignalFields[name][VBLE_] = vbleName
    if slopeName != None:
        SignalFields[name][SLOPE_] = slopeName
    elif coupleName != None:
        SignalFields[name][COUPLE_] = coupleName
    SignalFields[name][OFFSET_] = offsetName
    if formula != None:
        SignalFields[name][FORMULA_] = formula

def formulaSignal(name,itsFormula,dependencies):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    SignalFields[name] = {}
    SignalFields[name][FORMULA_] = itsFormula
    SignalFields[name][DEPEND_] = dependencies

def add2gui(name,destTab,destPlot,destAxis,plotColor):
    if not SignalFields.has_key(name):
        raise Exception("key %s doesn't exist"%(name))
    if SignalFields[name].has_key(GUI_):
        raise Exception("key %s already configured for the gui"%(name))
    SignalFields[name][GUI_] = {}
    SignalFields[name][GUI_][TAB_] = destTab
    SignalFields[name][GUI_][PLOT_] = destPlot
    SignalFields[name][GUI_][AXIS_] = destAxis
    SignalFields[name][GUI_][COLOR_] = plotColor

#--- Loops signals
newSignal('CavVolt_I','Cav_I')
newSignal('CavVolt_Q','Cav_Q')
newAmplitude('CavVolt','CavVolt_I','CavVolt_Q')
newSignal('FwCav_I','FwCav_I')
newSignal('FwCav_Q','FwCav_Q')
newAmplitude('FwCav','FwCav_I','FwCav_Q')
newSignal('RvCav_I','RvCav_I')
newSignal('RvCav_Q','RvCav_Q')
newAmplitude('RvCav','RvCav_I','RvCav_Q')
newSignal('Control_I','Control_I')
newSignal('Control_Q','Control_Q')
#newAmplitude('Control','Control_I','Control_Q')
newSignal('Error_I','Error_I')
newSignal('Error_Q','Error_Q')
newAmplitude('Error','Error_I','Error_Q')
newSignal('ErroAccum_I','ErroAccum_I')
newSignal('ErroAccum_Q','ErroAccum_Q')
newAmplitude('ErroAccum','ErroAccum_I','ErroAccum_Q')
newPhase('Dephase','TuningDephase')
newPhase('CavPhase','CavityPhase')
newPhase('FwCavPhase','FwCavPhase')
newSignal('FwIOT1_I','FwIOT1_I')
newSignal('FwIOT1_Q','FwIOT1_Q')
newAmplitude('FwIOT1','FwIOT1_I','FwIOT1_Q')
newSignal('FwIOT2_I','FwIOT2_I')
newSignal('FwIOT2_Q','FwIOT2_Q',)
newAmplitude('FwIOT2','FwIOT2_I','FwIOT2_Q')
newSignal('RvCircIn_I','RvCircIn_I')
newSignal('RvCircIn_Q','RvCircIn_Q')
newAmplitude('RvCircIn','RvCircIn_I','RvCircIn_Q')
newSignal('FwLoad_I','FwLoad_I')
newSignal('FwLoad_Q','FwLoad_Q')
newAmplitude('FwLoad','FwLoad_I','FwLoad_Q')
newSignal('MO_I','MO_I')
newSignal('MO_Q','MO_Q')
newAmplitude('MO','MO_I','MO_Q')

#fittedSignal('CavVolt_mV',vbleName='CavVolt',slopeName='CAV_VOLT_m',
#                                             offsetName='CAV_VOLT_n')
fittedSignal('CavVolt_kV',vbleName='CavVolt',slopeName='CAV_VOLT_m',
                                             offsetName='CAV_VOLT_n',
             #formula='y=x*m+n'
             )
fittedSignal('FwCav_kW',vbleName='FwCav',coupleName='CAV_FW_couple',
                                         offsetName='CAV_FW_offset',
             formula='y=x**2/100*c+o')
fittedSignal('RvCav_kW',vbleName='RvCav',coupleName='CAV_RV_couple',
                                         offsetName='CAV_RV_offset',
             #formula='y=x**2/1e8/10**c+o'
             )
fittedSignal('FwLoad_kW',vbleName='FwLoad',coupleName='LOAD_FW_couple',
                                           offsetName='LOAD_FW_offset',
             #formula='y=x**2/1e8/10**c+o'
             )

#formula PDisCav_kW = (CavVolt_kV**2)/(10e6*2*3.3e8) was wrong
formulaSignal('PDisCav_kW','((CavVolt_kV*1e3)**2)/ShuntImpedance/1000',
              ['CavVolt_kV'])
formulaSignal('PBeam_kW','FwCav_kW-RvCav_kW-PDisCav_kW',
                         ['FwCav_kW','RvCav_kW','PDisCav_kW'])

#---- FIXME: many intermediate values used for debugging.
DEBUG = False
if not DEBUG:
    formulaSignal('BeamPhase',
            '180-rad2deg(arcsin(PBeam_kW*1000/BeamCurrent/CavVolt_kV))',
              ['PBeam_kW','CavVolt_kV'])
else:
    formulaSignal('PBeam_kW_1000','PBeam_kW*100',['PBeam_kW'])
    formulaSignal('PBeam_kW_1000_BeamCurrent','PBeam_kW_1000/BeamCurrent',
                  ['PBeam_kW_1000'])
    formulaSignal('PBeam_kW_1000_BeamCurrent_CavVolt_kV',
                  'PBeam_kW_1000_BeamCurrent/CavVolt_kV',
                  ['PBeam_kW_1000_BeamCurrent','CavVolt_kV'])
    formulaSignal('BeamPhase',
            '180-rad2deg(arcsin(PBeam_kW_1000_BeamCurrent_CavVolt_kV))',
                  ['PBeam_kW_1000_BeamCurrent_CavVolt_kV'])
#---- Must be cleaned before production

formulaSignal('FwCav_Phase','rad2deg(arctan(FwCav_Q,FwCav_I))',
                            ['FwCav_Q','FwCav_I'])
                            #arctan(Q/I)*180/pi+180 
                            #if I>0 else 
                            #arctan(Q/I)*180/pi
formulaSignal('FwLoad_Phase','rad2deg(arctan(FwLoad_Q,FwLoad_I))',
                             ['FwLoad_Q','FwLoad_I'])
                             #arctan(FwLoad_Q/FwLoad_I*180/pi+180 
                             #if FwLoad_I < 0 else 
                             #arctan(FwLoad_Q/FwLoad_I*180/pi
formulaSignal('MO_Phase','rad2deg(arctan(MO_Q,MO_I))',
                         ['MO_Q','MO_I'])
                         #arctan(Q/I)*180/pi+180 
                         #if I<0 else 
                         #arctan(Q/I)*180/pi

## There is a set of formula signals in the documentation that responds to:
#   if Dephase > 512:
#       Dephase-1024/512*360
#   else:
#       Dephase/512*360
#   if CavPhase > 512:
#       CavPhase-1024/512*360
#   else:
#       CavPhase/512*360
#   if FwCavPhase > 512:
#       FwCavPhase-1024/512*360
#   else:
#       FwCavPhase/512*360
## This is because the original value has "two's complement", due to that a 
#  flag has been introduced in the newSignal() definition to proceed with a 
#  correct interpretation of the value in the processSignalSet() of the
#  FdlFileParser class when reading signal sets from files.
## With this is made previously, the if is not required on the formulaSignal():
#formulaSignal('Tuning_Dephase','Dephase/512*360',['Dephase'])
#formulaSignal('Tuning_CavPhase','CavPhase/512*360',['CavPhase'])
#formulaSignal('Tuning_FwCavPhase','FwCavPhase/512*360',['FwCavPhase'])

#--- Diag signals
newSignal('SSA1Input_I','SSA1Input_I')
newSignal('SSA1Input_Q','SSA1Input_Q')
newAmplitude('SSA1Input','SSA1Input_I','SSA1Input_Q')
newSignal('SSA2Input_I','SSA2Input_I')
newSignal('SSA2Input_Q','SSA2Input_Q')
newAmplitude('SSA2Input','SSA2Input_I','SSA2Input_Q')
newSignal('FwCircIn_I','FwCircIn_I')
newSignal('FwCircIn_Q','FwCircIn_Q')
newAmplitude('FwCircIn','FwCircIn_I','FwCircIn_Q')
newSignal('FwCircOut_I','FwCircOut_I')
newSignal('FwCircOut_Q','FwCircOut_Q')
newAmplitude('FwCircOut','FwCircOut_I','FwCircOut_Q')
newSignal('RvCircOut_I','RvCircOut_I')
newSignal('RvCircOut_Q','RvCircOut_Q')
newAmplitude('RvCircOut','RvCircOut_I','RvCircOut_Q')
newSignal('RvLoad_I','RvLoad_I')
newSignal('RvLoad_Q','RvLoad_Q')
newAmplitude('RvLoad','RvLoad_I','RvLoad_Q')
newSignal('RvIOT1_I','RvIOT1_I')
newSignal('RvIOT1_Q','RvIOT1_Q')
newAmplitude('RvIOT1','RvIOT1_I','RvIOT1_Q')
newSignal('RvIOT2_I','RvIOT2_I')
newSignal('RvIOT2_Q','RvIOT2_Q')
newAmplitude('RvIOT2','RvIOT2_I','RvIOT2_Q')


#--- Plots
Loops1 = 'loops1Plots'
Loops2 = 'loops2Plots'
Diag = 'diagnosticsPlots'
allPlots = {Loops1:['topLeft',       'topRight',
                    'middleLeft',    'middleRight',
                    'bottomLeft',    'bottomRight'],
            Loops2:['topLeft',       'topRight',
                    'middleLeft',    'middleRight',
                    'bottomLeft',    'bottomRight'],
            Diag:  ['topLeft',       'topRight',
                    'middleUpLeft',  'middleUpRight',
                    'middleDownLeft','middleDownRight',
                    'bottomLeft',    'bottomRight']}

##Loops1
add2gui('CavVolt_kV',       Loops1,'topLeft',     Y1_,'Red')
add2gui('BeamPhase',        Loops1,'topLeft',     Y2_,'Cyan')
if DEBUG:
    #FIXME: to be removed
    add2gui('PBeam_kW_1000_BeamCurrent_CavVolt_kV',
            Loops1,'topLeft',Y1_,'Green')
    add2gui('PBeam_kW_1000_BeamCurrent',           Loops1,'topLeft',Y1_,'Blue')
    add2gui('PBeam_kW_1000',                     Loops1,'topLeft',Y1_,'Yellow')
add2gui('RvCav_kW',         Loops1,'topRight',    Y1_,'Green')
add2gui('PDisCav_kW',       Loops1,'topRight',    Y2_,'Red')
add2gui('PBeam_kW',         Loops1,'topRight',    Y1_,'Blue')
add2gui('Control_I',        Loops1,'middleLeft',  Y1_,'Blue')
add2gui('Control_Q',        Loops1,'middleLeft',  Y2_,'Cyan')
add2gui('Error_I',          Loops1,'middleRight', Y1_,'Green')
add2gui('Error_Q',          Loops1,'middleRight', Y1_,'Blue')
add2gui('ErroAccum_I',      Loops1,'middleRight', Y2_,'Yellow')
add2gui('ErroAccum_Q',      Loops1,'middleRight', Y2_,'Cyan')
add2gui('FwCav_kW',         Loops1,'bottomLeft',  Y1_,'Blue')
add2gui('FwCav_Phase',      Loops1,'bottomLeft',  Y2_,'Cyan')
add2gui('Dephase',          Loops1,'bottomRight', Y1_,'Red')
add2gui('CavPhase',         Loops1,'bottomRight', Y1_,'Blue')
add2gui('FwCavPhase',       Loops1,'bottomRight', Y1_,'Green')
##Loops2
add2gui('FwIOT1_I',         Loops2,'topLeft',     Y1_,'Red')
add2gui('FwIOT1_Q',         Loops2,'topLeft',     Y1_,'Blue')
add2gui('FwIOT1',           Loops2,'topLeft',     Y1_,'Black')
add2gui('FwIOT2_I',         Loops2,'topRight',    Y1_,'Red')
add2gui('FwIOT2_Q',         Loops2,'topRight',    Y1_,'Blue')
add2gui('FwIOT2',           Loops2,'topRight',    Y1_,'Black')
add2gui('RvCircIn_I',       Loops2,'middleLeft',  Y1_,'Red')
add2gui('RvCircIn_Q',       Loops2,'middleLeft',  Y1_,'Blue')
add2gui('RvCircIn',         Loops2,'middleLeft',  Y1_,'Black')
add2gui('Error',            Loops1,'middleRight', Y1_,'Red')
add2gui('ErroAccum',        Loops1,'middleRight', Y2_,'Magenta')
add2gui('FwLoad_kW',        Loops2,'middleRight', Y1_,'Blue')
add2gui('FwLoad_Phase',     Loops2,'middleRight', Y2_,'Cyan')
add2gui('RvCav',            Loops2,'bottomLeft',  Y1_,'Blue')
add2gui('MO',               Loops2,'bottomRight', Y1_,'Blue')
add2gui('MO_Phase',         Loops2,'bottomRight', Y2_,'Cyan')
## Diagnostics plots
add2gui('SSA1Input_I',      Diag,'topLeft',           Y1_,'Red')
add2gui('SSA1Input_Q',      Diag,'topLeft',           Y1_,'Blue')
add2gui('SSA1Input',        Diag,'topLeft',           Y1_,'Black')
add2gui('SSA2Input_I',      Diag,'topRight',          Y1_,'Red')
add2gui('SSA2Input_Q',      Diag,'topRight',          Y1_,'Blue')
add2gui('SSA2Input',        Diag,'topRight',          Y1_,'Black')
add2gui('FwCircIn_I',       Diag,'middleUpLeft',      Y1_,'Red')
add2gui('FwCircIn_Q',       Diag,'middleUpLeft',      Y1_,'Blue')
add2gui('FwCircIn',         Diag,'middleUpLeft',      Y1_,'Black')
add2gui('FwCircOut_I',      Diag,'middleUpRight',     Y1_,'Red')
add2gui('FwCircOut_Q',      Diag,'middleUpRight',     Y1_,'Blue')
add2gui('FwCircOut',        Diag,'middleUpRight',     Y1_,'Black')
add2gui('RvCircOut_I',      Diag,'middleDownLeft',    Y1_,'Red')
add2gui('RvCircOut_Q',      Diag,'middleDownLeft',    Y1_,'Blue')
add2gui('RvCircOut',        Diag,'middleDownLeft',    Y1_,'Black')
add2gui('RvLoad_I',         Diag,'middleDownRight',   Y1_,'Red')
add2gui('RvLoad_Q',         Diag,'middleDownRight',   Y1_,'Blue')
add2gui('RvLoad',           Diag,'middleDownRight',   Y1_,'Black')
add2gui('RvIOT1_I',         Diag,'bottomLeft',        Y1_,'Red')
add2gui('RvIOT1_Q',         Diag,'bottomLeft',        Y1_,'Blue')
add2gui('RvIOT1',           Diag,'bottomLeft',        Y1_,'Black')
add2gui('RvIOT2_I',         Diag,'bottomRight',       Y1_,'Red')
add2gui('RvIOT2_Q',         Diag,'bottomRight',       Y1_,'Blue')
add2gui('RvIOT2',           Diag,'bottomRight',       Y1_,'Black')
