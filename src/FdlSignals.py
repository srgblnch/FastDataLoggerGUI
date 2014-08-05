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
handler = 'h'
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

SignalFields = {#Loops signals
                'CavVolt_I':    {field:'Cav_I'},
                'CavVolt_Q':    {field:'Cav_Q'},
                'FwCav_I':      {field:'FwCav_I'},
                'FwCav_Q':      {field:'FwCav_Q'},
                'RvCav_I':      {field:'RvCav_I'},
                'RvCav_Q':      {field:'RvCav_Q'},
                'Control_I':    {field:'Control_I',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleLeft',
                                      axis: y1,
                                      color:'Blue'}},
                'Control_Q':    {field:'Control_Q',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleLeft',
                                      axis: y2,
                                      color:'Cyan'}},
                'Error_I':      {field:'Error_I',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleRight',
                                      axis: y1,
                                      color:'Green'}},
                'Error_Q':      {field:'Error_Q',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleRight',
                                      axis: y1,
                                      color:'Blue'}},
                'ErroAccum_I':  {field:'ErroAccum_I',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleRight',
                                      axis: y2,
                                      color:'Yellow'}},
                'ErroAccum_Q':  {field:'ErroAccum_Q',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleRight',
                                      axis: y2,
                                      color:'Cyan'}},
                #Diag signals
                'SSA1Input_I':  {field:'SSA1Input_I'},
                'SSA1Input_Q':  {field:'SSA1Input_Q'},
                #Loops Amplitudes
                'CavVolt':      {I:'CavVolt_I',  Q:'CavVolt_Q'},
                'FwCav':        {I:'FwCav_I',    Q:'FwCav_Q'},
                'RvCav':        {I:'RvCav_I',    Q:'RvCav_Q'},
                'Control':      {I:'Control_I',  Q:'Control_Q'},
                'Error':        {I:'Error_I',    Q:'Error_Q',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleRight',
                                      axis: y1,
                                      color:'Red'}},
                'ErroAccum':    {I:'ErroAccum_I',Q:'ErroAccum_Q',
                                 gui:{tab:  'Loops1',
                                      plot: 'middleRight',
                                      axis: y2,
                                      color:'Magenta'}},
                #Diag Amplitudes
                'SSA1Input':     {I:'SSA1Input_I',Q:'SSA1Input_Q'},
                #fitted signals
                'CavVolt_mV':    {vble:   'CavVolt',
                                  slope:  'CavVolt_m',
                                  offset:  'CavVolt_n'},
                'CavVolt_kV':    {vble:   'CavVolt_mV',
                                  slope:  'CAV_VOLT_KV_m',
                                  offset:'CAV_VOLT_KV_n',
                                  gui:    {tab:'Loops1',
                                           plot:'topLeft',
                                           axis:y1,
                                           color:'Red'}},
                'FwCav_kW':      {vble:   'FwCav',
                                  couple: 'FwCav_kW_couple',
                                  offset:'FwCav_kW_offset',
                                  gui:    {tab:'Loops1',
                                           plot:'bottomLeft',
                                           axis:y1,
                                           color:'Blue'}},
                'RvCav_kW':      {vble:   'RvCav',
                                  couple: 'RvCav_kW_couple',
                                  offset:'RvCav_kW_offset',
                                  gui:    {tab:'Loops1',
                                           plot:'topRight',
                                           axis:y1,
                                           color:'Green'}},
                #formula signals
                'PDisCav_kW':    {formula:'(CavVolt_kV**2)/(10e6*2*3.3e8)',
                                  handler:'loops',
                                  depend: ['CavVolt_kV'],
                                  gui:    {tab:'Loops1',
                                           plot:'topRight',
                                           axis:y2,
                                           color:'Red'}},
                'PBeam_kW':      {formula:'FwCav_kW-RvCav_kW-PDisCav_kW',
                                  handler:'loops',
                                  depend: ['FwCav_kW','RvCav_kW',
                                           'PDisCav_kW'],
                                  gui:    {tab:'Loops1',
                                           plot:'topRight',
                                           axis:y1,
                                           color:'Blue'}},
                'BeamPhase':     {formula:\
                     '180-arcsin(PBeam_kW*1000/BeamCurrent/CavVolt_kV)*180/pi',
                                  handler:'loops',
                                  depend: ['PBeam_kW','CavVolt_kV'],
                                  gui:    {tab:'Loops1',
                                           plot:'topLeft',
                                           axis:y2,
                                           color:'Cyan'}},
#                #'FwCav_Phase':   {formula:'arctan'}
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
