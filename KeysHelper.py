from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, pyqtProperty
import sys

from pynput.keyboard import Key, Listener, KeyCode


class KeyMonitor(QObject):
    keyPressed = pyqtSignal(KeyCode)
    keyReleased = pyqtSignal(KeyCode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listener = Listener(on_press=self.on_press,on_release=self.on_release)

    def on_press(self,key):
        if(type(key)==KeyCode):
            self.keyPressed.emit(key)

    def on_release(self, key):
        if(type(key)==KeyCode):
            self.keyReleased.emit(key)

    def stop_monitoring(self):
        self.listener.stop()

    def start_monitoring(self):
        self.listener.start()



class KeysWidget(QWidget):

    def __init__(self, parent = None):
    
        QWidget.__init__(self, parent)
        self.val = {'m1':0,'m2':0,'m3':0,'m4':0}

        self.setMaximumSize(250,250)
        self.setMinimumSize(250,250)
        self.W = QPushButton("W")
        self.W.setMinimumSize(50,50)
        self.W.setMaximumSize(50,50)

        self.A = QPushButton("A")
        self.A.setMinimumSize(50,50)
        self.A.setMaximumSize(50,50)

        self.S = QPushButton("S")
        self.S.setMinimumSize(50,50)
        self.S.setMaximumSize(50,50)

        self.D = QPushButton("D")
        self.D.setMinimumSize(50,50)
        self.D.setMaximumSize(50,50)

        
        self.keys = QGridLayout()
        self.keys.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keys.addWidget(self.W,0,1)
        self.keys.addWidget(self.A,1,0)
        self.keys.addWidget(self.D,1,2)
        self.keys.addWidget(self.S,1,1)
        self.setLayout(self.keys)

        self.monitor = KeyMonitor()
        self.monitor.keyPressed.connect(self.onPress)
        self.monitor.keyPressed.connect(self.onRelease)
        self.monitor.start_monitoring()

    def OnPressW(self):
        self.W.click()
        for motor in self.val.keys():
            print(1)
            self.val[motor] = self.val[motor]+1

    def OnReleaseW(self):
        print('rel')
        self.W.click()
        for motor in self.val.keys():
            self.val[motor] = 0

    def OnPressA(self):
        self.val['m2']+=1
        self.val['m4']+=1

    def OnReleaseA(self):
        self.val['m2'] = self.val.get('m1')
        self.val['m4'] = self.val.get('m1')


    def OnPressS(self):
        for motor in self.val.keys():
            self.val[motor]-=1

    def OnReleaseS(self):
        for motor in self.val.keys():
            self.val[motor] = 0

    

    def OnPressD(self):
        self.val['m1']+=1
        self.val['m3']+=1

    def OnReleaseD(self):
        self.val['m1'] = self.val.get('m2')
        self.val['m3'] = self.val.get('m2')

    @pyqtSlot(KeyCode)
    def onPress(self,key):
        pressed = key.char
        if(pressed=='w'):
            self.OnPressW()
        if(pressed=='a'):
            self.OnPressA()
        if(pressed=='s'):
            self.OnPressS()
        if(pressed=='d'):
            self.OnPressD()
        print(self.val)
            
        

    @pyqtSlot(KeyCode)
    def onRelease(self,key):
        released = key.char
        if(released=='w'):
            self.OnReleaseW()
        if(released=='a'):
            self.OnReleaseA()
        if(released=='s'):
            self.OnReleaseS()
        if(released=='d'):
            self.OnReleaseD()



if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    window = KeysWidget()
    
    window.show()
    sys.exit(app.exec_())