from __future__ import print_function
import getDist
from planetInfo import getConst
import os
import cmath
from datetime import datetime, timedelta
#for graphing

#https://jakevdp.github.io/PythonDataScienceHandbook/04.02-simple-scatter-plots.html
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')

import numpy as np

np.seterr('raise')

#graph hyperbolic trajectory
def getExitState(target, TIME, state0):
    #os.chdir("./SPICE/")

    #constant storing the planet's basic info: [radius(km), gm, SOI radius(km)]
    plntConst = getConst(target,TIME)

    #unpack & init
    pos = complex(state0[0],state0[1])
    #posLog = []
    vel = complex(state0[2],state0[3])
    gm, soi = plntConst

    #print("r0:",pos)
    #print("v:",vel)
    #print("gm:",gm)
    #print("SoI:",soi)

    dist = abs(pos)
    #print("r:",dist)

    #see Basyal
    semiMajor = 1/(2/dist - abs(vel)**2/gm)
    specificAngMomentum = dist * abs(vel)
    specificOrbitalEnergy = abs(vel)**2/2-gm/dist
    trm = dist**2
    trm1 = abs(vel)**2
    #print("trm:", trm)
    #print("trm1:",trm1)
    eccen = np.sqrt(1 + specificOrbitalEnergy * trm * trm1 / gm ** 2)
    #eccentricity determines shape, hyperbola eccen>1
    if eccen<=1:
        return False

    #print("a:",semiMajor)
    #print("e:",eccen)

    trueAnom = np.arccos((semiMajor * (1 - eccen**2)-dist)/(eccen*dist))

    #correct quadrant of arccos for trueAnom, using the sign of flightPathAngle
    flightPathAngle = np.arctan(eccen * np.sin(trueAnom) / (1+eccen*np.cos(trueAnom)))
    if (flightPathAngle > 0 and trueAnom < 0) or (flightPathAngle < 0 and trueAnom > 0):
        trueAnom *= -1
    trueAnom -= np.pi
    #print("initAnom:",trueAnom)
    #actual angle = angle of position vector to the hofizontal axis, not the axis
    #of the hyperbola

    actualAngle = findAngle(pos.real, pos.imag)
    #print("entranceAngle:",actualAngle)

    exitAngle = actualAngle + 2 * trueAnom

    #print("exitAngle:",exitAngle)
    c = semiMajor * eccen
    centerAxisAngle = actualAngle + trueAnom
    center = cmath.rect(c, centerAxisAngle)
    #print("center position:",center)

    #magnitude of exiting velocity, calculated from the conservation of angular momentum
    exitDisplacement = specificAngMomentum / soi

    #find anomaly at the end by plugging in r = soi and then flipping the result
    exitAnom = np.arccos((semiMajor * (1 - eccen**2)-soi)/(eccen*soi))

    #correct quadrant of arccos for exitAnom, using the sign of exitFlightPathAngle
    exitFlightPathAngle = np.arctan(eccen * np.sin(exitAnom) / (1+eccen*np.cos(exitAnom)))
    if (exitFlightPathAngle > 0 and exitAnom < 0) or (exitFlightPathAngle < 0 and exitAnom > 0):
        exitAnom *= -1
    exitAnom -= np.pi
    exitAnom *= -1
    #print("exitAnom:",exitAnom)

    #calculate exit position by traversing (angularly) from r0 to rf
    #and plug in r = roi
    exitPos = cmath.rect(soi, actualAngle + trueAnom + exitAnom)
    #print("exitPos",exitPos)
    #direction of exitVel goes from center of hyperbola to exit position
    cToExitPos = exitPos - center
    #get exitVel
    exitVel = cmath.rect(exitDisplacement, cmath.polar(cToExitPos)[1])
    #print("exitVel",exitVel)

    return [exitPos.real, exitPos.imag, exitVel.real, exitVel.imag]

#target = planet to go (in string: e.g. "MARS" or "MARS BARYCENTER")
#TIME = time of entrance (in datetime obj form)
#state0 = position of entrance : [x,y,vx,vy]
#step = length of each step for the simulation (in timedelta obj form)

#assume barycenter to be center of cartesian graph (0,0)
#returns exit state [x, y, vx, vy], or false if the spacecraft never leaves SoI
#all distances are in km, all times are in s
#step is default at 3 seconds per step, or else it is visibly inaccurate
def exitSim(target, TIME, state0, step = timedelta(seconds=1)):
    #os.chdir("./SPICE/")

    #constant storing the planet's basic info: [radius(km), gm, SOI radius(km)]
    plntConst = getConst(target,TIME)

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

        #for graphing, un-comment if you want to see graph
        posLog.append(pos)

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



    #for graphing, un-comment if you want to see graph
    x = []
    y = []
    for i in posLog:
        x.append(i.real)
        y.append(i.imag)
    plt.scatter(x,y, marker='o')
    plt.show()


    return [pos.real, pos.imag, vel.real, vel.imag]



def findAngle (x, y):
    temp = np.arccos(x/np.sqrt(x**2+y**2))
    if y<0:
        temp = 2 * np.pi - temp
    return temp

if __name__ == '__main__':
    #os.chdir("./SPICE/")

    #target = planet to go
    #TIME = time of entrance
    #state0 = position of entrance : [x,y,vx,vy]

    #assume barycenter to be center of cartesian graph (0,0)
    getExitState("EARTH BARYCENTER", datetime(2001,10,15),[87000.0,-87000.0,0,-6])

    #graphHyperbola("EARTH BARYCENTER", datetime(2001,10,15),[87000.0,-87000.0,0,-6])
