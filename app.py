
import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QAction, QSplashScreen, QSplitter, QLineEdit, QGridLayout, QWidget, QPushButton, QCalendarWidget, QLabel, QVBoxLayout, QSizePolicy
from PySide2.QtOpenGL import QGLWidget
from PySide2.QtCore import Slot, qApp, QFile, QTimer, Qt, QDate
from PySide2.QtGui import QKeySequence, QIcon, QPixmap

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from datetime import datetime, timedelta
from src.SPICE.ephemeris import ephemeris
from src.traj import trajectory
import spiceypy as sp
import numpy as np
import os

import src.visualizeGL as vis
#
# data related
#
viewTime = datetime(2001,6,1)
#
# graphic related
#
#list of everything that will be drawn
drawables = []
defaultTrajColor = [130, 184, 97]

#the root window

class Mouse(object):

    def __init__(self):
        self.pos = [0,0]
        self.draggingIn = None
mouse = Mouse()

class MainWindow(QMainWindow):

    def __init__(self, split):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Grav Assist Simulator")

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage("sample status bar message")

        # Window dimensions
        geometry = qApp.desktop().availableGeometry(self)
        if geometry.width() > 1024 and geometry.height() > 720:
            self.setGeometry(50,50,1024,720)

        # the splitter view is in the center
        self.setCentralWidget(split)

class cntrView(QSplitter):

    def __init__(self, graph, toolbox):
        QSplitter.__init__(self, Qt.Horizontal)

        #prepare graph
        self.graphWidget = graph
        self.addWidget(graph)

        #add toolbox on the right
        self.tBox = toolbox
        self.addWidget(self.tBox)

    def mousePressEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                self.graphWidget.setFocus()
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])
            elif clicked == self.tBox:
                mouse.draggingIn = None
                self.tBox.setFocus()
            else:
                mouse.draggingIn = None
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])
            else:
                mouse.draggingIn = None

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
        if self.childAt(mouse.pos[0], mouse.pos[1]) == self.graphWidget:
            self.graphWidget.mDrag(mouse.pos[0], mouse.pos[1])

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.parent().close()
        else:
            self.graphWidget.kPress(e.key())

class Toolbox(QWidget):
    def __init__(self):
        QWidget.__init__(self, None)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.content = []

        #add elements
        #def addWidget (arg__1, row, column, rowSpan, columnSpan[, alignment=Qt.Alignment()])
        #def addWidget (arg__1, row, column[, alignment=Qt.Alignment()])

        #animate button
        animate = QPushButton('animate', self)
        animate.setToolTip('start animation')
        animate.clicked.connect(self.anim)
        self.animate = animate
        self.layout.addWidget(animate, 3, 1, rowSpan = 1, columnSpan = 2)

        #label
        l1 = QLabel()
        l1.setText("start time")
        l1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #l1.setFixedHeight(30)
        self.layout.addWidget(l1, 1, 1)
        #calendar1
        calendar1 = QCalendarWidget()
        calendar1.setGridVisible(True)
        calendar1.setHorizontalHeaderFormat(QCalendarWidget.NoHorizontalHeader)
        calendar1.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar1.setFixedSize(200,200)
        #calendar1.clicked.connect(self.showDate)
        self.calendar1 = calendar1
        self.layout.addWidget(calendar1, 2, 1)
        #label
        l2 = QLabel()
        l2.setText("end time")
        l2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #l2.setFixedHeight(30)
        self.layout.addWidget(l2, 1, 2)
        #calendar2
        calendar2 = QCalendarWidget()
        calendar2.setGridVisible(True)
        calendar2.setHorizontalHeaderFormat(QCalendarWidget.NoHorizontalHeader)
        calendar2.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar2.setFixedSize(200,200)
        #calendar2.clicked.connect(self.showDate)
        self.calendar2 = calendar2
        self.layout.addWidget(calendar2, 2, 2)

        l3 = QLabel()
        self.layout.addWidget(l3, 4, 1)

    def anim(self):
        global gl
        global viewTime
        s = self.calendar1.selectedDate().toPython()
        f = self.calendar2.selectedDate().toPython()
        print(s, f)
        if s < f:
            viewTime = s
            gl.animate(self.calendar2.selectedDate().toPython())

class glWidget(QGLWidget):

    def __init__(self):
        QGLWidget.__init__(self, None)
        self.setMinimumSize(640, 480)
        self.makeCurrent()
        self.initted = False
        self.initializeGL()

    def paintGL(self):
        global drawables
        window.status.showMessage("drawing")

        #all the planets
        for i in vis.planets:
            if i == 'SUN':
                up = [0,0,1]
                traj = None
            else:
                #up = np.cross(vis.planets[i].body.state(viewTime)[0:3], vis.planets[i].body.state(viewTime)[4:6])
                #up /= np.linalg.norm(up)
                global ephem
                traj = trajectory(vis.planets['SUN'].body, viewTime, vis.planets[i].body.state(viewTime))
                up = traj.up

                global defaultTrajColor
                #color, foc, ecc, matrix, a, angleIn=0, angleOut=0
                trajDraw = vis.orbit(defaultTrajColor, [0,0,0], traj.rMtrx, traj.elements['A'], traj.elements['ECC'])
                drawables.append(vis.drawable(trajDraw))

            #                                                      position                 upwards direction
            drawables.append(vis.drawable(vis.planets[i], vis.planets[i].body.state(viewTime)[0:3], up))

        vis.draw(drawables)
        drawables = []

        window.status.showMessage("solar system at: "+viewTime.strftime("%Y-%m-%d"))

    def animate(self, fTime):
        global viewTime
        if viewTime >= fTime:
            return
        #print(viewTime)
        viewTime += timedelta(days = 1)
        self.updateGL()
        QTimer.singleShot(50, (lambda: self.animate(fTime)))

    def resizeGL(self, w, h):
        vis.reshape(w, h)

    def initializeGL(self):
        global ephem

        if not self.initted:
            vis.init(1024, 720)
            for i in vis.planets:
                vis.planets[i].body = ephem.get_body(i)
        self.initted = True

    def mClick(self, button, state, x, y):
        vis.mouseclick(button, state, x, y)
        self.updateGL()

    def mDrag(self, x, y):
        vis.mousemotion(x, y)
        self.updateGL()

    def kPress(self, key):
        vis.keydown(key, 0, 0)
        self.updateGL()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    #loading screen
    loading = QSplashScreen(QPixmap('assets/loading-min.jpg').scaled(640,480))
    loading.show()
    loading.setStyleSheet('font-size: 18pt; font-family: Courier; color: rgb(255, 255, 255)')
    loading.showMessage("picture by NASA/JPL-Caltech/Univ. of Arizona\nMars Reconnaissance Orbiter (MRO)\nid: PIA17646")

    #SPICE initializations
    global ephem
    root_dir = os.path.abspath(os.getcwd())
    ephem = ephemeris(sp, root_dir)

    #construct gl widget
    global gl
    gl = glWidget()

    global tbox
    tbox = Toolbox()

    #construct central splitter view
    global splitter
    splitter = cntrView(gl, tbox)

    #initialize main window
    global window
    window = MainWindow(splitter)

    window.show()
    #splash.close()
    loading.finish(window)

    app.exec_()
