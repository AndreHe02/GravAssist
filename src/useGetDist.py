from __future__ import print_function
from getDist import getDist
import os
import cmath
from datetime import datetime, timedelta
#for graphing

#https://jakevdp.github.io/PythonDataScienceHandbook/04.02-simple-scatter-plots.html
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')

import numpy as np

#target = planet to go (in string: e.g. "MARS" or "MARS BARYCENTER")
#TIME = time of entrance (in datetime obj form)
#state0 = position of entrance ： [x,y,vx,vy]
#step = length of each step for the simulation (in timedelta obj form)

#assume barycenter to be center of cartesian graph (0,0)
#returns exit state [x, y, vx, vy], or false if the spacecraft never leaves SoI
#all distances are in km, all times are in s
#step is default at 3 seconds per step, or else it is visibly inaccurate
def getExitState(target, TIME, state0, step = timedelta(seconds=3)):
    #os.chdir("./SPICE/")

    #constant storing the planet's basic info: [radius(km), gm, SOI radius(km)]
    plntConst = getDist.getConst(target,TIME)

    #unpack & init
    pos = complex(state0[0],state0[1])
    posLog = []
    vel = complex(state0[2],state0[3])
    gm, soi = plntConst

    dist = abs(pos)
    #angDisplacement = 0
    count = 0

    #construct circular orbit (for testing)
    #vel = cmath.rect((gm/dist)**(0.5), 3/4*3.1415926)

    #TODO: add crash detection?
    #simulation loop: quit if the spacecraft has went around a circle (2 pi plus a bit more)
    while dist<soi:
        '''
        #for graphing, un-comment if you want to see graph
        posLog.append(pos)
        '''
        #phase = angle of complex number, in radians
        angTemp = cmath.phase(pos)
        a = cmath.rect(-1*gm/(dist**2),angTemp)

        #print(angDisplacement," ",abs(a)," ",pos)
        pos += vel * step.seconds
        vel += a * step.seconds
        #angular displacement = linear displacement / r
        #angDisplacement += abs(vel/dist)
        #print(angDisplacement)
        dist = abs(pos)

        count+=1

        #if after a long time, the spacecraft goes back to around it's initial position,
        #then it's probably going in ellipse
        #otherwise if it

        if count > 30000:
            if count > 200000:
                return False
            if abs(pos - complex(state0[0],state0[1]))/abs(pos) < 0.1:
                return False


    '''
    #for graphing, un-comment if you want to see graph
    x = []
    y = []
    for i in posLog:
        x.append(i.real)
        y.append(i.imag)
    plt.scatter(x,y, marker='o')
    plt.show()
    '''

    return [pos.real, pos.imag, vel.real, vel.imag]

if __name__ == '__main__':
    os.chdir("./SPICE/")

    #target = planet to go
    #TIME = time of entrance
    #state0 = position of entrance ： [x,y,vx,vy]

    #assume barycenter to be center of cartesian graph (0,0)
    getExitState("EARTH BARYCENTER", datetime(2001,10,15),[7000,7000,-5 ,5])
