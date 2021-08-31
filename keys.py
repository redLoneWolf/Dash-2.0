# from Dashboard.SteeringTest import State, States, TargetCourse
from ImageFeedWidget import ImageFeedWidget
import sys
import os
from types import TracebackType
from PyQt5 import QtCore, QtGui
import qdarkstyle
import math
from SteeringTest import *
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QBoxLayout, QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem, QTabWidget, QVBoxLayout,
    QWidget,
    QMainWindow,
    QTextEdit,
    QMessageBox
)
from PyQt5.QtCore import(
    QSize,
    pyqtSignal,
    pyqtSlot
    )
# import matplotlib.pyplot as plt
from CompassWidget import CompassWidget
from AttitudeWidget import AttitudeIndicator
from CustomGraph import CustomGraph,randColor,genColorCode
from STLViewerWidget import STLViewerWidget
from CameraReceiver import CameraWidget
from MapWidget import MapWidget
from TCPProtocol import Protocol
from Tracking import ProcessImage
import pyqtgraph as pg

from PyQt5.QtCore import Qt
w = 900; h = 600

import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
from utils import NetworkAdapter, getIpv4AddressWithAdapter




            

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.keylist=[]
        self.val = {'m1':0,'m2':0,'m3':0,'m4':0}
        self.protocol = None
        self.yMax= 0
        self.yMin= 0
        self.xMax= 0
        self.xMin =0
        self.calibrate = True
        self.count = 0
        self.mx=[]
        self.my=[]
        self.mz =[]
        self.sensor_x=0
        self.offset_x=0
        self.offset_y=0
        self.offset_z=0
        self.sensor_z=0
        self.sensor_y = 0
 
        self.CurrFrameData =None

        self.RC_ENABLED = True
        self.USB_CONNECTED = False
        self.TELEMETRY_STARTED= False
        self.DEPTH_FEED_STARTED = False
        self.CAM_FEED_STARTED= False
        self.WAYPOINT_STARTED = False
        self.initUi()
    
    def initUi(self):
     
      
        self.initRCControls()
        
       
        

        self.grid = QGridLayout()
   
        

       
        # self.grid.addLayout(self.keys,2,0,Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)
  

        # self.setLayout(self.grid)


    def initRCControls(self):
        self.W = QPushButton("W")
        self.W.setMinimumSize(40,40)
        self.W.setMaximumSize(40,40)
        self.W.pressed.connect(self.OnPressW)
        self.W.released.connect(self.OnReleaseW)

        self.A = QPushButton("A")
        self.A.setMinimumSize(40,40)
        self.A.setMaximumSize(40,40)
        self.A.pressed.connect(self.OnPressA)
        self.A.released.connect(self.OnReleaseA)

        self.S = QPushButton("S")
        self.S.setMinimumSize(40,40)
        self.S.setMaximumSize(40,40)
        self.S.pressed.connect(self.OnPressS)
        self.S.released.connect(self.OnReleaseS)

        self.D = QPushButton("D")
        self.D.setMinimumSize(40,40)
        self.D.setMaximumSize(40,40)
        self.D.pressed.connect(self.OnPressD)
        self.D.released.connect(self.OnReleaseD)
        # self.hideRCControls()
        
        self.keys = QGridLayout()
        self.keys.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.keys.addWidget(self.W,0,1)
        self.keys.addWidget(self.A,1,0)
        self.keys.addWidget(self.D,1,2)
        self.keys.addWidget(self.S,1,1)
        c = QWidget(self)
        c.setLayout(self.keys)
        self.setCentralWidget(c)
        # self.showRCControls()

    def hideRCControls(self):
        self.W.hide() 
        self.A.hide()
        self.S.hide()
        self.D.hide()
    
    def showRCControls(self):
        self.W.show() 
        self.A.show()
        self.S.show()
        self.D.show()






        

 

    def OnPressW(self):
        for motor in self.val.keys():
            self.val[motor] = self.val[motor]+1
        

    def OnReleaseW(self):
        for motor in self.val.keys():
            self.val[motor] = 0

    #   25

    
    def OnPressA(self):

        self.val['m1']+=1  # fixed
        self.val['m3']-=1

        self.val['m2']+=1 # fixed
        self.val['m4']-=1
       


    def OnReleaseA(self):
       
        self.val['m2'] =0
        self.val['m4'] =0

        self.val['m1'] =0
        self.val['m3'] =0

       
    def OnPressS(self):
        for motor in self.val.keys():
            self.val[motor]-=1
          

    def OnReleaseS(self):
        for motor in self.val.keys():
            self.val[motor] = 0
        print(self.val)

    def OnPressD(self):

        self.val['m2']-=1
        self.val['m4']+=1

        self.val['m1']-=1
        self.val['m3']+=1


    def OnReleaseD(self):
        

        self.val['m1'] =0
        self.val['m3'] =0

        self.val['m2'] =0
        self.val['m4'] =0
      

    def keyPressEvent(self, event):
        if(self.RC_ENABLED):
            print("cont",event.count())
            # if event.isAutoRepeat():
                # return
            if Qt.Key.Key_W == event.key():
                self.W.setDown(True)
                self.OnPressW()
            
            if Qt.Key.Key_S == event.key():
                self.S.setDown(True)
                self.OnPressS()

            if Qt.Key.Key_A == event.key():
                self.A.setDown(True)
                self.OnPressA()
            
            if Qt.Key.Key_D == event.key():
                self.D.setDown(True)
                self.OnPressD()

            self.sendRC()

    def keyReleaseEvent(self, event):
        if(self.RC_ENABLED):
            if event.isAutoRepeat():
                return
            if Qt.Key.Key_W == event.key():
                self.W.setDown(False)
                self.OnReleaseW()

            if Qt.Key.Key_S == event.key():
                self.S.setDown(False)
                self.OnReleaseS()
            
            if Qt.Key.Key_A == event.key():
                self.A.setDown(False)
                self.OnReleaseA()
            
            if Qt.Key.Key_D == event.key():
                self.D.setDown(False)
                self.OnReleaseD()
                
            self.sendRC()




    def sendRC(self):
        arr = []
        for motor in self.val.keys():
            WithinRange = max(min(100, self.val[motor]), -100)
            arr.append(WithinRange)
        print(arr)
        # self.protocol.sendRCData(arr)




          
            

    



if __name__ == "__main__":
    # create logger
    app = QApplication(sys.argv)


    # app.setStyleSheet(qdarkstyle.load_stylesheet())
    window = Window()
    window.show()
    sys.exit(app.exec_())