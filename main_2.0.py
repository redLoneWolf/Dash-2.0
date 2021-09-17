# from Dashboard.SteeringTest import State, States, TargetCourse
from TCPServer import ClientTypes
from ImageFeedWidget import ImageFeedWidget
import sys
import os
from types import TracebackType
from PyQt5 import QtCore, QtGui
import qdarkstyle
import math

import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QBoxLayout, QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem, QTabWidget, QVBoxLayout,
    QWidget,
    QMainWindow,
    QTextEdit,
    QMessageBox
)
from PyQt5.QtCore import(
    QSize,
    QTime,
    QTimer,
    pyqtSignal,
    pyqtSlot
    )
# import matplotlib.pyplot as plt
from CompassWidget import CompassWidget
from AttitudeWidget import AttitudeIndicator
from CustomGraph import CustomGraph,randColor,genColorCode
from STLViewerWidget import STLViewerWidget
from CameraReceiver import CameraWidget

from TCPProtocol import Protocol

import pyqtgraph as pg

from PyQt5.QtCore import Qt
w = 900; h = 600

import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
from utils import NetworkAdapter, getIpv4AddressWithAdapter


log = logging.getLogger('hello')
log.setLevel(logging.INFO)
format = logging.Formatter(fmt="%(asctime)s %(levelname)s %(funcName)s %(message)s",datefmt="%Y-%m-%d %H:%M:%S")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(format)
log.addHandler(ch)

fh = handlers.RotatingFileHandler("dashboard.log", maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(format)
log.addHandler(fh)

import configparser

# 25
RC_INC = 8

def get_key(dictionary,val):
    for key, value in dictionary.items():
         if val == value:
             return key


class ConfigTab(QWidget):
    onUsingNgrok = pyqtSignal(str)
    onUsingLocal = pyqtSignal(str,str,int)

    def __init__(self,newtworkAdapters):
        super().__init__()
        self.newtworkAdapters:list[NetworkAdapter] = newtworkAdapters
        
        self.vBox = QVBoxLayout(self)
        self.selectedHost = None

        self.gb = QGroupBox("Use Local")
        self.gb.setCheckable(True)
        self.gb.setChecked(True)
        self.gb.toggled.connect(self.onUseLocalGB)
        
        self.localLayout = QFormLayout()
        # Add widgets to the layout
        self.networkSelectCB = QComboBox()
        # self.networkSelectCB.addItem()
        for adapter in self.newtworkAdapters:
            self.networkSelectCB.addItem(str(adapter),userData=adapter.getIp())
        
        self.networkSelectCB.currentIndexChanged.connect(self.onSelectionChange)
        self.portLineEdit = QLineEdit()
        self.portLineEdit.setMaxLength(5)
        self.portLineEdit.textChanged.connect(self.onPortChange)
        self.portLineEdit.setPlaceholderText("Default:8888 Maximum:65535")
        self.portLineEdit.setValidator(QtGui.QIntValidator(0,65535))
        
        
        self.portlabel = QLabel("Port :") 
        
        self.localLayout.addRow("Network :",self.networkSelectCB )
        self.localLayout.addRow(self.portlabel,self.portLineEdit )
        self.saveLocalInfoChkBx = QCheckBox("Save")
        
        self.localLayout.addRow(self.saveLocalInfoChkBx)

        self.gb.setLayout(self.localLayout)

        self.gb.setFixedSize(QSize(530,100))

        self.gb2 = QGroupBox("Use Ngrok")
        self.gb2.setCheckable(True)
        self.gb2.setChecked(False)
        self.gb2.toggled.connect(self.onUseNgrokGB)
     
        self.vBox.addStretch(1)
        self.vBox.addWidget(self.gb,)
       
        self.ngrokLayout = QFormLayout()
        self.authtokenEdit = QLineEdit()
        self.authtokenEdit.textChanged.connect(self.onAuthLEChanged)
        self.authtokenEdit.setPlaceholderText("get Auth token From ngrok")
        self.ngrokLayout.addRow("Ngrok AuthToken",self.authtokenEdit)
        self.saveNgrokAuthChkBx = QCheckBox("Save")
        
        self.ngrokLayout.addRow(self.saveNgrokAuthChkBx)

        self.gb2.setLayout(self.ngrokLayout)
        self.gb2.setFixedSize(QSize(530,90))
        self.vBox.addWidget(self.gb2,)
        self.gotoDashBoardBtn = QPushButton("Go to Dashboard")
        self.gotoDashBoardBtn.clicked.connect(self.onDashboardBtn)
        self.vBox.addWidget(self.gotoDashBoardBtn,alignment=Qt.AlignmentFlag.AlignRight)
            
        self.vBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vBox.addStretch(1)
      
        self.setLayout(self.vBox)
        self.applyConfig()

    def applyConfig(self):
        self.config = configparser.ConfigParser()
        self.config.read("dashboard.ini")
       

        if self.config.has_option("LOCAL","adapter"):
            # print("adapter")
            adapter = self.config.get("LOCAL","adapter")
            self.networkSelectCB.setCurrentIndex(self.getNetworkAdapterIndex(adapter))
            

        if self.config.has_option("LOCAL","port"):
            # print("port")
            port = self.config.get("LOCAL","port")
            self.portLineEdit.setText(port)
        
        if self.config.has_option("NGROK","auth"):
            # print("auth")
            auth =  self.config.get("NGROK","auth")
            self.authtokenEdit.setText(auth)
        
        

    def onDashboardBtn(self):
        if self.gb.isChecked():
            idx = self.networkSelectCB.currentIndex()
            adapter = self.newtworkAdapters[idx].getAdapterName()
            ip = self.newtworkAdapters[idx].getIp()
            port = int(self.portLineEdit.text()) if len(self.portLineEdit.text()) > 0 else 8888
            if self.saveLocalInfoChkBx.isChecked():
                self.saveLocalConfig(adapter,port)
            
            self.onUsingLocal.emit(adapter,ip,port)

        elif self.gb2.isChecked():
            auth =  self.authtokenEdit.text()
            if self.saveNgrokAuthChkBx.isChecked():
                self.saveNgrokConfig(auth)
            
            self.onUsingNgrok.emit(auth)
            
    
    def onPortChange(self,port):
        if len(port)>0:
            if int(port) > 65535:
                print("greater than range")
                self.portlabel.setText("Port :<font color='red'>max:65535</font>")
                self.gotoDashBoardBtn.setEnabled(False)

            else: 
                self.portlabel.setText("Port :")
                self.gotoDashBoardBtn.setEnabled(True)
    
    def saveNgrokConfig(self,auth):
        if not self.config.has_section('NGROK'):
            self.config.add_section('NGROK')

        self.config.set('NGROK','auth', auth)
        with open('dashboard.ini', 'w') as configfile:
           self.config.write(configfile)
    
    def saveLocalConfig(self,adapter,port):
        if not self.config.has_section('LOCAL'):
            self.config.add_section('LOCAL')

        self.config.set('LOCAL','adapter', adapter)
        self.config.set('LOCAL','port', str(port))
        with open('dashboard.ini', 'w') as configfile:
           self.config.write(configfile)


    def onSelectionChange(self,i):
        self.selectedHost = self.networkSelectCB.itemData(i)
  
        
    
    def onAuthLEChanged(self,token):
        if len(token)>0:
            self.gotoDashBoardBtn.setEnabled(True)
        else:
            self.gotoDashBoardBtn.setEnabled(False)


    def onUseLocalGB(self,toggle):
        if toggle:
            # print("Toggled Local")
            self.gb2.setChecked(False)
        else:
            # print("UNToggled Local")
            self.gb2.setChecked(True)
            
    def onUseNgrokGB(self,toggle):
        if toggle:
            # print("Toggled Ngrok")
            self.gb.setChecked(False)
            if len(self.authtokenEdit.text())==0:
                self.gotoDashBoardBtn.setEnabled(False)
        else:
            # print("UNToggled Ngrok")
            self.gb.setChecked(True)

    def getNetworkAdapterIndex(self,val):
        i = 0
        for adapter in self.newtworkAdapters:
            if adapter.getAdapterName()==val:
                return i
            i = i + 1
            

class Dashboard(QWidget):
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

        self.RC_ENABLED = False
        self.USB_CONNECTED = False
        self.TELEMETRY_STARTED= False
        self.DEPTH_FEED_STARTED = False
        self.CAM_FEED_STARTED= False
        self.WAYPOINT_STARTED = False
        self.initUi()
        self.battery = 0
    
    def initUi(self):
        self.initLeftSidebar()
        self.initCenterArea()
        self.initRightSidebar()
        self.initRCControls()
        
       
        
   
        
        self.grid = QGridLayout()
        self.side = QWidget()
        

        self.side.setLayout(self.sideBar)
        self.side.setMinimumWidth(200)
        self.side.setMinimumHeight(300)
   
        self.grid.addWidget(self.side,0,0)
        self.grid.addWidget(self.cam,0,1,alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)
        self.grid.addWidget(self.depthCam,0,2,alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)

        self.grid.addLayout(self.graphVLayout,2,3,Qt.AlignmentFlag.AlignBottom)
        self.grid.addLayout(self.rigthSidebar,0,3,alignment=Qt.AlignmentFlag.AlignRight)
        self.grid.addLayout(self.keys,2,0,Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)
  
        # self.mainWidget.setLayout(self.grid)
        self.setLayout(self.grid)

        self.disableLeftSideBar(True)

    def initCenterArea(self):
        labels = {'ax':randColor(), 'ay':randColor(), 'az':randColor(), 'gx':randColor(), 'gy':randColor(), 'gz':randColor(), 'x':randColor(), 'y':randColor(), 'z':randColor(),'mx':randColor(), 'my':randColor(), 'mz':randColor()}
        mag = {'mx':genColorCode(255,0,0), 'my':genColorCode(0,255,0), 'mz':genColorCode(0,0,255)}

        
        self.AccGraph= CustomGraph(curveNames=mag,name="Accelerometer in m/s2")
        self.GyroGraph= CustomGraph(curveNames=mag,row=1,col=0,name="Gyroscope in deg/s")
        
        self.MagGraph= CustomGraph(curveNames=mag,row=3,col=0,name="Mag in deg/s")

        self.graphVLayout =  QVBoxLayout()
        self.MagGraph.setMaximumHeight(200)
        self.AccGraph.setMaximumHeight(200)
        self.GyroGraph.setMaximumHeight(200)
        self.graphVLayout.addWidget(self.AccGraph)
        self.graphVLayout.addWidget(self.GyroGraph)
        self.graphVLayout.addWidget(self.MagGraph)
        
                
        
        # self.graphVLayout.addStretch(1)

        self.camLayout = QHBoxLayout() 
        self.cam = ImageFeedWidget(name="RGB Cam",parent=self)
        
      
        self.cam.setMaximumHeight(480)
        self.cam.setMaximumWidth(640)
   
        self.cam.setMinimumHeight(480)
        self.cam.setMinimumWidth(640)
        
        self.depthCam = ImageFeedWidget(name = "Depth Cam",parent=self)
        
        self.depthCam.setMaximumHeight(240)
        self.depthCam.setMaximumWidth(320)
        self.depthCam.setMinimumHeight(240)
        self.depthCam.setMinimumWidth(320)
        
        # self.depthCam.show()

      





    def initRightSidebar(self):
        self.topHbox = QHBoxLayout()
    
        self.connectBtn = QPushButton("Start Server")
        self.connectBtn.clicked.connect(self.onStartStopBtn)
        self.ipEditText = QTextEdit(self)
        self.ipEditText.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ipEditText.setReadOnly(True)
        self.ipEditText.setMaximumHeight(25)
        self.ipEditText.setMaximumWidth(100)
        self.ipEditText.setText("IP Address")
        self.ipEditText.verticalScrollBar().setDisabled(True)

        self.portEditText = QTextEdit(self)
        self.portEditText.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.portEditText.setReadOnly(True)
        self.portEditText.setMaximumHeight(25)
        self.portEditText.setMaximumWidth(90)
        self.portEditText.setText("Port")
        self.portEditText.verticalScrollBar().setDisabled(True)

        self.topHbox.setAlignment(Qt.AlignTop | Qt.AlignRight)
    
        self.topHbox.addWidget(self.ipEditText,alignment=Qt.AlignRight)
        self.topHbox.addWidget(self.portEditText,alignment=Qt.AlignRight)
        self.topHbox.addWidget(self.connectBtn,alignment=Qt.AlignRight)
        
        self.stlViewer = STLViewerWidget()
        self.stlViewer.setMinimumSize(240//2, 240//2)
        self.stlViewer.setMaximumSize(240//2, 240//2)

        self.compass = CompassWidget()
        self.compass.setMinimumSize(320//2, 240//2)
        self.compass.setMaximumSize(320//2, 240//2)

        self.attitudeIndicator = AttitudeIndicator()
        self.attitudeIndicator.setMinimumSize(240//2, 240//2)
        self.attitudeIndicator.setMaximumSize(240//2, 240//2)



        self.rigthSidebar = QVBoxLayout()
        self.rigthSidebar.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.rigthSidebar.addLayout(self.topHbox)
        # self.rigthSidebar.addSpacing(20)
        self.rigthSidebar.addWidget(self.compass ,alignment=Qt.AlignHCenter)
        # self.rigthSidebar.addSpacing(25)
        self.rigthSidebar.addWidget(self.attitudeIndicator,alignment=Qt.AlignHCenter)
        # self.rigthSidebar.addSpacing(25)
        self.rigthSidebar.addWidget(self.stlViewer,alignment=Qt.AlignHCenter )

        self.rigthSidebar.addStretch(1)

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
        self.hideRCControls()
        
        self.keys = QGridLayout()
        self.keys.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.keys.addWidget(self.W,0,1)
        self.keys.addWidget(self.A,1,0)
        self.keys.addWidget(self.D,1,2)
        self.keys.addWidget(self.S,1,1)

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


    def initLeftSidebar(self):
        self.stats = QVBoxLayout()
        self.batteryTE = QTextEdit(self)
    
        self.batteryTE.setReadOnly(True)
        self.batteryTE.setText("Battery 0%")
        self.batteryTE.setMaximumSize(80,20)
        self.batteryTE.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.batteryTE.verticalScrollBar().setDisabled(True)
        cleintLabel = QLabel("Connected Clients")
        self.clientsListView = QListWidget()

        self.clientListWidgets = {ClientTypes.MAIN:QListWidgetItem("MAIN"),
                                    ClientTypes.CAM:QListWidgetItem("CAM"),
                                    ClientTypes.DEPTH_CAM:QListWidgetItem("DEPTH_CAM")
                                    } 

        self.clientsListView.setMaximumHeight(100)
        
        self.stats.addWidget(cleintLabel, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.stats.addWidget(self.clientsListView, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.stats.addWidget(self.batteryTE, alignment=Qt.AlignmentFlag.AlignHCenter)

       
        

        # self.stats.addWidget(self.wifiSignal)

        self.sideBar = QVBoxLayout(self)     
        self.sideBar.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sideBar.addLayout(self.stats)
        self.connectUSBBtn = QPushButton("Connect USB")
        self.connectUSBBtn.clicked.connect(self.onUSBBtn)
        self.sideBar.addWidget(self.connectUSBBtn)
        self.telemetryBtn = QPushButton("Start Telemetry")
        self.telemetryBtn.clicked.connect(self.onTelemetryBtn)
        self.sideBar.addWidget(self.telemetryBtn)

        self.cameraFeedBtn = QPushButton("Start Camera Feed")
        self.cameraFeedBtn.clicked.connect(self.onCameraFeedBtn)
        self.sideBar.addWidget(self.cameraFeedBtn)
        self.depthFeedBtn = QPushButton("Start Depth Feed")
        self.depthFeedBtn.clicked.connect(self.onDepthFeedBtn)
        self.sideBar.addWidget(self.depthFeedBtn)
        # print(self.palette().color(QtGui.QPalette.Base).name())
        self.rcBtn = QPushButton("Start RC")
        self.rcBtn.clicked.connect(self.onRCBtn)
        self.sideBar.addWidget(self.rcBtn)

        self.sideBar.addStretch(1)



        
    def disableLeftSideBar(self,disable:bool):
        self.connectUSBBtn.setDisabled(disable)

        self.telemetryBtn.setDisabled(disable)


        self.cameraFeedBtn.setDisabled(disable)

        self.depthFeedBtn.setDisabled(disable)

        self.rcBtn.setDisabled(disable)
 

    def OnPressW(self):
        for motor in self.val.keys():
            self.val[motor] = self.val[motor]+RC_INC
            # if self.val[motor] > 255:
            #     self.val[motor] = 255

            # if self.val[motor] < -255:
            #     self.val[motor] = -255

        # print(self.val)

    def OnReleaseW(self):
        for motor in self.val.keys():
            self.val[motor] = 0

        # print(self.val)

    
    def OnPressA(self):

        self.val['m1']+=RC_INC  # fixed
        self.val['m3']-=RC_INC

        self.val['m2']+=RC_INC # fixed
        self.val['m4']-=RC_INC
        

        # self.val['m1']+=10

        # self.val['m2']+=10


        # print(self.val)



    def OnReleaseA(self):
        # self.val['m2'] = self.val.get('m1')
        # self.val['m4'] = self.val.get('m1')
        self.val['m2'] =0
        self.val['m4'] =0

        self.val['m1'] =0
        self.val['m3'] =0

        # self.val['m3']+=10

        # self.val['m4']+=10

        # print(self.val)

    def OnPressS(self):
        for motor in self.val.keys():
            self.val[motor]-=RC_INC
            # if self.val[motor] > 255:
            #     self.val[motor] = 255

            # if self.val[motor] < -255:
            #     self.val[motor] = -255

        # print(self.val)

    def OnReleaseS(self):
        for motor in self.val.keys():
            self.val[motor] = 0
        print(self.val)

    def OnPressD(self):

        self.val['m2']-=RC_INC
        self.val['m4']+=RC_INC

        self.val['m1']-=RC_INC
        self.val['m3']+=RC_INC

        # self.val['m2']=-128
        # self.val['m4']=128

        # self.val['m1']=-128
        # self.val['m3']=128

        # print(self.val)

    def OnReleaseD(self):
        # self.val['m1'] = self.val.get('m2')
        # self.val['m3'] = self.val.get('m2')

        self.val['m1'] =0
        self.val['m3'] =0

        self.val['m2'] =0
        self.val['m4'] =0
        # print(self.val)

    def keyPressEvent(self, event:QtGui.QKeyEvent):
        if(self.RC_ENABLED):
           
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

    def onUSBBtn(self):
        if self.protocol.isListening() and not self.USB_CONNECTED:
            self.protocol.connectUSB()
            self.USB_CONNECTED = True
            self.connectUSBBtn.setText("Disconnect USB")
            log.info("USB Connected")

        elif self.protocol.isListening() and self.USB_CONNECTED:
            self.protocol.disconnectUSB()
            self.USB_CONNECTED = False
            self.connectUSBBtn.setText("Connect USB")
            log.info("USB disonnected")


    def onTelemetryBtn(self):
    
        if self.protocol.isListening() and not self.TELEMETRY_STARTED:
            self.protocol.startTelemetry()
            log.info("Telemetry Started")
            self.telemetryBtn.setText("Stop Telemetry")
            self.onTelemtryStart()

        elif self.protocol.isListening() and self.TELEMETRY_STARTED:
            self.protocol.stopTelemetry()
            self.telemetryBtn.setText("Start Telemetry")
            log.info("Telemetry Stopped")
            self.onTelemtryStop()

    
    def onTelemtryStart(self):
        self.TELEMETRY_STARTED = True
        self.attitudeIndicator.start()
        self.AccGraph.start()
        self.GyroGraph.start()
        self.MagGraph.start()
        self.stlViewer.start()

    
    def onTelemtryStop(self):
        self.TELEMETRY_STARTED = False
        self.attitudeIndicator.stop()
        self.AccGraph.stop()
        self.GyroGraph.stop()
        self.MagGraph.stop()
        self.stlViewer.stop()


    def onCameraFeedBtn(self):
        if not self.protocol.isCamConnected() and self.protocol.isListening() and not self.CAM_FEED_STARTED:
            self.protocol.changeCam.connect(self.cam.setImage)
            self.protocol.startCamFeed()
            self.cameraFeedBtn.setText("Stop Cam Feed")
            self.CAM_FEED_STARTED = True
            
        elif self.protocol.isCamConnected() and self.protocol.isListening() and self.CAM_FEED_STARTED:
            self.protocol.changeCam.disconnect(self.cam.setImage)
            self.protocol.stopCamFeed()
            log.info("CamFeed Stopped")
            self.cameraFeedBtn.setText("Start Cam Feed")
            self.CAM_FEED_STARTED = False
            
    def onDepthFeedBtn(self):
        if not self.protocol.isDepthConnected() and self.protocol.isListening() and not self.DEPTH_FEED_STARTED:
            self.protocol.changeDepth.connect(self.depthCam.setImage)
            self.protocol.startDepthFeed()
            self.depthFeedBtn.setText("Stop Depth Feed")
            self.DEPTH_FEED_STARTED = True

        elif self.protocol.isDepthConnected() and self.protocol.isListening() and self.DEPTH_FEED_STARTED:
            self.protocol.changeDepth.disconnect(self.depthCam.setImage)
            self.protocol.stopDepthFeed()
            log.info("DepthFeed Stopped")
            self.depthFeedBtn.setText("Start Depth Feed")
            self.DEPTH_FEED_STARTED = False
        
    def sendRC(self):
        arr = []
        for motor in self.val.keys():
            WithinRange = max(min(100, self.val[motor]), -100)
            arr.append(WithinRange)
        print(arr)
        self.protocol.sendRCData(arr)

    def onRCBtn(self):
        
        if not self.RC_ENABLED:
            self.showRCControls()
            self.RC_ENABLED = True 
            log.info("RC Enabled")

        else: 
            self.hideRCControls()
            self.RC_ENABLED = False
            log.info("RC Disabled")
            
    def updateStlRotation(self,x,y,z):
        self.stlViewer.setValues(x,y,z)
    
    def updateAttitude(self,roll,pitch):
        self.attitudeIndicator.setRollPitch(roll,pitch)

    def updateCompass(self,deg):
        self.compass.setAngle(deg)

    def initServerWithLocal(self,ip,port):
        self.protocol = Protocol(self.onPacketReceive,parent=self)
        self.protocol.onStart.connect(self.onServerStart)
        self.protocol.initLocal(ip,port)
            
    def initServerWithNgrok(self,auth):
        self.protocol = Protocol(self.onPacketReceive,parent=self)
        self.protocol.onStart.connect(self.onServerStart)
        self.protocol.initNgrok(auth)
        
    def onServerStart(self,ip,port):
        self.ipEditText.setText(ip)
        self.portEditText.setText(str(port))

    def onStartStopBtn(self):
        if(not self.protocol.isListening()):
            self.startServer()
            self.connectBtn.setText("Stop Server")
            
        else:
            self.stopServer()
            self.ipEditText.setText("IP Address")
            self.portEditText.setText("Port")
            self.connectBtn.setText("Start Server")
            
    def startServer(self):
        self.protocol.sessionOpened()
        self.protocol.setTelemetryCallBack(self.onTelemetryData)
        self.protocol.onClientDisconnect.connect(self.handleDisconnect)
        self.protocol.onClientConnect.connect(self.handleConnect)

    @pyqtSlot(ClientTypes)
    def handleConnect(self,clientType:ClientTypes):
        self.USB_CONNECTED = False
        if clientType == ClientTypes.MAIN:
            
            self.disableLeftSideBar(False)
            self.connectUSBBtn.setText("Connect USB")
            self.clientsListView.addItem(self.clientListWidgets.get(clientType))
        elif clientType == ClientTypes.CAM:
            self.cameraFeedBtn.setText("Stop Cam Feed")
            self.CAM_FEED_STARTED = True
            self.clientsListView.addItem(self.clientListWidgets.get(clientType))
        elif clientType == ClientTypes.DEPTH_CAM:
            self.depthFeedBtn.setText("Stop Depth Feed")
            self.DEPTH_FEED_STARTED = True
            self.clientsListView.addItem(self.clientListWidgets.get(clientType))

    @pyqtSlot(ClientTypes)
    def handleDisconnect(self,clientType:ClientTypes):
        
        if clientType == ClientTypes.MAIN:
            self.USB_CONNECTED = False
            self.connectUSBBtn.setText("Connect USB")
            self.disableLeftSideBar(True)
            self.onTelemtryStop()
            self.TELEMETRY_STARTED=False
            self.clientsListView.takeItem(self.clientsListView.row(self.clientListWidgets.get(ClientTypes.MAIN)))
            self.clientsListView.takeItem(self.clientsListView.row(self.clientListWidgets.get(ClientTypes.CAM)))
            self.clientsListView.takeItem(self.clientsListView.row(self.clientListWidgets.get(ClientTypes.DEPTH_CAM)))
        elif clientType == ClientTypes.CAM:
            self.cameraFeedBtn.setText("Start Cam Feed")
            self.CAM_FEED_STARTED = False
            self.clientsListView.takeItem(self.clientsListView.row(self.clientListWidgets.get(clientType)))
        elif clientType == ClientTypes.DEPTH_CAM:
            self.depthFeedBtn.setText("Start Depth Feed")
            self.DEPTH_FEED_STARTED = False
            self.clientsListView.takeItem(self.clientsListView.row(self.clientListWidgets.get(clientType)))
       
     

    
    def onPacketReceive(command,data):
        # print(command,data)
        pass


    def stopServer2(self):
        
        if self.protocol.isListening():
            self.protocol.disconnect()
            self.protocol.stop()

        
  
    def stopServer(self):
        if self.protocol and self.protocol.checkClientConnection(ClientTypes.MAIN):
            self.protocol.sendDisconnect()
            QTimer.singleShot(500, self.stopServer2)
            
        
        
    def updateDeviceStats(self,stats):
        charge = stats[0]
        self.batteryTE.setText("Battery {bat}%".format(bat=charge))

        # wifiStrength = stats[1]
        # wifiStatus = ""
        # if wifiStrength >-50:
        #     wifiStatus = "Excellent"
        
        # if wifiStrength >=-60 and wifiStrength <-50:
        #     wifiStatus = "Good"

        # if wifiStrength >=-70 and wifiStrength <-60:
        #     wifiStatus = "Fair"

        # if wifiStrength <-70:
        #     wifiStatus = "Weak"

        # Excellent >-50 dBm

        # Good -50 to -60 dBm

        # Fair -60 to -70 dBm

        # Weak < -70 dBm

        # self.wifiSignal.setText("Wifi {status}".format(status=wifiStatus))
   
    def onTelemetryData(self,splittedSensorData,locData=None,deviceStats=None):
        self.AccGraph.setValues(splittedSensorData[0])
        self.GyroGraph.setValues(splittedSensorData[1])
        self.MagGraph.setValues(splittedSensorData[2])
        x = splittedSensorData[3][0]
        y =  splittedSensorData[3][1]
        z = splittedSensorData[3][2]
        z = z+90

        self.updateCompass(locData[-1])

        self.attitudeIndicator.setRoll(z)
        self.attitudeIndicator.setPitch(y)
     
        self.updateStlRotation(z,y,x)

  
        if deviceStats.any():
            if self.battery != deviceStats[0] :
                self.updateDeviceStats(deviceStats)
                self.battery = deviceStats[0]


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.protocol = None
        self.trackerWindow = None
        self.newtworkAdapters:list[NetworkAdapter] = getIpv4AddressWithAdapter()
        self.initUi()    
       


        
    def initUi(self):
        self.setWindowTitle("Dashboard 2.0")

        
        self.dashboard  = Dashboard()
        self.configTab = ConfigTab(self.newtworkAdapters)
        self.configTab.onUsingLocal.connect(self.onLocal)
        self.configTab.onUsingNgrok.connect(self.onNgrok)
        self.tabwidget = QTabWidget()

        self.tabwidget.addTab(self.configTab,'Config')
        self.tabwidget.addTab(self.dashboard,'Dashboard')
        # self.tabwidget.setTabEnabled(1,False)
        
        self.setCentralWidget(self.tabwidget)
        
        # self.resize(w, h)
        self.showMaximized()

    @pyqtSlot(str)
    def onNgrok(self,auth):
        self.dashboard.initServerWithNgrok(auth)
        self.tabwidget.setCurrentIndex(1)

    @pyqtSlot(str,str,int)
    def onLocal(self,adapter,ip,port):
        self.dashboard.initServerWithLocal(ip,port)
        self.tabwidget.setCurrentIndex(1)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.dashboard.stopServer()
            event.accept()
            log.info("window Closed")
        else:
            event.ignore()


if __name__ == "__main__":
    # create logger
    app = QApplication(sys.argv)
    # app.setStyleSheet(qdarkstyle.load_stylesheet())
    window = Window()
    window.show()
    sys.exit(app.exec_())