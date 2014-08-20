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
    - signals with 'f', 'h' and 'd':
        - calculate using a formula with other fields, and left the result 
            in 'h'. It also has a dependency list with a list of other keys 
            it need to correctly do its own calculation.
    - signals with 'gui' key: its items describes locations ('tab','plot' and 
        'y' axis) and colour to plot  this signal in the interface.
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

SignalFields = {}

####
#--- Dictionary keywords:
#pure file signal description fields and their amplitude components
field='field'
I = 'I'
Q = 'Q'
#signals with linear of quadratic fits using facade's attrs
vble = 'x'
slope = 'm'
offset = 'n'
couple = 'c'
#formula evaluation signals
formula = 'f'
depend = 'd'
#descriptions for the graphical interface
gui = 'gui'
tab = 'tab'
plot = 'plot'
axis = 'axis'
color='color'
#allowed strings: 'Black','Red','Blue','Magenta','Green','Cyan','Yellow'
y1 = Qwt5.QwtPlot.Axis(0)
y2 = Qwt5.QwtPlot.Axis(1)
#--- done dictionary keywords
####

def newSignal(name,fieldName):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    SignalFields[name] = {}
    SignalFields[name][field] = fieldName

def newAmplitude(name,Iname,Qname):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    SignalFields[name] = {}
    SignalFields[name][I] = Iname
    SignalFields[name][Q] = Qname
    
def fittedSignal(name,vbleName,slopeName=None,coupleName=None,offsetName=None):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    if (slopeName == None and coupleName == None) or \
       (slopeName != None and coupleName != None):
        raise Exception("fitted signal %s requires a slope or a couple! "\
                        "(exclusive or)"%(name))
    SignalFields[name] = {}
    SignalFields[name][vble] = vbleName
    if slopeName != None:
        SignalFields[name][slope] = slopeName
    elif coupleName != None:
        SignalFields[name][couple] = coupleName
    SignalFields[name][offset] = offsetName

def formulaSignal(name,itsFormula,dependencies):
    if SignalFields.has_key(name):
        raise Exception("key %s already exist!"%(name))
    SignalFields[name] = {}
    SignalFields[name][formula] = itsFormula
    SignalFields[name][depend] = dependencies

def add2gui(name,destTab,destPlot,destAxis,plotColor):
    if not SignalFields.has_key(name):
        raise Exception("key %s doesn't exist"%(name))
    if SignalFields[name].has_key(gui):
        raise Exception("key %s already configured for the gui"%(name))
    SignalFields[name][gui] = {}
    SignalFields[name][gui][tab] = destTab
    SignalFields[name][gui][plot] = destPlot
    SignalFields[name][gui][axis] = destAxis
    SignalFields[name][gui][color] = plotColor

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
newAmplitude('Control','Control_I','Control_Q')
newSignal('Error_I','Error_I')
newSignal('Error_Q','Error_Q')
newAmplitude('Error','Error_I','Error_Q')
newSignal('ErroAccum_I','ErroAccum_I')
newSignal('ErroAccum_Q','ErroAccum_Q')
newAmplitude('ErroAccum','ErroAccum_I','ErroAccum_Q')
newSignal('Dephase','TuningDephase')
newSignal('CavPhase','CavityPhase')
newSignal('FwCavPhase','FwCavPhase')
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

fittedSignal('CavVolt_mV',vbleName='CavVolt',slopeName='CAV_VOLT_m',
                                             offsetName='CAV_VOLT_n')
fittedSignal('CavVolt_kV',vbleName='CavVolt',slopeName='CAV_VOLT_KV_m',
                                             offsetName='CAV_VOLT_KV_n')
fittedSignal('FwCav_kW',vbleName='FwCav',coupleName='CAV_FW_couple',
                                         offsetName='CAV_FW_offset')
fittedSignal('RvCav_kW',vbleName='RvCav',coupleName='CAV_RV_couple',
                                         offsetName='CAV_RV_offset')



formulaSignal('PDisCav_kW','(CavVolt_kV**2)/(10e6*2*3.3e8)',['CavVolt_kV'])
formulaSignal('FwLoad_kW','(FwLoad**2)/(1e8*10**-3.70092)+0.1667',['FwLoad'])
formulaSignal('PBeam_kW','FwCav_kW-RvCav_kW-PDisCav_kW',
                         ['FwCav_kW','RvCav_kW','PDisCav_kW'])
formulaSignal('BeamPhase',
              '180-arcsin(PBeam_kW*1000/BeamCurrent/CavVolt_kV)*180/pi',
              ['PBeam_kW','CavVolt_kV'])
formulaSignal('FwCav_Phase','arctan(FwCav_Q/FwCav_I)*180/pi+180',
                            ['FwCav_Q','FwCav_I'])
                            #arctan(Q/I)*180/pi+180 
                            #if I>0 else 
                            #arctan(Q/I)*180/pi
                            #FIXME: there is an IF statement here
formulaSignal('Tuning_Dephase','Dephase-1024/512*360',['Dephase'])
                               #Dephase-1024/512*360 
                               #if Dephase > 512 else 
                               #Dephase/512*360
                               #FIXME: there is an IF statement here
formulaSignal('Tuning_CavPhase','CavPhase-1024/512*360',['CavPhase'])
                                #CavPhase-1024/512*360 
                                #if CavPhase > 512 else 
                                #CavPhase/512*360
                                #FIXME: there is an IF statement here
formulaSignal('Tuning_FwCavPhase','FwCavPhase-1024/512*360',['FwCavPhase'])
                                  #FwCavPhase-1024/512*360 
                                  #if FwCavPhase > 512 else 
                                  #FwCavPhase/512*360
                                  #FIXME: there is an IF statement here
formulaSignal('FwLoad_Phase','arctan(FwLoad_Q/FwLoad_I)*180/pi+180',
                             ['FwLoad_Q','FwLoad_I'])
                             #arctan(FwLoad_Q/FwLoad_I*180/pi+180 
                             #if FwLoad_I < 0 else 
                             #arctan(FwLoad_Q/FwLoad_I*180/pi
                             #FIXME: there is an IF statement here
formulaSignal('MO_Phase','arctan(MO_Q/MO_I)*180/pi+180',['MO_Q','MO_I'])
                         #arctan(Q/I)*180/pi+180 
                         #if I<0 else 
                         #arctan(Q/I)*180/pi
                         #FIXME: there is an IF statement here

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
##Loops1
add2gui('CavVolt_kV',       'Loops1','topLeft',     y1,'Red')
add2gui('BeamPhase',        'Loops1','topLeft',     y2,'Cyan')
add2gui('RvCav_kW',         'Loops1','topRight',    y1,'Green')
add2gui('PDisCav_kW',       'Loops1','topRight',    y2,'Red')
add2gui('PBeam_kW',         'Loops1','topRight',    y1,'Blue')
add2gui('Control_I',        'Loops1','middleLeft',  y1,'Blue')
add2gui('Control_Q',        'Loops1','middleLeft',  y2,'Cyan')
add2gui('Error_I',          'Loops1','middleRight', y1,'Green')
add2gui('Error_Q',          'Loops1','middleRight', y1,'Blue')
add2gui('ErroAccum_I',      'Loops1','middleRight', y2,'Yellow')
add2gui('ErroAccum_Q',      'Loops1','middleRight', y2,'Cyan')
add2gui('FwCav_kW',         'Loops1','bottomLeft',  y1,'Blue')
add2gui('FwCav_Phase',      'Loops1','bottomLeft',  y2,'Cyan')
add2gui('Tuning_Dephase',   'Loops1','bottomRight', y1,'Red')
add2gui('Tuning_CavPhase',  'Loops1','bottomRight', y1,'Blue')
add2gui('Tuning_FwCavPhase','Loops1','bottomRight', y1,'Green')
##Loops2
add2gui('FwIOT1_I',         'Loops2','topLeft',     y1,'Red')
add2gui('FwIOT1_Q',         'Loops2','topLeft',     y1,'Blue')
add2gui('FwIOT1',           'Loops2','topLeft',     y1,'Black')
add2gui('FwIOT2_I',         'Loops2','topRight',    y1,'Red')
add2gui('FwIOT2_Q',         'Loops2','topRight',    y1,'Blue')
add2gui('FwIOT2',           'Loops2','topRight',    y1,'Black')
add2gui('RvCircIn_I',       'Loops2','middleLeft',  y1,'Red')
add2gui('RvCircIn_Q',       'Loops2','middleLeft',  y1,'Blue')
add2gui('RvCircIn',         'Loops2','middleLeft',  y1,'Black')
add2gui('Error',            'Loops1','middleRight', y1,'Red')
add2gui('ErroAccum',        'Loops1','middleRight', y2,'Magenta')
add2gui('FwLoad_kW',        'Loops2','middleRight', y1,'Blue')
add2gui('FwLoad_Phase',     'Loops2','middleRight', y2,'Cyan')
add2gui('RvCav',            'Loops2','bottomLeft',  y1,'Blue')
add2gui('MO',               'Loops2','bottomRight', y1,'Blue')
add2gui('MO_Phase',         'Loops2','bottomRight', y2,'Cyan')
## Diagnostics plots
add2gui('SSA1Input_I',      'Diag','topLeft',           y1,'Red')
add2gui('SSA1Input_Q',      'Diag','topLeft',           y1,'Blue')
add2gui('SSA1Input',        'Diag','topLeft',           y1,'Black')
add2gui('SSA2Input_I',      'Diag','topRight',          y1,'Red')
add2gui('SSA2Input_Q',      'Diag','topRight',          y1,'Blue')
add2gui('SSA2Input',        'Diag','topRight',          y1,'Black')
add2gui('FwCircIn_I',       'Diag','middleUpLeft',      y1,'Red')
add2gui('FwCircIn_Q',       'Diag','middleUpLeft',      y1,'Blue')
add2gui('FwCircIn',         'Diag','middleUpLeft',      y1,'Black')
add2gui('FwCircOut_I',      'Diag','middleUpRight',     y1,'Red')
add2gui('FwCircOut_Q',      'Diag','middleUpRight',     y1,'Blue')
add2gui('FwCircOut',        'Diag','middleUpRight',     y1,'Black')
add2gui('RvCircOut_I',      'Diag','middleDownLeft',    y1,'Red')
add2gui('RvCircOut_Q',      'Diag','middleDownLeft',    y1,'Blue')
add2gui('RvCircOut',        'Diag','middleDownLeft',    y1,'Black')
add2gui('RvLoad_I',         'Diag','middleDownRight',   y1,'Red')
add2gui('RvLoad_Q',         'Diag','middleDownRight',   y1,'Blue')
add2gui('RvLoad',           'Diag','middleDownRight',   y1,'Black')
add2gui('RvIOT1_I',         'Diag','bottomLeft',        y1,'Red')
add2gui('RvIOT1_Q',         'Diag','bottomLeft',        y1,'Blue')
add2gui('RvIOT1',           'Diag','bottomLeft',        y1,'Black')
add2gui('RvIOT2_I',         'Diag','bottomRight',       y1,'Red')
add2gui('RvIOT2_Q',         'Diag','bottomRight',       y1,'Blue')
add2gui('RvIOT2',           'Diag','bottomRight',       y1,'Black')
