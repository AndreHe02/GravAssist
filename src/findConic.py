from __future__ import print_function
import os

#spiceypy
from SPICE.ephemeris import ephemeris
import spiceypy as sp

#math and data types
import cmath
import math
import time
import numpy as np
from scipy.integrate import quad
from datetime import datetime, timedelta

#for graphing
#https://jakevdp.github.io/PythonDataScienceHandbook/04.02-simple-scatter-plots.html
import matplotlib.pyplot as plt
plt.style.use('seaborn')

#fellow classes
from body import body

#raise error when having invalid values
np.seterr('raise')

#print or not
allowed = False

#standard operations to use

def printD(*arg):
    if allowed:
        print(arg)

def findAngle(vec, base = []):
    if not len(base):
        return np.arctan2(vec[1],vec[0])
    else:
        vTemp = rotateBy(vec, -1 * findAngle(base))
        return findAngle(vTemp)

def rotateBy(vec, ang):
    #apply rotational matrix to rotate -1 * base
    return np.array([vec[0]*np.cos(ang)-vec[1]*np.sin(ang), vec[0]*np.sin(ang)+vec[1]*np.cos(ang)])

def mag(vec):
    return math.sqrt(np.sum([n**2 for n in vec]))

#the trajectory class
class trajectory:

    def __init__(self, body, time, state):
        self.body = body
        self.time = time
        self.state = state
        self.soi = body.soi(time)
        printD("a new 'trajectory' is created with state: ",state,"\n")

        self.r = np.array([state[0],state[1]])
        self.v = np.array([state[2],state[3]])
        #position vector, velocity vector
        r, v = self.r, self.v
        #distance, speed
        dist, spd = mag(r), mag(v)
        #gm
        GM = body.Gmass[0]
        #total energy of system
        self.E_sp = 1 / 2 * (dist ** 2) - GM / spd

        printD(r,v,dist,spd,GM,self.E_sp,"\n")

        #eccentricity vector (Basyal, 2.73)
        self.e = 1 / GM * ((spd ** 2 - GM / dist) * r - np.dot(r, v)*v)
        printD(self.e)
        #determine shape based on eccentricity
        if mag(self.e) >= 1:
            self.hySetup()
        else:
            self.elSetup()

    #calculate additional trajectory parameters for a hyperbola
    def hySetup(self):
        #position vector, velocity vector
        r = self.r
        v = self.v
        printD("r: ", r, " v:", v)
        #distance, speed
        dist, spd = mag(r), mag(v)
        #angle from the horizontal to the eccentricity vector
        eAngle = findAngle(self.e)
        printD("e Angle:", eAngle)
        eMag = mag(self.e)
        printD("eMag", eMag)
        #GM
        GM = self.body.Gmass[0]

        #vis viva for semi major axis
        self.a = -1 * abs (1 / (2 / dist - spd**2 / GM))
        printD("semi-major: ", self.a)
        #focal distance = rp + semi major axis, take negative value
        self.f = -1 * (abs(self.a * (1 - eMag)) + abs(self.a))
        printD("focal distance:", self.f)

        rR, vR = rotateBy(r, -1 * eAngle), rotateBy(v, -1 * eAngle)
        #zenith angle, which the flight path angle is complement to
        #zenith is always positive, fpa might be either pos, neg, or 0
        zenith = abs(findAngle(vR,rR))
        printD("zenith: ", zenith)
        fpa = np.pi / 2 - zenith
        #if fpa is 0, then determine the direction of v directly, relative to the focal vector
        if fpa == 0:
            fpa = np.cross(np.array([vR[0],vR[1],0]),np.array([self.e[0],self.e[1]]))[2]

        #true anomaly, sign is corrected to the sign of the rRy
        iAnom = np.arccos((self.a * (1 - eMag**2) - dist)/ eMag / dist) * np.sign(rR[1])
        printD("iAnom: ", iAnom)

        #rotational direction, true is anti-clockwise -> this prepares the sign of the
        #exit state: abs(exit anomaly) >= abs(entrance anomaly)
        #therefore there won't be ambiguity for the case where both signs
        #of the exit anomaly are reachable by a single path from the entrance anomaly
        #, which implies that abs(exit anomaly) < abs(entrance anomaly)

        #the direction is calculated with the z value of the
        #specific angular momentum
        #the sign of the exit anomaly should be the same with hz
        self.direction = np.cross([rR[0],rR[1],0], [vR[0],vR[1],0])[2]
        self.direction = np.sign(self.direction)
        printD("counterClockwise: ", self.direction)

        #calculate the exit state
        #first: the exit speed by total specific orbital energy
        vInf = math.sqrt(self.E_sp * 2)

        #second: get the rf vector relative to the focal axis
        #calculate un-signed exit anomaly with distance = soi(see Basyal 2.29)
        fAnom = abs(np.arccos((self.a * (1 - eMag**2) - self.soi)/ eMag / self.soi))
        printD('soi: ',self.soi)
        #angle correction
        fAnom *= self.direction

        rfR = np.array([self.soi*np.cos(fAnom), self.soi*np.sin(fAnom)])

        #third: complete the vf vector relative to the focal axis
        #assume that v is in the same direction with rfR
        vfR = np.array([vInf*np.cos(fAnom), vInf*np.sin(fAnom)])

        printD("fAnom: ", fAnom)
        printD("rR, rfR: ", rR, rfR)
        printD("vR, vfR: ", vR, vfR)

        self.entranceState = [rR,vR, iAnom]
        self.exitState = [rfR,vfR, fAnom]

    #calculate additional trajectory parameters for an ellipse
    def elSetup(self):
        #position vector, velocity vector
        r = self.r
        v = self.v
        #distance, speed
        dist, spd = mag(r), mag(v)
        #angle from the horizontal to the eccentricity vector
        eAngle = findAngle(self.e)
        eMag = mag(self.e)
        #GM
        GM = self.body.Gmass[0]

        #vis viva for semi major axis
        self.a = 1 / (2 / dist - spd**2 / GM)


    def plot(self, poly=20):
        correction = findAngle(self.e)
        printD("correction: ", correction)

        #for a cyclic trajectory
        if mag(self.e) < 1:
            lo = -1*np.pi
            hi = np.pi
            printD("is cyclic")
        #for a non-cyclic trajectory
        else:
            lo = self.entranceState[2]
            hi = self.exitState[2]
            printD("is not cyclic")

        x = []
        y = []
        step = []

        printD("iAnom,fAnom: ",lo,hi)
        printD("semi-major: ", self.a, "\n eccentricity:", mag(self.e))

        #temp denotes true anomaly
        for temp in range(poly):
            ang = lo + (hi-lo)/(poly-1)*temp
            #calculation of dist (see Basyal 2.26)
            dist = abs(self.a * (1 - mag(self.e)**2) / (1 + mag(self.e) * np.cos(ang)))
            r = rotateBy(np.array([dist*np.cos(ang),dist*np.sin(ang)]), correction)
            #r = rotateBy(np.array([dist*np.cos(ang),dist*np.sin(ang)]), 0)
            #printD(ang)
            #printD(r,dist,"\n")
            printD(r[0],r[1])
            x.append(r[0])
            y.append(r[1])
            step.append(ang)


        soi = self.soi
        tra = plt.axes()

        if mag(self.e) < 1:
            tra.scatter(x, y, marker = 'x', c = 'blue')
        else:
            tra.scatter(x, y, marker = 'x', c = 'green')
        #soi range
        circle = plt.Circle((0, 0), soi, color='red', fill=False)
        tra.add_artist(circle)
        #be in color
        plt.jet()
        #SoI size
        tra.set_xlim(-1.25*soi,1.25*soi)
        tra.set_ylim(-1.25*soi,1.25*soi)
        #set x-y ratio to be equal, to look more realistic
        tra.set_aspect('equal')

        for i, txt in enumerate(step):
            tra.annotate(("f=%.2f" % txt), (x[i]+1000, y[i]))
        plt.show()

    def getTime (self):

        e = mag(self.e)
        a = self.a
        if e < 1:
            printD("in cycle for ever")
            return

        rStart, vStart, aStart = self.entranceState
        rExit, vExit, aExit = self.exitState

        printD("rStart, rExit: ", rStart, rExit)
        printD("semiMajor:", a)
        # find total area sweeped by the object inside the sphere of influence
        # A(r) = [integrate from periapsis to r: sqrt(x^2-a^2)dx] * sqrt(e^2-1) + .5*sign(rx)*rx*ry
        # quad (formula, lower bound, upper bound)
        printD("focal coordinate", self.f)
        xP = a # coordinate of periapsis if origin is set at intercept of asymptotes
        X = lambda r: self.f + r[0] # horizontal coordinate of a vector if origin is set at intercept of asymptotes
        printD("xP: ", xP, "xrStart:", X(rStart))
        #evaluate area
        A = lambda r: quad(lambda x: math.sqrt(x**2-a**2), X(r), xP)[0] * math.sqrt(e**2 - 1) + .5 * np.sign(r[0])*abs(r[0]*r[1])
        #add or minus the areas for the entrance and exit vectors
        if np.sign(rStart[1]) == np.sign(rExit[1]):
            area = A(rExit) - A(rStart)
        else:
            area = A(rExit) + A(rStart)

        # dA/dt = r * v / 2
        arealVelocity = mag(rStart) * mag(vStart) / 2
        printD("areaV is ", arealVelocity)

        return area / arealVelocity

if __name__ == '__main__':
    E = ephemeris(sp, '/Users/labohem/Desktop/school/independent study/GravAssist')
    earth = E.get_body('EARTH')

    #constructs a conic section trajectory based on the given initial state
    #traj.a = semi major axis
    #traj.e = eccentricity vector, pointing from the foci to the center, with magnitude = eccentricity

    traj = trajectory(earth, datetime(2001,10,15),[200000,70000,-.5,-6])
    traj.plot()
    print("time in soi is ",traj.getTime())
