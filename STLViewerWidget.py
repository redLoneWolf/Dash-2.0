from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from PyQt5.QtWidgets import (

    QApplication, QPushButton, QVBoxLayout,
    QWidget,
    QMainWindow,
)
import pyqtgraph.opengl as gl
import numpy as np

class STLViewerWidget(QWidget):
    def __init__(self):
        super(STLViewerWidget, self).__init__()
        # self.setGeometry(0, 0, 512, 512)         
        self.initUI()
        self.hi = 90
        self.currentSTL = None

        # print("Hello")        
        self.showSTL()
        self.rx = 0
        self.ry = 0 
        self.rz = 0 

        self.timer=QTimer()
     


    def start(self):
        self.timer=QTimer()
        self.timer.timeout.connect(self.updateRotation)
        self.timer.start(100)

    def stop(self):
        if self.timer.isActive():
            self.timer.stop()

    def initUI(self):
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.viewer = gl.GLViewWidget()
        layout.addWidget(self.viewer, 1)
       
        

        self.viewer.setCameraPosition(distance=10)
        
        g = gl.GLGridItem()
        g.setSize(200, 200)
        g.setSpacing(5, 5)
        self.viewer.addItem(g)
        
        # timer = QTimer(self)
        # timer.setInterval(200)   # period, in milliseconds
        # timer.timeout.connect(self.updateRotation)
        # timer.start()
            
    def showSTL(self, filename='hi'):
        vertices = np.array([ 
                [-3, -2, -0.5], # first
                [+3, -2, -0.5],
                [+3, +2, -0.5],
                [-3, +2, -0.5],

                [-3, -2, +0.5],
                [+3, -2, +0.5],
                [+3, +2, +0.5],
                [-3, +2, +0.5]])
            # Define the 12 triangles composing the cube

        vertices = np.array([ 
                [-0.5, -4, -2], # first
                [+0.5, -4, -2],
                [+0.5, +4, -2],
                [-0.5, +4, -2],

                [-0.5, -4, +2],
                [+0.5, -4, +2],
                [+0.5, +4, +2],
                [-0.5, +4, +2]])
        
        cubeClrArray = np.array(
                [[1.0, 0.0, 1.0],
                 [1.0, 0.0, 0.0],
                 [1.0, 0.0, 0.0],
                 [1.0, 0.0, 0.0],
                 [1.0, 0.0, 0.0],
                 [1.0, 0.0, 0.0],
                 [1.0, 0.0, 0.0],
                 [1.0, 0.0, 0.0]])

        faces = np.array([\
                [0,3,1],
                [1,3,2],
                [0,4,7],
                [0,7,3],

                [4,5,6],
                [4,6,7],
                [5,1,2],
                [5,2,6],

                [2,3,6],
                [3,7,6],
                [0,1,5],
                [0,5,4]
                ])
        meshdata = gl.MeshData(vertexes=vertices, faces=faces,faceColors=cubeClrArray)
        mesh = gl.GLMeshItem(meshdata=meshdata, smooth=True, drawFaces=True, drawEdges=True, edgeColor=(0, 1, 0, 1),computeNormals=False, )
        axis  =  gl.GLAxisItem()
        self.viewer.addItem(axis)
        self.viewer.addItem(mesh)
        
        self.currentSTL = mesh

    def setValues(self,x,y,z):
        self.rx = x
        self.ry = y
        self.rz = z 

    def updateRotation(self,):
        # print("hi")
        # self.currentSTL.translate(0,0,0)
        self.currentSTL.resetTransform()
        self.currentSTL.rotate(self.rx,1,0,0)
        self.currentSTL.rotate(self.ry,0,1,0)
        self.currentSTL.rotate(self.rz,0,0,1)
        # self.hi = self.hi + 1
        # self.currentSTL.rotate(w,x,y,z)

if __name__ == '__main__':
    app = QApplication([])
    window = STLViewerWidget()
    window.show()
    app.exec_()