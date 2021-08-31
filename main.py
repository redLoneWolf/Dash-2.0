# from Dashboard.SteeringTest import State, States, TargetCourse
import sys
import os
from types import TracebackType
from PyQt5 import QtCore, QtGui
import qdarkstyle
import math
from SteeringTest import *
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QBoxLayout, QComboBox, QGridLayout,
    QHBoxLayout, QLayout,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget,
    QMainWindow,
    QTextEdit,
    QMessageBox
)
from PyQt5.QtCore import(
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


log = logging.getLogger('hello')
log.setLevel(logging.INFO)
format = logging.Formatter(fmt="%(asctime)s %(levelname)s %(funcName)s %(message)s",datefmt="%Y-%m-%d %H:%M:%S")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(format)
log.addHandler(ch)

fh = handlers.RotatingFileHandler("dashboard.log", maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(format)
log.addHandler(fh)

DEGTORAD = 0.0174532925199432957

RADTODEG = 57.295779513082320876

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.protocol = None
        self.trackers = ['CSRT','KCF','MedianFlow','MIL','TLD','MOSSE','Boosting']
        self.trackerWindow = None
        self.initUi()    
        self.initServer()
        self.keylist=[]
        self.val = {'m1':0,'m2':0,'m3':0,'m4':0}
        
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
        self.scale_x=0
        self.scale_y=0
        self.scale_z=0
        self.CurrFrameData =None

        self.RC_ENABLED = False
        self.USB_CONNECTED = False
        self.TELEMETRY_STARTED= False
        self.DEPTH_FEED_STARTED = False
        self.CAM_FEED_STARTED= False
        self.WAYPOINT_STARTED = False

        
        
    def initUi(self):
        self.setWindowTitle("Dashboard")

        
        self.initLeftSidebar()
        self.initCenterArea()
        self.initRightSidebar()
        self.initRCControls()
        
       
        
        self.mainWidget = QWidget()
        
        self.grid = QGridLayout()
        self.side = QWidget()
        

        self.side.setLayout(self.sideBar)
        self.side.setMinimumWidth(200)
        self.side.setMinimumHeight(300)
        # self.grid.addLayout(self.stats,0,0)
        self.grid.addWidget(self.side,0,0,Qt.AlignmentFlag.AlignTop)
        # self.grid.addLayout(self.sideBar,0,0)
        self.grid.addLayout(self.camLayout,0,1,1,1)
        self.grid.addWidget(self.depthCam,1,1,1,1)
        # self.grid.addWidget(self.keyWidget,1,1,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignBottom)
        # self.grid.addLayout(self.rigthSidebar,0,3)
        # self.grid.addLayout(self.graphVLayout,3,2)
        
        # self.grid.addLayout(mapLayout,1,1)
        # self.graphVLayout.insertWidget(0,self.keyWidget)
        self.grid.addLayout(self.graphVLayout,2,1,Qt.AlignBottom|Qt.AlignHCenter)
        self.grid.addLayout(self.rigthSidebar,0,3,3,1,Qt.AlignRight)
        self.grid.addLayout(self.keys,2,0,Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)
        # self.mainWidget.setLayout(self.layout1)
        self.mainWidget.setLayout(self.grid)
        # self.setLayout(self.grid)
        self.setCentralWidget(self.mainWidget)
        self.disableLeftSideBar(True)
        self.resize(w, h)

    def initCenterArea(self):
        labels = {'ax':randColor(), 'ay':randColor(), 'az':randColor(), 'gx':randColor(), 'gy':randColor(), 'gz':randColor(), 'x':randColor(), 'y':randColor(), 'z':randColor(),'mx':randColor(), 'my':randColor(), 'mz':randColor()}
        mag = {'mx':genColorCode(255,0,0), 'my':genColorCode(0,255,0), 'mz':genColorCode(0,0,255)}

        
        self.AccGraph= CustomGraph(curveNames=mag,name="Accelerometer in m/s2")
        self.GyroGraph= CustomGraph(curveNames=mag,row=1,col=0,name="Gyroscope in deg/s")
        
        self.MagGraph= CustomGraph(curveNames=mag,row=3,col=0,name="Mag in deg/s")

        self.graphVLayout =  QHBoxLayout()
        self.MagGraph.setMaximumHeight(200)
        self.AccGraph.setMaximumHeight(200)
        self.GyroGraph.setMaximumHeight(200)
        self.graphVLayout.addWidget(self.AccGraph)
        self.graphVLayout.addWidget(self.GyroGraph)
        self.graphVLayout.addWidget(self.MagGraph)
        
                
        
        # self.graphVLayout.addStretch(1)

        self.camLayout = QHBoxLayout() 
        self.cam = CameraWidget(self,ViewName="RGB Cam",ROICallback=self.onROI,ImageCallBack=self.OnImageData)
        # self.cam.ImageCallBack.connect(self.OnImageData)
        self.cam.setMaximumHeight(480)
        self.cam.setMaximumWidth(640)
   
        self.cam.setMinimumHeight(480)
        self.cam.setMinimumWidth(640)
        
        self.depthCam = CameraWidget(ViewName = "Depth Cam")
        self.depthCam.setMaximumHeight(240)
        self.depthCam.setMaximumWidth(320)
        self.depthCam.setMinimumHeight(240)
        self.depthCam.setMinimumWidth(320)
        
        # self.depthCam.show()

        self.camLayout.addWidget(self.cam)
        self.map = MapWidget(self.onWayPointBtn)
        self.map.setMaximumHeight(480)
        self.map.setMaximumWidth(640)
        self.map.setMinimumHeight(480)
        self.map.setMinimumWidth(640)
        self.camLayout.addWidget(self.map)

    @pyqtSlot(np.ndarray)
    def OnImageData(self,data):
        self.CurrFrameData = data
        if(self.trackerWindow is not None):
            print("not none")
            self.trackerWindow.DetectObject(self.CurrFrameData)

    def onTrackBtn(self):
    
        self.trackerWindow = ProcessImage(self.currentTracker,self.CurrFrameData)
        # self.updateTimer = QtCore.QTimer(self)
        # self.updateTimer.timeout.connect(self.updateAI)
        # self.updateTimer.start(1000/self.hz)


    def initRightSidebar(self):
        self.topHbox = QHBoxLayout()
    
        self.connectBtn = QPushButton("Start Server")
        self.connectBtn.clicked.connect(self.onConnectBtn)
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
        self.stlViewer.setMinimumSize(240, 240)
        self.stlViewer.setMaximumSize(240, 240)

        self.compass = CompassWidget()
        self.compass.setMinimumSize(320, 240)
        self.compass.setMaximumSize(320, 240)
        self.attitudeIndicator = AttitudeIndicator()
        self.attitudeIndicator.setMinimumSize(240, 240)
        self.attitudeIndicator.setMaximumSize(240, 240)



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
        self.W.setMinimumSize(30,30)
        self.W.setMaximumSize(30,30)
        self.W.pressed.connect(self.OnPressW)
        self.W.released.connect(self.OnReleaseW)

        self.A = QPushButton("A")
        self.A.setMinimumSize(30,30)
        self.A.setMaximumSize(30,30)
        self.A.pressed.connect(self.OnPressA)
        self.A.released.connect(self.OnReleaseA)

        self.S = QPushButton("S")
        self.S.setMinimumSize(30,30)
        self.S.setMaximumSize(30,30)
        self.S.pressed.connect(self.OnPressS)
        self.S.released.connect(self.OnReleaseS)

        self.D = QPushButton("D")
        self.D.setMinimumSize(30,30)
        self.D.setMaximumSize(30,30)
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
        self.stats = QHBoxLayout()
        self.battery = QTextEdit(self)
    
        self.battery.setReadOnly(True)
        self.battery.setText("Battery 0%")
        self.battery.setMaximumSize(80,20)
        self.battery.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.battery.verticalScrollBar().setDisabled(True)

        

        self.wifiSignal = QTextEdit(self)
        
        self.wifiSignal.setReadOnly(True)
        self.wifiSignal.setText("Wi-Fi No")
        self.wifiSignal.setMaximumSize(80,20)
        self.wifiSignal.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wifiSignal.verticalScrollBar().setDisabled(True)
        self.stats.addWidget(self.battery)
        self.stats.addWidget(self.wifiSignal)

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
        print(self.palette().color(QtGui.QPalette.Base).name())

        # self.trackBtn = QPushButton("Track")
        # self.trackBtn.clicked.connect(self.onTrackBtn)
        # self.sideBar.addWidget(self.trackBtn)

        
        # self.currentTracker = self.trackers.index('KCF')
        self.trkrCombo= QComboBox(self)
        
        # self.trkrCombo.setPlaceholderText("Select tracker")
        self.trkrCombo.currentIndexChanged.connect(self.onTrackerSelect)
        for tracker in self.trackers:
            self.trkrCombo.addItem(tracker)
        self.sideBar.addWidget(self.trkrCombo)



        self.rcBtn = QPushButton("Start RC")
        self.rcBtn.clicked.connect(self.onRCBtn)
        self.sideBar.addWidget(self.rcBtn)

        # self.sideBar.addLayout(self.keys)
        # self.left = QWidget()
        # self.left.setLayout(self.sideBar)
        # self.left.setMaximumHeight(100)
        self.sideBar.addStretch(1)

    def onTrackerSelect(self,selection):
        self.currentTracker = self.trackers[selection]
        print(selection)
        log.info("Selected Tracker : "+self.trackers[selection])

        
    def disableLeftSideBar(self,disable:bool):
        self.connectUSBBtn.setDisabled(disable)

        self.telemetryBtn.setDisabled(disable)


        self.cameraFeedBtn.setDisabled(disable)

        self.depthFeedBtn.setDisabled(disable)

        self.rcBtn.setDisabled(disable)
 

    def OnPressW(self):
        for motor in self.val.keys():
            self.val[motor] = self.val[motor]+25
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

        self.val['m1']+=25  # fixed
        self.val['m3']-=25

        self.val['m2']+=25 # fixed
        self.val['m4']-=25
        

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
            self.val[motor]-=25
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

        self.val['m2']-=25
        self.val['m4']+=25

        self.val['m1']-=25
        self.val['m3']+=25

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

    def keyPressEvent(self, event):
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


    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.protocol.isListening():
                self.protocol.disconnect()

            event.accept()
            log.info("window Closed")
        else:
            event.ignore()


        

    def onWayPointBtn(self,latlongs):
        print(latlongs)
        if self.protocol.isListening() and not self.WAYPOINT_STARTED:
            self.protocol.startWayPoint(latlongs)
            self.WAYPOINT_STARTED = True
        
        elif self.protocol.isListening() and  self.WAYPOINT_STARTED:
            self.protocol.stopWayPoint()

        

    def onUSBBtn(self):
        if self.protocol.isListening() and not self.USB_CONNECTED:
            self.protocol.connectUSB()
            self.USB_CONNECTED = True
            log.info("USB Connected")

        elif self.protocol.isListening() and self.USB_CONNECTED:
            self.protocol.disconnectUSB()
            self.USB_CONNECTED = False
            log.info("USB disonnected")


    def onTelemetryBtn(self):
    
        if self.protocol.isListening() and not self.TELEMETRY_STARTED:
            self.protocol.startTelemetry()
            self.TELEMETRY_STARTED = True
            log.info("Telemetry Started")
            self.telemetryBtn.setText("Stop Telemetry")

        elif self.protocol.isListening() and self.TELEMETRY_STARTED:
            self.protocol.stopTelemetry()
            self.TELEMETRY_STARTED = False
            self.telemetryBtn.setText("Start Telemetry")
            log.info("Telemetry Stopped")


    def onCameraFeedBtn(self):
        if not self.cam.isListening() and self.protocol.isListening() and not self.CAM_FEED_STARTED:
            self.cam.start(self.MainIp,self.MainPort+1)
            log.info("CamFeed Started listening on {}:{}".format(self.MainIp,self.MainPort+1))
            self.protocol.startCamFeed()
            self.cameraFeedBtn.setText("Stop Cam Feed")
            self.CAM_FEED_STARTED = True
            
            

        elif self.cam.isListening() and self.protocol.isListening() and self.CAM_FEED_STARTED:
            self.protocol.stopCamFeed()
            log.info("CamFeed Stopped")
            self.cam.stop()
            self.cameraFeedBtn.setText("Start Cam Feed")
            self.CAM_FEED_STARTED = False
            
        


    def onDepthFeedBtn(self):
        
        if not self.depthCam.isListening() and self.protocol.isListening() and not self.DEPTH_FEED_STARTED:
      
            self.depthCam.start(self.MainIp,self.MainPort+2)
            log.info("DepthFeed Started listening on {}:{}".format(self.MainIp,self.MainPort+2))
            self.protocol.startDepthFeed()
            self.depthFeedBtn.setText("Stop Depth Feed")
            # self.depthCam.show()
            self.DEPTH_FEED_STARTED = True

        elif self.depthCam.isListening() and self.protocol.isListening() and self.DEPTH_FEED_STARTED:
            self.protocol.stopDepthFeed()
            log.info("DepthFeed Stopped")
            self.depthFeedBtn.setText("Start Depth Feed")
            # self.depthCam.hide()
            self.depthCam.stop()
            self.DEPTH_FEED_STARTED = False
        

    def sendRC(self):
        arr = []
        for motor in self.val.keys():
            WithinRange = max(min(128, self.val[motor]), -128)
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
            

    def onROI(self,x,y,width,height):
        if self.protocol.isListening() and self.cam.isListening()  and self.CAM_FEED_STARTED:
            self.protocol.sendROI(x,y,width,height,self.trackers.index(self.currentTracker))
    
    def addMapPoints(self,latLong,angle):
        self.map.updateMapLine(latLong,angle)
    
    def updateStlRotation(self,x,y,z):
        self.stlViewer.updateRotation(x,y,z)
    
    def updateAttitude(self,roll,pitch):
        self.attitudeIndicator.setRollPitch(roll,pitch)

    def updateCompass(self,deg):
        self.compass.setAngle(deg)

    def initServer(self):
        # self.protocol = Protocol(self.onPacketReceive,ip = "192.168.43.214",port=8888)
        
        self.protocol = Protocol(self.onPacketReceive,parent=self)
        self.MainIp = self.protocol.getIp()
        self.MainPort = self.protocol.getPort()
        self.inited =  False

    def onConnectBtn(self):
        if(not self.protocol.isListening()):
            self.startServer()
            self.connectBtn.setText("Stop Server")
            self.ipEditText.setText(self.protocol.getIp())
            self.portEditText.setText(str(self.protocol.getPort()))
            self.disableLeftSideBar(False)
        else:
            self.stopServer()
            self.ipEditText.setText("IP Address")
            self.portEditText.setText("Port")
            self.connectBtn.setText("Start Server")
            self.disableLeftSideBar(True)
    
    

    
    def startServer(self):

        self.protocol.sessionOpened()
        self.protocol.setTelemetryCallBack(self.onTelemetryData)
        if(not self.map.isNotReady()):
            self.map.reload()

    
    def onPacketReceive(command,data):
        # print(command,data)
        pass


  
    def stopServer(self):
        self.map.clear()
        self.protocol.stop()
        
    def updateDeviceStats(self,stats):
        charge = stats[0]
        self.battery.setText("Battery {bat}%".format(bat=charge))

        wifiStrength = stats[1]
        wifiStatus = ""
        if wifiStrength >-50:
            wifiStatus = "Excellent"
        
        if wifiStrength >=-60 and wifiStrength <-50:
            wifiStatus = "Good"

        if wifiStrength >=-70 and wifiStrength <-60:
            wifiStatus = "Fair"

        if wifiStrength <-70:
            wifiStatus = "Weak"

        # Excellent >-50 dBm

        # Good -50 to -60 dBm

        # Fair -60 to -70 dBm

        # Weak < -70 dBm

        self.wifiSignal.setText("Wifi {status}".format(status=wifiStatus))
   
    def onTelemetryData(self,splittedSensorData,locData=None,deviceStats=None):
        self.AccGraph.run(splittedSensorData[0])
        self.GyroGraph.run(splittedSensorData[1])
        self.MagGraph.run(splittedSensorData[3])
        x = splittedSensorData[3][0]
        y =  splittedSensorData[3][1]
        z = splittedSensorData[3][2]
        z = z+90

        # print(locData[-1])
        # sys.exit()
        self.updateCompass(locData[-1])

        self.attitudeIndicator.setRoll(z)
        self.attitudeIndicator.setPitch(y)
     
        self.updateStlRotation(z,y,x)


        # if not self.inited:
            # self.initPlot()

        # self.run(locData[-1],locData[:2])
        

        
        

        
        if deviceStats.any():
            self.updateDeviceStats(deviceStats)
        

        # self.updateAttitude(x,z)
        self.addMapPoints([locData[1],locData[0]],locData[-1])
        # self.updateCompass(locData[-2])
        # print(locData[-2])
        #update data on all
        

    def initPlot(self):
        print("plot init")
        self.inited = True
        self.robotInitialLocation = [10.935963, 0,78.686615]

        # self.initialOrientation = get_bearing_in_degrees() * DEGTORAD
        self.cx=[]
        self.cy=[]
        # if FLAG == "PATH":
        self.path=[]
        self.path.append(self.robotInitialLocation)
        self.path.append([10.936080, 0,78.686124])
        self.path.append([10.936584, 0,78.685885])
        self.path.append([10.936849,0, 78.685765])
        self.path.append([10.937285,0, 78.685709])
        self.path.append([10.93769375549963,0, 78.68631176363178])

        self.cx = [x for x,y,z in self.path]

        self.cy = [z for x,y,z in self.path]


        self.state = State(x=self.robotInitialLocation[0], y=self.robotInitialLocation[2], yaw=0.0, v=0.0)

        self.lastIndex = len(self.cx) - 1
        self.time2 = 0.0
        self.states = States()
        self.states.append(self.time2, self.state)
        self.target_speed = 6.28
        self.target_course = TargetCourse(self.cx, self.cy)
        self.target_ind, _ = self.target_course.search_target_index(self.state)
        print(self.target_ind)
        self.dt =  0.1 
    
    def run(self,magDeg,latlong):
        # print("plot run")
        self.position = self.robotInitialLocation
    
        DX = self.cx[self.target_ind] - self.position[0]
        DY = self.cy[self.target_ind]- self.position[2]
        self.radians = math.atan2(DY,DX)
        self.degrees = self.radians * (180 /math.pi)

        

    
        
        self.turn = self.degrees - magDeg
        self.k = 1
        # print('turn',self.turn)
        self.turn = self.turn % 360
        self.turn =  self.turn * DEGTORAD
        self.turn = -self.turn
        # print("rad :",self.turn)
        self.v =  (6.28)
        # print(self.v)
        # print("in whiles "+ str(self.turn))
        self.ai = proportional_control(self.target_speed, self.state.v)
        self.alpha, self.di, self.target_ind = pure_pursuit_steer_control(self.state, self.target_course, self.target_ind)
        # print("alpha :",self.alpha)
        self.alpha = -self.alpha        #inverting alpha
        print('turn',self.turn*RADTODEG)
        print("alpha :",self.alpha*RADTODEG)
        left_velocity = self.v * (math.cos(self.alpha) - self.k * math.sin(self.alpha)  )

        right_velocity = self.v * (math.cos(self.alpha) + self.k * math.sin(self.alpha)  )

        print(left_velocity,right_velocity)
        
        # Wheels(left_velocity,right_velocity)
        self.state.update(self.ai, self.di)  # Control vehicle

        position = [latlong[0],0,latlong[1]]

        self.state.x = position[0]
        self.state.y = position[2]
        self.state.yaw = magDeg * DEGTORAD

        # print(self.di*RADTODEG)
        
        self.time2 +=self.dt
        self.states.append(self.time2, self.state)
        
        
        # plt.cla()
            
        # plt.gcf().canvas.mpl_connect(
            # 'key_release_event',
            # lambda event: [exit(0) if event.key == 'escape' else None])
        # plot_arrow(state.x, state.y, state.yaw)
        # plt.plot(self.cx, self.cy, "-r", label="course")
        # robotInitialLocation = [cx[target_ind],0,cy[target_ind]]

        # print('cx',self.cx[self.target_ind],'cy',self.cy[self.target_ind])
        # plt.plot(self.states.x, self.states.y, "-d", label="trajectory")
        # plt.plot(self.cx[self.target_ind], self.cy[self.target_ind], "xg", label="target")
        
        # print(self.states.x,self.states.y)
        # plt.axis("equal")
        # plt.grid(True)
        # plt.title("Speed[km/h]:" + str(self.state.v * 3.6)[:4])

        # plt.pause(0.001)
        # print(self.state.yaw)



if __name__ == "__main__":
    # create logger
    app = QApplication(sys.argv)


    # app.setStyleSheet(qdarkstyle.load_stylesheet())
    window = Window()
    window.show()
    sys.exit(app.exec_())