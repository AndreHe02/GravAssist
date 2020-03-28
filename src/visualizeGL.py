from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import time

from PIL import Image as Image
import sys

IS_PERSPECTIVE = True                               # 透视投影
VIEW = np.array([-0.8, 0.8, -0.8, 0.8, 1.0, 100.0])  # 视景体的left/right/bottom/top/near/far六个面
SCALE_K = np.array([1.0, 1.0, 1.0])                 # 模型缩放比例
EYE = np.array([0.0, 0.0, 10.0])                     # 眼睛的位置（默认z轴的正方向）
LOOK_AT = np.array([0.0, 0.0, 0.0])                 # 瞄准方向的参考点（默认在坐标原点）
EYE_UP = np.array([0.0, 1.0, 0.0])                  # 定义对观察者而言的上方（默认y轴的正方向）
WIN_W, WIN_H = 640, 480                             # 保存窗口宽度和高度的变量
LEFT_IS_DOWNED = False                              # 鼠标左键被按下
RIGHT_IS_DOWNED = False                             # 鼠标右键被按下
MOUSE_X, MOUSE_Y = 0, 0                             # 考察鼠标位移量时保存的起始位置

def readTex(filename):
    t = time.time()
    img = Image.open(filename)

    img_data = np.asarray(img)

    #print("reading ",filename," takes: ",(time.time()-t)/1000)

    textID = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textID)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_ADD)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)

    #print("concluding",filename," takes: ",(time.time()-t)/1000)
    return textID

# 材质类
class material(object):

    def __init__(self, emission, specular, diffuse, shininess, slices):
        super(material, self).__init__()
        self.emission = emission
        self.specular = specular
        self.diffuse = diffuse
        self.shininess = shininess
        self.slices = slices

    def setMat(self, x):
        if self.emission == 0:
            glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0,0,0,1])
        else:
            glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, np.concatenate([np.array(x)*self.emission,[1]]))
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, np.concatenate([np.array(x)*self.diffuse,[1]]))
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, np.concatenate([np.array(x)*self.diffuse,[0]]))
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, np.concatenate([np.array([1,1,1])*self.specular,[1]]))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.shininess)

        glColor3f(0,0,0)
        #glColor3f(x[0], x[1], x[2])

        if self.diffuse==0:
            glColor3f(x[0], x[1], x[2])
    #glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, )

class drawable(object):
    def __init__(self, obj, pos, up = None):
        super(drawable, self).__init__()
        self.obj = obj
        self.pos = pos
        self.up = up

    def draw(self):
        self.obj.draw(self.pos, self.up)


class drawableType(object):

    def __init__(self):
        super(drawableType, self).__init__()

class celes(drawableType):
    """docstring for celes."""

    def __init__(self, name, emit, mat, tex, r, rings):
        super(celes, self).__init__()
        self.name = name
        self.emit = emit
        self.mat = mat
        self.tex = tex
        self.r = r
        self.rings = rings

    def draw(self, pos, up):
        glEnable(GL_TEXTURE_2D)
        qobj = gluNewQuadric()
        gluQuadricTexture(qobj, GL_TRUE)

        glPushMatrix()

        glTranslate(pos[0], pos[1], pos[2])
        rotateTo([0,0,1], up)

        glBindTexture(GL_TEXTURE_2D, self.tex)
        sphere(qobj, self.r, self.emit, self.mat)
        gluDeleteQuadric(qobj)

        for i in self.rings:
            hollowDisk (i.r * self.r, i.R * self.r, self.emit, self.mat)
        glPopMatrix()

class orbit(drawableType):

    def __init__(self, color, foc, ecc, a, angleIn=0, angleOut=0):
        super(orbit, self).__init__()
        self.color = color
        self.foc = foc
        self.ecc = ecc
        self.a = a
        self.angleIn = angleIn
        self.angleOut = angleOut

    def draw(pos):
        pass

class arrow(drawableType):
    def __init__(self, color, vec):
        super(orbit, self).__init__()
        self.color = color
        self.vec = vec

    def draw(pos):
        pass

class ring(object):
    def __init__(self, r, R):
        self.r = r
        self.R = R

def getposture():
    global EYE, LOOK_AT

    dist = np.sqrt(np.power((EYE-LOOK_AT), 2).sum())
    if dist > 0:
        phi = np.arcsin((EYE[1]-LOOK_AT[1])/dist)
        theta = np.arcsin((EYE[0]-LOOK_AT[0])/(dist*np.cos(phi)))
    else:
        phi = 0.0
        theta = 0.0

    return dist, phi, theta

DIST, PHI, THETA = getposture()                     # 眼睛与观察目标之间的距离、仰角、方位角

def init(w=640, h=480):
    global WIN_W, WIN_H
    WIN_W, WIN_H = w, h

    global quad

    glClearColor(0.0,0.0,0.0,0.0); # 设置画布背景色。注意：这里必须是4个参数
    glEnable(GL_DEPTH_TEST)          # 开启深度测试，实现遮挡关系
    glDepthFunc(GL_LEQUAL)           # 设置深度测试函数（GL_LEQUAL只是选项之一
    quad = gluNewQuadric()

    # 设置灯光
    glEnable ( GL_COLOR_MATERIAL )
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    light_ambient = [.001,.001,.001,1]
    #light_diffuse = [0.98, 0.83, 0.25, 1]
    #glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_POSITION, [0,1,0,0])

    glShadeModel(GL_SMOOTH)

    # 设置素材
    glEnable(GL_TEXTURE_2D)

    global materials, textures

    materials = {"graphElement":material(1, 0, 0, 0, 20),
        "star":material(.08, .8, 0, 120, 30),
        "rock":material(0, 1, .2, 5, 20),
        "gas":material(.005, .3, .2, 0, 30)}

    textures = {"sun": readTex('assets/sun-min.jpg'),
        "mercury":readTex('assets/mercury-min.jpg'),
        "venus":readTex('assets/venus-min.jpg'),
        "earth":readTex('assets/earth-min.jpg'),
        "mars":readTex('assets/mars-min.jpg'),
        "jupiter":readTex('assets/jupiter-min.jpg'),
        "saturn":readTex('assets/saturn-min.jpg'),
        "neptune":readTex('assets/neptune-min.jpg'),
        "uranus":readTex('assets/uranus-min.jpg')}

    global planets

    planets = {
        "SUN": celes(
            "Sun", [0.996, .434, 0], materials['star'], textures['sun'], 1.5, []
            ),
        "MERCURY": celes(
            "Mercury", [0, 0, 0], materials['rock'], textures['mercury'], .4, []
            ),
        "VENUS": celes(
            "Venus", [0,0,0], materials['rock'], textures['venus'], .45, []
            ),
        "EARTH": celes(
            "Earth", [0,0,0], materials['rock'], textures['earth'], .5, []
            ),
        "MARS": celes(
            "Mars", [0,0,0], materials['rock'], textures['mars'], .5, []
            ),
        "JUPITER": celes(
            "Jupiter", [.727, .641, .551], materials['gas'], textures['jupiter'], .85, []
            ),
        "SATURN": celes(
            "Saturn", [1, .914, .797], materials['gas'], textures['saturn'], .75, [ring(1.5, 2), ring(2.1, 2.3)]
            ),
        "URANUS": celes(
            "Uranus", [.616, .820, .847], materials['gas'], textures['uranus'], .6, [ring(2.1, 2.3)]
            ),
        "NEPTUNE": celes(
            "Neptune", [.208, .329, .690], materials['gas'], textures['neptune'], .6, [ring(1.8, 2.2)]
            ),}

    print('initted')
    print(textures)

def rotateTo (fr, to):
    axis = np.cross(fr, to)
    ang = np.arccos(np.dot(fr, to) / (np.linalg.norm(fr) * np.linalg.norm(to)))
    print("rotate by", ang, "around", axis)
    glRotatef(-1 * np.degrees(ang), axis[0], axis[1], axis[2])

def hollowDisk(r, R,color, mat, slice=20):
    mat.setMat(color)
    rot = 0
    deltaRot = 2 * np.pi / slice
    glBegin(GL_TRIANGLE_STRIP)
    for i in range (slice+1):
        glVertex3f(r * np.cos(rot), r * np.sin(rot), 0)
        glVertex3f(R * np.cos(rot+.5*deltaRot), R * np.sin(rot+.5*deltaRot), 0)
        rot += deltaRot
    glEnd()

def draw(drawables = []):

    global IS_PERSPECTIVE, VIEW
    global EYE, LOOK_AT, EYE_UP
    global SCALE_K
    global WIN_W, WIN_H

    global quad

    global materials, textures

    # 清除屏幕及深度缓存
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 设置投影（透视投影）
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    if WIN_W > WIN_H:
        if IS_PERSPECTIVE:
            glFrustum(VIEW[0]*WIN_W/WIN_H, VIEW[1]*WIN_W/WIN_H, VIEW[2], VIEW[3], VIEW[4], VIEW[5])
        else:
            glOrtho(VIEW[0]*WIN_W/WIN_H, VIEW[1]*WIN_W/WIN_H, VIEW[2], VIEW[3], VIEW[4], VIEW[5])
    else:
        if IS_PERSPECTIVE:
            glFrustum(VIEW[0], VIEW[1], VIEW[2]*WIN_H/WIN_W, VIEW[3]*WIN_H/WIN_W, VIEW[4], VIEW[5])
        else:
            glOrtho(VIEW[0], VIEW[1], VIEW[2]*WIN_H/WIN_W, VIEW[3]*WIN_H/WIN_W, VIEW[4], VIEW[5])

    # 设置模型视图
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # 几何变换
    glScale(SCALE_K[0], SCALE_K[1], SCALE_K[2])

    # 设置视点
    gluLookAt(
        EYE[0], EYE[1], EYE[2],
        LOOK_AT[0], LOOK_AT[1], LOOK_AT[2],
        EYE_UP[0], EYE_UP[1], EYE_UP[2]
    )

    # 设置视口
    glViewport(0, 0, WIN_W, WIN_H)

    glDisable(GL_TEXTURE_2D)
    glBegin(GL_LINES)
    # 以红色绘制x轴
    materials["graphElement"].setMat([1,0,0])       # 设置当前颜色为红色不透明
    glVertex3f(-0.8, 0.0, 0.0)                      # 设置x轴顶点（x轴负方向）
    glVertex3f(0.8, 0.0, 0.0)                       # 设置x轴顶点（x轴正方向）

    # 以绿色绘制y轴
    materials["graphElement"].setMat([0,1,0])       # 设置当前颜色为绿色不透明
    glVertex3f(0.0, -0.8, 0.0)                      # 设置y轴顶点（y轴负方向）
    glVertex3f(0.0, 0.8, 0.0)                       # 设置y轴顶点（y轴正方向）

    # 以蓝色绘制z轴
    materials["graphElement"].setMat([0,0,1])       # 设置当前颜色为蓝色不透明
    glVertex3f(0.0, 0.0, -0.8)                      # 设置z轴顶点（z轴负方向）
    glVertex3f(0.0, 0.0, 0.8)                       # 设置z轴顶点（z轴正方向）

    glEnd()                              # 结束绘制线段

    # 绘制
    for i in drawables:
        i.draw()

    glDisable(GL_TEXTURE_2D)

    # ---------------------------------------------------------------
    glutSwapBuffers()                    # 切换缓冲区，以显示绘制内容

def sphere(quad, r, color, mat, pos = None):
    #glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, color)
    if pos == None:
        mat.setMat(color)
        gluSphere(quad, r, mat.slices, mat.slices)
    else:
        glPushMatrix()
        glTranslate(pos[0], pos[1], pos[2])
        mat.setMat(color)
        gluSphere(quad, r, mat.slices, mat.slices)
        glPopMatrix()

def reshape(width, height):
    global WIN_W, WIN_H

    WIN_W, WIN_H = width, height
    glutPostRedisplay()

def mouseclick(button, state, x, y):
    global SCALE_K
    global LEFT_IS_DOWNED
    global RIGHT_IS_DOWNED
    global MOUSE_X, MOUSE_Y

    MOUSE_X, MOUSE_Y = x, y
    if button == GLUT_LEFT_BUTTON:
        LEFT_IS_DOWNED = state==GLUT_DOWN
        #print("left")
    elif button == GLUT_RIGHT_BUTTON:
        RIGHT_IS_DOWNED = state==GLUT_DOWN
        #print("right")

def mousemotion(x, y):
    global LEFT_IS_DOWNED
    global EYE, EYE_UP
    global MOUSE_X, MOUSE_Y
    global DIST, PHI, THETA
    global WIN_W, WIN_H

    global SCALE_K
    global RIGHT_IS_DOWNED

    global LOOK_AT

    if RIGHT_IS_DOWNED:
        dy = y - MOUSE_Y
        lookTo = EYE - LOOK_AT
        lookRight = np.cross(-1 * lookTo, EYE_UP)
        lookTo = lookTo * (1 + .025 * np.sign(dy))
        EYE = LOOK_AT + lookTo
        DIST, PHI, THETA = getposture()

        glutPostRedisplay()

    elif LEFT_IS_DOWNED:
        dx = MOUSE_X - x
        dy = y - MOUSE_Y
        MOUSE_X, MOUSE_Y = x, y

        PHI += 2*np.pi*dy/WIN_H
        PHI %= 2*np.pi
        THETA += 2*np.pi*dx/WIN_W
        THETA %= 2*np.pi
        r = DIST*np.cos(PHI)

        EYE[1] = DIST*np.sin(PHI)
        EYE[0] = r*np.sin(THETA)
        EYE[2] = r*np.cos(THETA)

        if 0.5*np.pi < PHI < 1.5*np.pi:
            EYE_UP[1] = -1.0
        else:
            EYE_UP[1] = 1.0

        glutPostRedisplay()

def keydown(key, x, y):
    global DIST, PHI, THETA
    global EYE, LOOK_AT, EYE_UP
    global IS_PERSPECTIVE, VIEW

    lookTo = EYE - LOOK_AT
    lookRight = np.cross(-1 * lookTo, EYE_UP)
    #print("up: ", EYE_UP)
    #print("right: ", lookRight)
    #print("to: ", lookTo)

    #视景体平移
    if key in [b'W', b'A', b'S', b'D']:
        if key == b'W': # 参考点,视点向上
            shift = EYE_UP * .05
        elif key == b'A': # 参考点,视点向左
            shift = lookRight * -.05
        elif key == b'S': # 参考点，视点向下
            shift = EYE_UP * -.05
        elif key == b'D': # 参考点,视点向右
            shift = lookRight * .05

        LOOK_AT += shift
        EYE += shift

        DIST, PHI, THETA = getposture()
        glutPostRedisplay()

    #参照点按视点当前方位平移
    elif key in [b'Z', b'C', b'Q', b'E']:

        if key == b'Z': # 向上旋转
            shift = EYE_UP * .05
        elif key == b'C': # 向下旋转
            shift = EYE_UP * -.05
        elif key == b'Q': #向左旋转
            shift = lookRight * -.05
        elif key == b'E': #向右旋转
            shift = lookRight * .05

        LOOK_AT += shift

        DIST, PHI, THETA = getposture()
        glutPostRedisplay()
    elif key == b' ': # 空格键，切换投影模式
        IS_PERSPECTIVE = not IS_PERSPECTIVE
        glutPostRedisplay()

if __name__ == "__main__":

    #glut general graphics initialization
    glutInit()
    displayMode = GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH
    glutInitDisplayMode(displayMode)

    #glut general window initialization
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(300, 200)
    glutCreateWindow('test')

    init(WIN_W, WIN_H)                              # 初始化画布

    #glut window functions
    glutDisplayFunc(draw)               # 注册回调函数draw()
    glutReshapeFunc(reshape)            # 注册响应窗口改变的函数reshape()
    glutMouseFunc(mouseclick)           # 注册响应鼠标点击的函数mouseclick()
    glutMotionFunc(mousemotion)         # 注册响应鼠标拖拽的函数mousemotion()
    glutKeyboardFunc(keydown)           # 注册键盘输入的函数keydown()

    glutMainLoop()                      # 进入glut主循环
#————————————————
#版权声明：本文为CSDN博主「天元浪子」的原创文章，遵循 CC 4.0 BY-SA 版权协议，转载请附上原文出处链接及本声明。
#原文链接：https://blog.csdn.net/xufive/article/details/86565130
