
import sys
import os
os.environ['OPENBLAS_NUM_THREADS']='1' #multithread conflict fix
#os.system('echo $OPENBLAS_NUM_THREADS')

#from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtOpenGL import QGLWidget
from PySide2.QtCore import *

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from datetime import datetime, timedelta
from src.SPICE.ephemeris import ephemeris
from src.traj import trajectory
from src.optimize import *
from src.lambert import *
from src.voyager_missions import *
from src.path import *
import spiceypy as sp
import numpy as np
#np.show_config()

import src.visualizeGL as vis
import faulthandler

from importlib import reload

#
# data related
#
viewTime = datetime(2001,1,1)
faulthandler.enable()
#
# graphic related
#
#list of everything that will be drawn
drawables = []
defaultTrajColor = [130, 184, 97]
trajColors = [[255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255], [255,255,255]]
flightPathColor = [156, 61, 219] #yay purple
probePathColor = [156, 61, 219]

framerate = 30.0

known_missions = [
    'VOYAGER 1',
    'VOYAGER 2'
]

class Mouse(object):

    def __init__(self):
        self.pos = [0,0]
        self.draggingIn = None

mouse = Mouse()

class MissionCalculator(QRunnable):
    def __init__(self, mName):
        super(MissionCalculator, self).__init__()

        self.mName = mName
        self.signals = Signals()

    def run(self, ephem_=None):
        try:
            #calculate for given mission
            global results
            global ephem

            if not ephem_: ep = ephem
            else: ep = ephem_

            if self.mName == 'VOYAGER 1':
                results = [voyager1_recreated(ep), voyager1_original(ep)]
            elif self.mName == 'VOYAGER 2':
                results = [voyager2_recreated(ep), voyager2_original(ep)]

        except Exception as e:
            print('error:', e)
            self.signals.error.emit(69)
            traceback.print_last()
        except Warning as e:
            print('error:', e)
            self.signals.error.emit(420)
            traceback.print_last()
        else:
            self.signals.finished.emit()


class LambertCalculator(QRunnable):

    def __init__(self, departure, arrival, earliest, latest, sun):
        super(LambertCalculator, self).__init__()

        #take input for the run function
        self.departure = departure
        self.arrival = arrival
        self.earliest = earliest
        self.latest = latest
        self.sun = sun

        self.signals = Signals()

    @Slot()
    def run(self):
        try:
            K = 5  #sample density and decay rate
            N = 1  #how many solutions to keep
            ITERS = 2 #for descent minimization
            tE, tL = self.earliest, self.latest
            GM = self.sun.Gmass[0]
            F = lambda t0, T: direct_transfer_cost(self.departure, self.arrival, t0, T, GM)[0]
            C = lambda t0, T: t0 + T < tL

            #sample for initial conditions
            inits = []
            for i in range(K):
                for j in range(K):
                    t0_ = tE + (tL-tE) * i / K
                    T_ = (tL - t0_) * j / K
                    dV = F(t0_, T_)
                    if dV: inits.append([dV, t0_, T_])
            inits = sorted(inits, key=lambda x: x[0])

            #descend to local minima
            ranges = [[tE, tL], [timedelta(days=0), tL-tE]]
            steps = [(tL-tE)/K/K, (tL-tE)/K/K]
            solutions = []
            for initial in inits[:N]:
                pinit = initial[1:]
                res = decaying_descent(F, ranges, steps, pinit,
                           condition=C, iters = ITERS, decay_factor=K)
                dV, solution = direct_transfer_cost(self.departure, self.arrival, res[0], res[1], GM)
                solutions.append([dV, res[0], res[1], solution])
            solutions = sorted(solutions, key=lambda x: x[0])

            global results
            results = [path(t0, dV, T, [t0], [trajectory(self.sun, t0, np.concatenate((self.departure.state(t0)[:3], sol['v1'])), t0+T)]) for dV, t0, T, sol in solutions]

        except Exception as e:
            print('error:', e)
            self.signals.error.emit(69)
            traceback.print_last()
        except Warning as e:
            print('error:', e)
            self.signals.error.emit(420)
            traceback.print_last()
        else:
            self.signals.finished.emit()

class Signals(QObject):

    finished = Signal()
    error = Signal(int)

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Grav Assist Simulator")

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage("sample status bar message")

        # Window dimensions
        geometry = QApplication.desktop().availableGeometry(self)
        if geometry.width() > 1024 and geometry.height() > 720:
            self.setGeometry(50,50,1024,720)

        tbox = Toolbox()
        gl1 = glWidget()
        gl2 = glWidget()

        self.splitter = cntrView(gl1, tbox)
        self.player = plyrView(gl2)

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.splitter)
        self.stacked.addWidget(self.player)

        self.setCentralWidget(self.stacked)

        self.useSplitter()

    def useSplitter(self):

        #cancel selection
        global selectedSolution
        selectedSolution = None
        #self.splitter = cntrView(glWidget(), Toolbox())
        #vis.init()
        self.splitter.graphWidget.initializeGL()
        vis.defaultConfig()
        self.stacked.setCurrentWidget(self.splitter)

        self.splitter.graphWidget.resizeGL(self.splitter.graphWidget.frameGeometry().width()*2, self.splitter.graphWidget.frameGeometry().height()*2)


    def usePlayer(self):
        global selectedSolution
        if selectedSolution == None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("You need to choose a particular solution!")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
        else:
            #self.player = plyrView(glWidget())
            self.player.reset()
            self.player.notifyChange()
            self.stacked.setCurrentWidget(self.player)
            self.player.graphWidget.resizeGL(self.player.graphWidget.frameGeometry().width()*2, self.player.graphWidget.frameGeometry().height()*2)

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
        pass
        """
        if e.key() == Qt.Key_Escape:
            self.parent().close()
        else:
            self.graphWidget.kPress(e.key())"""

class Toolbox(QWidget):
    def __init__(self):
        QWidget.__init__(self, None)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.content = []

        #label
        l0 = QLabel()
        l0.setText("known missions")
        l0.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.layout.addWidget(l0, 0, 0)

        #missions selector
        self.missions = QComboBox()
        global known_missions
        self.missions.addItem('--custom setting--')
        self.missions.addItems(known_missions)
        self.missions.currentIndexChanged.connect(self.missionToggle)
        self.layout.addWidget(self.missions, 0, 1)

        #label
        l1 = QLabel()
        l1.setText("earliest departure")
        l1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.layout.addWidget(l1, 1, 0)
        #calendar1
        calendar1 = QCalendarWidget()
        calendar1.setGridVisible(True)
        calendar1.setHorizontalHeaderFormat(QCalendarWidget.NoHorizontalHeader)
        calendar1.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar1.activated.connect(lambda: self.refreshCal(calendar1)) #refresh
        calendar1.currentPageChanged.connect(lambda: self.refreshCal(calendar1)) #refresh
        calendar1.setFixedSize(200,200)
        #calendar1.clicked.connect(self.showDate)
        self.calendar1 = calendar1
        self.layout.addWidget(calendar1, 2, 0)
        #label
        l2 = QLabel()
        l2.setText("latest arrival")
        l2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #l2.setFixedHeight(30)
        self.layout.addWidget(l2, 1, 1)
        #calendar2
        calendar2 = QCalendarWidget()
        calendar2.setGridVisible(True)
        calendar2.setHorizontalHeaderFormat(QCalendarWidget.NoHorizontalHeader)
        calendar2.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar2.activated.connect(lambda: self.refreshCal(calendar2)) #refresh
        calendar2.currentPageChanged.connect(lambda: self.refreshCal(calendar2)) #refresh
        calendar2.setFixedSize(200,200)
        #calendar2.clicked.connect(self.showDate)
        self.calendar2 = calendar2
        self.layout.addWidget(calendar2, 2, 1)

        l3 = QLabel()
        l3.setText('departure from')
        self.layout.addWidget(l3, 3, 0)

        #departure selector
        self.departure = QComboBox()
        self.departure.addItems(['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'])
        self.layout.addWidget(self.departure, 3, 1)

        l4 = QLabel()
        l4.setText('arrive at')
        self.layout.addWidget(l4, 4, 0)

        #arrival selector
        self.arrival = QComboBox()
        self.arrival.addItems(['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'])
        self.layout.addWidget(self.arrival, 4, 1)

        #calculate button
        self.calculate = QPushButton('calculate path', self)
        self.calculate.clicked.connect(self.report)
        self.layout.addWidget(self.calculate, 5, 0, rowSpan = 1, columnSpan = 2)

        #list of solutions
        l5 = QLabel()
        l5.setText('available paths')
        self.layout.addWidget(l5, 6, 0)
        self.solutions = QTreeWidget()
        hd = QTreeWidgetItem()
        self.solutions.setHeaderLabels(['launch','deltaV (km/s)', 'duration (yr)', 'flyby'])

        self.layout.addWidget(self.solutions, 7, 0, 1, 2)

        global selectedSolution
        selectedSolution = None

        #animate button
        self.animate = QPushButton('view animated', self)
        self.animate.clicked.connect(self.anim)
        self.layout.addWidget(self.animate, 8, 0, rowSpan = 1, columnSpan = 2)

        l6 = QLabel()
        l6.setText('app by Andre He & Alan Tao\ndata from JPL SPICE Toolkit, app built with PySide2 and FBS, textures from Solar System Scope')
        l6.setWordWrap(True)
        l6.setStyleSheet("QLabel { color : gray;}")
        self.layout.addWidget(l6, 9, 0, 1, 2)

    def missionToggle(self):
        mName = self.missions.currentText()
        global known_missions
        if mName in known_missions:
            #disable the custom parts
            self.calendar1.setEnabled(False)
            self.calendar2.setEnabled(False)
            self.departure.setEnabled(False)
            self.arrival.setEnabled(False)
        else:
            #enable the custom parts
            self.calendar1.setEnabled(True)
            self.calendar2.setEnabled(True)
            self.departure.setEnabled(True)
            self.arrival.setEnabled(True)

    def refreshCal(self, calendar):
        #print('refresh')
        calendar.hide()
        calendar.show()

    def report(self):
        #if a known mission is selected -> use grav assist
        mName = self.missions.currentText()
        calc = 0
        global known_missions
        if mName in known_missions:
            calc = MissionCalculator(mName)

        else:
            #if a custome setup is selected -> use lambert
            earliest = self.calendar1.selectedDate().toPython()
            earliest = datetime(year=earliest.year, month=earliest.month, day=earliest.day)
            latest = self.calendar2.selectedDate().toPython()
            latest = datetime(year=latest.year, month=latest.month, day=latest.day)
            if earliest >= latest:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText('latest arrival should come after earliest departure')
                msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                return
            depart = self.departure.currentText()
            arrive = self.arrival.currentText()
            if depart == arrive:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText('departure must be different from arrival')
                msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                return
            print('calculate the optimal path from', depart,' to ', arrive, ' that starts after', earliest,' and arrives before', latest)

            #QRunnable for calculation
            calc = LambertCalculator(ephem.get_body(depart.upper()), ephem.get_body(arrive.upper()), earliest, latest, ephem.get_body('SUN'))

        self.threadpool = QThreadPool()

        #loading message
        self.loadingMessage = QMessageBox()
        self.loadingMessage.setText("calculating...")
        self.loadingMessage.setIcon(QMessageBox.NoIcon)
        self.loadingMessage.setStandardButtons(QMessageBox.NoButton)

        calc.signals.finished.connect(self.resultGot) #finishing background calculations turn off the loading box
        calc.signals.error.connect(lambda: self.spawnError('error during calculation')) #throw error

        self.threadpool.start(calc)
        self.loadingMessage.exec_()

    def resultGot(self):

        #close the loading message
        self.loadingMessage.done(0)

        #update solutions list
        self.solutions.clear()

        #add new result to list
        global results

        #print(results)
        for i in results:
            iItem = QTreeWidgetItem([
                i.launch.strftime('%Y.%m.%d'),
                str(i.deltaV),
                str(i.duration.total_seconds()/ 31556952),
                ', '.join([f for f in i.flyby if f != 'SUN'])
            ])
            self.solutions.addTopLevelItem(iItem)

    def spawnError(self, errMessage):

        #close the loading message first
        self.loadingMessage.done(0)

        #run new error message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(errMessage)
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()

    def anim(self):
        global results
        global selectedSolution

        selectedSolution = results[self.solutions.indexFromItem(self.solutions.currentItem()).row()]

        global viewTime
        viewTime = selectedSolution.launch

        #calculate positions
        global probePositions

        probePositions = []
        tTemp = timedelta(seconds = 0)
        tIncr = timedelta(days = 1)

        while tTemp < selectedSolution.duration:
            probePositions.append(selectedSolution.getPosition(tTemp.total_seconds()))
            tTemp += tIncr

        global window
        window.usePlayer()

        """
        global gl
        global viewTime
        s = self.calendar1.selectedDate().toPython()
        f = self.calendar2.selectedDate().toPython()
        print(s, f)
        if s < f:
            viewTime = s
            gl.animate(self.calendar2.selectedDate().toPython())"""


class plyrView(QWidget):
    def __init__(self, graph):
        QWidget.__init__(self, None)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        #animate button
        self.back = QPushButton('back', self)
        self.back.setToolTip('go back to input page')
        self.back.clicked.connect(self.switch)
        self.layout.addWidget(self.back, 0, 0)

        #screen
        self.graphWidget = graph
        self.layout.addWidget(graph, 1, 0, 1, 8)
        self.graphWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        #progress slider
        self.progress = QSlider(Qt.Horizontal)
        self.progress.sliderPressed.connect(self.progressPrs)
        self.progress.sliderReleased.connect(self.progressRls)
        self.layout.addWidget(self.progress, 2, 1, 2, 1)

        #play/pause button
        self.isPlaying = False
        self.wasPlaying = False
        self.play = QPushButton('\u25B6', self)
        self.play.setToolTip('play/pause')
        self.play.clicked.connect(self.playBtn)
        self.play.setStyleSheet('QPushButton {font-weight: bold;}')
        self.layout.addWidget(self.play, 2, 0, 2, 1)

        #speed button
        spdLbl = QLabel()
        spdLbl.setText("video speed: ")
        spdLbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.layout.addWidget(spdLbl, 2, 2)
        self.speed = QPushButton('7 days/second')
        self.speed.setToolTip('change playing speed')
        self.speed.clicked.connect(self.changeSpd)
        self.layout.addWidget(self.speed, 3, 2)
        self.vidSpeed = 604800 # in seconds per second

        #view mode button
        mdLbl = QLabel()
        mdLbl.setText('camera mode')
        self.layout.addWidget(mdLbl, 2, 3)
        self.mode = QComboBox()
        self.mode.addItems(['chase','bird\'s eye','flyby'])
        self.mode.currentIndexChanged.connect(self.setMode)
        self.vidMode = 0
        self.layout.addWidget(self.mode, 3, 3)

        """
        #info button
        self.info = QPushButton('info')
        self.info.setToolTip('show info about path')
        self.info.clicked.connect(self.showInfo)
        self.layout.addWidget(self.info, 3, 4)"""

    def reset(self):
        #animate button
        self.back = QPushButton('back', self)
        self.back.setToolTip('go back to input page')
        self.back.clicked.connect(self.switch)
        self.layout.addWidget(self.back, 0, 0)

        #screen
        self.graphWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        #progress slider

        #play/pause button
        self.isPlaying = False
        self.wasPlaying = False
        self.play.setText('\u25B6')
        self.play.setToolTip('play/pause')
        self.play.setStyleSheet('QPushButton {font-weight: bold;}')

        #speed button
        self.speed.setText('7 days/second')
        self.speed.setToolTip('change playing speed')
        self.vidSpeed = 604800 # in seconds per second

        #view mode button
        self.vidMode = 0

        """
        #info button
        self.info = QPushButton('info')
        self.info.setToolTip('show info about path')
        self.info.clicked.connect(self.showInfo)
        self.layout.addWidget(self.info, 3, 4)"""

    def notifyChange(self):
        global selectedSolution
        ss = selectedSolution

        self.progress.setMinimum(0)
        self.progress.setMaximum(ss.duration.total_seconds())
        self.progress.setValue(0)

    def playBtn(self):
        if self.isPlaying == True:
            self.wasPlaying = False
            self.pauseVid()
        else:
            self.wasPlaying = True

            global viewTime
            global selectedSolution
            #if finished, then go back to beginning
            #print(selectedSolution.launch+selectedSolution.duration)
            if viewTime >= selectedSolution.launch+selectedSolution.duration - timedelta(days = 1):
                #print("we've reached the end game")
                self.progress.setValue(0)

            self.playVid()

    def recurDraw(self):
        if self.isPlaying:
            global viewTime
            global selectedSolution
            viewTime = selectedSolution.launch + timedelta(seconds=self.progress.value())

            global framerate
            dT = timedelta(seconds = self.vidSpeed / framerate)
            viewTime = viewTime + dT
            self.progress.setValue(round((viewTime-selectedSolution.launch).total_seconds()))

            if viewTime > selectedSolution.launch + selectedSolution.duration:
                self.updateCam()
                self.graphWidget.updateGL()
                self.pauseVid()
                return

            QTimer.singleShot(round(1000 / framerate), self.recurDraw)

            self.updateCam()
            self.graphWidget.updateGL()

    def updateCam(self):
        global selectedSolution, viewTime
        deltaT = (viewTime - selectedSolution.launch).total_seconds()
        #chase
        if self.vidMode == 0:
            vis.autoChase(selectedSolution.getPosition(deltaT))

        #flyby
        elif self.vidMode == 2:
            body = selectedSolution.getTrajectory(deltaT).body
            if not body.name == 'SUN':
                vis.autoFlyby(body.state(viewTime), body.soi(viewTime))
            else:
                vis.autoSolarCenter()

        #bird eye
        elif self.vidMode == 1:
            global solarSystemPlaneUP
            vis.autoBirdEye(solarSystemPlaneUP, selectedSolution.getTrajectory(deltaT).body.state(viewTime))


    def playVid(self):
        #print('playing')
        self.play.setText('\u2759\u2759')
        self.play.hide()
        self.play.show()
        self.isPlaying = True

        self.recurDraw()

    def pauseVid(self):
        #print('pausing')
        self.play.setText('\u25B6')
        self.play.hide()
        self.play.show()
        self.isPlaying = False

    def progressPrs(self):
        if self.isPlaying:
            self.pauseVid()

    def progressRls(self):

        #update screen
        global viewTime
        global selectedSolution
        viewTime = selectedSolution.launch + timedelta(seconds=self.progress.value())

        self.updateCam()
        self.graphWidget.updateGL()

        if self.wasPlaying:
            self.playVid()

    def changeSpd(self):
        if self.isPlaying:
            self.pauseVid()

        if self.vidSpeed==1 * 86400:
            self.vidSpeed = 7 * 86400
            self.speed.setText('7 days/second')
        elif self.vidSpeed == 7 * 86400:
            self.vidSpeed = 30 * 86400
            self.speed.setText('30 days/second')
        elif self.vidSpeed == 30 * 86400:
            self.vidSpeed = 100 * 86400
            self.speed.setText('100 days/second')
        elif self.vidSpeed == 100 * 86400:
            self.vidSpeed = 1 * 86400
            self.speed.setText('1 day/second')

        self.speed.hide()
        self.speed.show()

        if self.wasPlaying:
            self.playVid()

    def setMode(self):
        if self.isPlaying:
            self.pauseVid()
        print(self.mode.currentText(), self.mode.currentIndex())
        self.vidMode = self.mode.currentIndex()

        if self.wasPlaying:
            self.playVid()

    def showInfo(self):
        if self.isPlaying:
            self.pauseVid()
        #show info here
            #apejfaioejfaper
        if self.wasPlaying:
            self.playVid()

    def switch(self):
        global window
        window.useSplitter()

    def mousePressEvent(self, e):
        global mouse
        clicked = self.childAt(mouse.pos[0], mouse.pos[1])
        mouse.pos = [e.x(), e.y()]

        if e.button() == Qt.MouseButton.LeftButton:
            if clicked == self.graphWidget:
                self.graphWidget.setFocus()
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_LEFT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])

                if self.isPlaying:
                    self.pauseVid()
            else:
                mouse.draggingIn = None
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = self.graphWidget
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_DOWN, mouse.pos[0], mouse.pos[1])

                if self.isPlaying:
                    self.pauseVid()
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

                if self.wasPlaying == True:
                    self.playVid()
        elif e.button() == Qt.MouseButton.RightButton:
            if clicked == self.graphWidget:
                mouse.draggingIn = None
                self.graphWidget.mClick(GLUT_RIGHT_BUTTON, GLUT_UP, mouse.pos[0], mouse.pos[1])

                if self.wasPlaying == True:
                    self.playVid()
    def mouseMoveEvent(self, e):
        #print(e)
        mouse.pos = [e.x(), e.y()]
        if self.childAt(mouse.pos[0], mouse.pos[1]) == self.graphWidget:
            self.graphWidget.mDrag(mouse.pos[0], mouse.pos[1])

    def keyPressEvent(self, e):
        pass
        """
        if e.key() == Qt.Key_Escape:
            self.parent().close()
        else:
            self.graphWidget.kPress(e.key())"""

class glWidget(QGLWidget):

    def __init__(self):
        QGLWidget.__init__(self, None)
        self.setMinimumSize(640, 480)
        self.makeCurrent()
        self.initted = False
        self.initializeGL()
        self.solution = None

    def setSolution(self, solution):
        self.solution = solution

    def paintGL(self):
        global drawables
        global window
        window.status.showMessage("drawing")

        global viewTime
        global selectedSolution

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

                """
                #for demo purpose (of prediction error):
                if not selectedSolution == None:

                    traj0 = trajectory(vis.planets['SUN'].body, selectedSolution.launch, vis.planets[i].body.state(selectedSolution.launch))
                    T = (viewTime - selectedSolution.launch).total_seconds()
                    drawables.append(vis.drawable(vis.probe(), traj0.relPosition(T)))"""

            #                                                      position                 upwards direction
            drawables.append(vis.drawable(vis.planets[i], vis.planets[i].body.state(viewTime)[0:3], up))

        """
        #all other trajectories
        if not selectedSolution == None:
            index = 0
            global trajColors
            for i, tr in enumerate(selectedSolution.trajectories):
                global flightPathColor
                iOrbit = vis.orbit(flightPathColor, tr.body.state(selectedSolution.entranceTimes[i])[0:3], tr.rMtrx, tr.elements['A'], tr.elements['ECC'], tr.angleIn, tr.angleOut)
                drawables.append(vis.drawable(iOrbit))
            deltaT = (viewTime - selectedSolution.launch).total_seconds()
            #print('launch at ',selectedSolution.launch,', viewing at ',viewTime)
            #print("t = ", deltaT, "s, at ", selectedSolution.getPosition(deltaT), " on orbit around ", selectedSolution.getTrajectory(deltaT).body.name)
            #print('------')"""

        #the probe itself
        if not selectedSolution == None:
            deltaT = (viewTime - selectedSolution.launch).total_seconds()
            position = selectedSolution.getPosition(deltaT)

            global probePositions
            drawables.append(vis.drawable(vis.probePath(probePathColor, probePositions)))

            drawables.append(vis.drawable(vis.probe(),pos = position))

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
    #loading.setStyleSheet('font-size: 18pt; font-family: Courier; color: rgb(255, 255, 255)')
    #loading.showMessage("picture by NASA/JPL-Caltech/Univ. of Arizona\nMars Reconnaissance Orbiter (MRO)\nid: PIA17646")

    #SPICE initializations
    global ephem
    root_dir = os.path.abspath(os.getcwd())
    ephem = ephemeris(sp, root_dir)

    global solarSystemPlaneUP
    e2001 = ephem.get_body('EARTH').state(datetime(2001,1,1))
    e2001UP = np.cross(np.array(e2001[0:3]), np.array(e2001[3:]))
    solarSystemPlaneUP = e2001UP / np.linalg.norm(e2001UP)

    #initialize main window
    global window
    window = MainWindow()
    
    app.setWindowIcon(QIcon('logo.ico'))
    window.setWindowIcon(QIcon('logo.ico'))

    window.show()
    #splash.close()
    loading.finish(window)

    app.exec_()
