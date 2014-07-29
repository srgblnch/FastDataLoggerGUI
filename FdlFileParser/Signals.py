###############################################################################
## file :               Signals.py
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

####
#--- Dictionary keywords:
#pure file signal description fields
I = 'I'
Q = 'Q'
#signals with linear of quadratic fits using facade's attrs
vble = 'x'
slope = 'm'
loffset = 'n'
couple = 'c'
qoffset = 'o'
#formula evaluation signals
formula = 'f'
handler = 'h'
depend = 'd'
#descriptions for the graphical interface
gui = 'gui'
tab = 'tab'
plot = 'plot'
axis = 'axis'
color='color'
y1 = Qwt5.QwtPlot.Axis(0)
y2 = Qwt5.QwtPlot.Axis(1)
#--- done dictionary keywords
####

SignalFields = {'CavVolt_mV':    {I:'Cav_I',  Q:'Cav_Q'  },
                'FwCav_mV':      {I:'FwCav_I',Q:'FwCav_Q'},
                'RvCav_mV':      {I:'RvCav_I',Q:'RvCav_Q'},
                'CavVolt_kV':    {vble:   'CavVolt_mV',
                                  slope:  'CAV_VOLT_KV_m',
                                  loffset:'CAV_VOLT_KV_n',
                                  gui:    {tab:'Loops1',
                                           plot:'topLeft',
                                           axis:y1,
                                           color:'Red'}},
                'PDisCav_kW':    {vble:   'CavVolt_mV',
                                  couple: 'PDisCav_c',
                                  qoffset:'PDisCav_o',},
                'FwCav_kW':      {vble:   'FwCav_mV',
                                  couple: 'FwCav_kW_c',
                                  qoffset:'FwCav_kW_o'},
                'RvCav_kW':      {vble:   'RvCav_mV',
                                  couple: 'RvCav_kW_c',
                                  qoffset:'RvCav_kW_o',},
                'PBeam_kW':      {formula:'FwCav_kW-RvCav_kW-PDisCav_kW',
                                  handler:'loops',
                                  depend: ['FwCav_kW','RvCav_kW',
                                           'PDisCav_kW']},
                'BeamPhase':     {formula:\
                     '180-arcsin(PBeam_kW*1000/BeamCurrent/CavVolt_kV)*180/pi',
                                  handler:'loops',
                                  depend: ['PBeam_kW','CavVolt_kV'],
                                  gui:    {tab:'Loops1',
                                           plot:'topLeft',
                                           axis:y2,
                                           color:'Cyan'}}
               }

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

#Correspondence of signals structure. 
#Section 6.1 table 6 of the documentation v2 from 20140620
#FIXME: what about this position 1!!
DiagFields = { 0:'separator',   1:'??',         #0  
               2:'SSA1Input_I', 3:'SSA1Input_Q',#1
               4:'SSA2Input_I', 5:'SSA2Input_Q',#2
               6:'FwCircIn_I',  7:'FwCircIn_Q', #3
               8:'FwCircOut_I', 9:'FwCircOut_Q',#4
              10:'RvCircOut_I',11:'RvCircOut_Q',#5
              12:'RvLoad_I',   13:'RvLoad_Q',   #6
              14:'RvIOT1_I',   15:'RvIOT1_Q',   #7
              16:'RvIOT2_I',   17:'RvIOT2_Q'    #8
             }