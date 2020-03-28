
import sys
from PySide2.QtWidgets import QApplication, QLabel, QMainWindow, QAction, QSplashScreen, QDialog
from PySide2.QtOpenGL import QGLWidget
from PySide2.QtCore import Slot, qApp, QFile, QTimer, Qt
from PySide2.QtGui import QKeySequence, QIcon, QPixmap

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import src.visualizeGL as vis
import datetime

drawables = []

class Mouse(object):

    def __init__(self):
        self.left = False
        self.right = False
        self.pos = [0,0]
        self.draggingIn = None

mouse = Mouse()

class MainWindow(QMainWindow):

    def __init__(self, graph):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Window Title")
        self.setWindowIcon(QIcon("assets/icon.png"))

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage("sample status bar message")

        # Window dimensions
        geometry = qApp.desktop().availableGeometry(self)
        self.setFixedSize(1024,720)
        self.setMinimumSize(660,500)
        self.move(50,50)

        print("before adding graph")
        #prepare graph
        self.graphWidget = graph
        self.setCentralWidget(graph)
        print("central")

    def mousePressEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])

    def mouseReleaseEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = None
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_UP, mouse.pos[0], mouse.pos[1])
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = None
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_UP, mouse.pos[0], mouse.pos[1])

    def mouseMoveEvent(self, e):
        #print(e)
        mouse.pos = [e.x(), e.y()]

        if mouse.draggingIn == self.graphWidget:
            self.graphWidget.mDrag(mouse.pos[0], mouse.pos[1])

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            print(e.key())


class glWidget(QGLWidget):

    def __init__(self):
        QGLWidget.__init__(self, None)
        self.setMinimumSize(640, 480)
        self.makeCurrent()
        self.initted = False
        self.initializeGL()

    def paintGL(self):
        global drawables

        vis.draw(drawables)

    def resizeGL(self, w, h):
        vis.reshape(w, h)

    def actualInit(self):
        vis.init(1024,720)
        global drawables
        x = 0
        for i in vis.planets:
            drawables.append(vis.drawable(vis.planets[i],cvrt([4*x, 1 * x,0]), cvrt([1,-1,0])))
            x += 1

        for i in drawables:
            print(i.obj," at ", i.pos)

    def initializeGL(self):
        if not self.initted:
            self.actualInit()
        self.initted = True

    def mClick(self, button, state, x, y):
        vis.mouseclick(button, state, x, y)
        self.updateGL()

    def mDrag(self, x, y):
        vis.mousemotion(x, y)
        self.updateGL()

def cvrt(pos):
    return [pos[0], pos[2], pos[1]]

if __name__ == '__main__':
    app = QApplication(sys.argv)

    #loading screen
    loading = QSplashScreen(QPixmap('assets/loading-min.jpg').scaled(640,480))
    loading.show()
    loading.setStyleSheet('font-size: 18pt; font-family: Courier; color: rgb(255, 255, 255)')
    loading.showMessage("picture by NASA/JPL-Caltech/Univ. of Arizona\nMars Reconnaissance Orbiter (MRO)\nid: PIA17646")

    #insert spice initializations here


    #construct gl widget
    gl = glWidget()

    #initialize main window
    window = MainWindow(gl)

    window.show()
    #splash.close()
    loading.finish(window)

    app.exec_()
