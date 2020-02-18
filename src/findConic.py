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
from datetime import datetime, timedelta

#for graphing
#https://jakevdp.github.io/PythonDataScienceHandbook/04.02-simple-scatter-plots.html
import matplotlib.pyplot as plt
plt.style.use('seaborn')

#fellow classes
from body import body

#raise error when having invalid values
np.seterr('raise')

#standard operations to use
def antiClock(vec):
    return np.cross(np.array([1,0,0]),np.array([vec[0],vec[1],0]))[2] >= 0

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
        print("a new 'trajectory' is created with state: ",state,"\n")

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

        print(r,v,dist,spd,GM,self.E_sp,"\n")

        #eccentricity vector (Basyal, 2.73)
        self.e = 1 / GM * ((spd ** 2 - GM / dist) * r - np.dot(r, v)*v)
        print(self.e)
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
        #distance, speed
        dist, spd = mag(r), mag(v)
        #angle from the horizontal to the eccentricity vector
        eAngle = findAngle(self.e)
        eMag = mag(self.e)
        #GM
        GM = self.body.Gmass[0]

        #vis viva for semi major axis
        self.a = -1 * abs (1 / (2 / dist - spd**2 / GM))
        print("semi-major: ", self.a)
        #focal distance = rp + semi major axis, take negative value
        self.f = -1 * abs (self.a * (1 - self.e) + self.a)

        rR, vR = rotateBy(r, -1 * eAngle), rotateBy(v, -1 * eAngle)
        #zenith angle, which the flight path angle is complement to
        #zenith is always positive, fpa might be either pos, neg, or 0
        zenith = abs(findAngle(vR,rR))
        fpa = np.pi / 2 - zenith
        #if fpa is 0, then determine the direction of v directly, relative to the focal vector
        if fpa == 0:
            fpa = np.cross(np.array([vR[0],vR[1],0]),np.array([self.e[0],self.e[1]]))[2]

        #true anomaly, sign is corrected to the sign of the fpa (see Basyal 2.29)
        iAnom = abs(np.arccos((self.a * (1 - eMag**2) - dist)/ eMag / dist))
        iAnom *= fpa / abs(fpa)

        #rotational direction, true is anti-clockwise -> this prepares the sign of the
        #exit state: abs(exit anomaly) >= abs(entrance anomaly)
        #therefore there won't be ambiguity for the case where both signs
        #of the exit anomaly are reachable by a single path from the entrance anomaly
        #, which implies that abs(exit anomaly) < abs(entrance anomaly)

        #the direction is calculated with the z value of the
        #specific angular momentum
        #the sign of the exit anomaly should be the same with hz
        self.direction = np.cross([rR[0],rR[1],0], [vR[0],vR[1],0])[2]
        self.direction /= abs(self.direction)

        #calculate the exit state
        #first: the exit speed by total specific orbital energy
        vInf = math.sqrt(self.E_sp * 2)

        #second: get the rf vector relative to the focal axis
        #calculate un-signed exit anomaly with distance = soi(see Basyal 2.29)
        fAnom = abs(np.arccos((self.a * (1 - eMag**2) - self.soi)/ eMag / self.soi))
        print('eMag: ',eMag)
        print('soi: ',self.soi)
        print('fAnom: ',fAnom)
        #angle correction
        fAnom *= self.direction / abs(self.direction)
        rfR = np.array([self.soi*np.cos(fAnom), self.soi*np.sin(fAnom)])

        #third: complete the vf vector relative to the focal axis
        #assume that v is in the same direction with rfR
        vfR = np.array([vInf*np.cos(fAnom), vInf*np.sin(fAnom)])

        print("rfR: ",rfR)
        #convert back to normal coordinates
        vf = rotateBy(vfR, eAngle)
        rf = rotateBy(rfR, eAngle)

        print("rf: ",rf)

        self.entranceState = [rR,vR]
        self.exitState = [rfR,vfR]

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
        stepsize = .05
        #for a cyclic trajectory
        if mag(self.e) < 1:
            lo = -1*np.pi
            hi = np.pi
            print("is cyclic")
        #for a non-cyclic trajectory
        else:
            lo = findAngle(self.entranceState[0])
            hi = findAngle(self.exitState[0])
            print("is not cyclic")

        x = []
        y = []
        step = []

        print("iAnom,fAnom: ",lo,hi)
        print("semi-major: ",self.a, "\n eccentricity:", mag(self.e))

        #temp denotes true anomaly
        for temp in range(poly):
            ang = lo + (hi-lo)/(poly-1)*temp
            #calculation of dist (see Basyal 2.26)
            dist = abs(self.a * (1 - mag(self.e)**2) / (1 + mag(self.e) * np.cos(ang)))
            r = rotateBy(np.array([dist*np.cos(ang),dist*np.sin(ang)]), correction)
            print(ang)
            print(r,dist,"\n")
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

if __name__ == '__main__':
    E = ephemeris(sp, '/Users/labohem/Desktop/school/independent study/GravAssist')
    earth = E.get_body('EARTH')

    #constructs a conic section trajectory based on the given initial state
    #traj.a = semi major axis
    #traj.e = eccentricity vector, pointing from the foci to the center, with magnitude = eccentricity
    
    traj = trajectory(earth, datetime(2001,10,15),[200000,70000,0,-1.65])
    traj.plot()
