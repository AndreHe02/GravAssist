from __future__ import print_function
import os

#spiceypy
from src.SPICE.ephemeris import ephemeris
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
from src.body import body

#raise error when having invalid values
np.seterr('raise')

#standard operations to use

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

def convert(dateObj):
    return sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())

def squish(coord, mtrx):
    #print ("mtrx:", mtrx)
    return np.matmul(mtrx, coord)[0:2]

def unSquish(coord, mtrx):
    invMtrx = np.linalg.inv(mtrx)
    #print(invMtrx)
    return np.matmul(invMtrx, np.append(coord, [0]))

class trajectory:

    #
    #state is relative to the sun
    #
    def __init__(self,body,time,state):

        self.body = body
        self.entranceState = state

        self.GM = body.Gmass[0]

        #output vars explanation
        #https://ssd.jpl.nasa.gov/?sb_elem
        #function documentation
        #https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/oscltx_c.html

        self.elements = sp.oscltx(state, convert(time), self.GM)
        self.elements = {
            "RP": self.elements[0], #Perifocal distance.
            "ECC": self.elements[1], #Eccentricity.
            "INC": self.elements[2], #Inclination.
            "LNODE": self.elements[3], #Longitude of the ascending node.
            "ARGP": self.elements[4], #Argument of periapsis.
            "M0": self.elements[5], #Mean anomaly at epoch.
            "T0": self.elements[6], #Epoch.
            "GM": self.elements[7], #Gravitational parameter.
            "NU": self.elements[8], #True anomaly at epoch.
            "A": self.elements[9] #Semi-major axis. A is set to zero if it is not computable.
        }
        #print(self.elements)

        r = np.array(state[:3])
        v = np.array(state[3:6])
        #https://space.stackexchange.com/questions/22000/simulate-celestial-body-motion-on-hyperbolic-trajectory-2d
        h = np.cross(r, v)
        e = np.cross(v, h) / self.GM - r / mag(r)

        #eccentricity direction as i
        i = e / np.linalg.norm(e)
        self.eccVec = i
        #rotational momentum direction as k
        k = h / np.linalg.norm(h)
        self. up = k
        #figure out j from the first 2 vectors
        j = np.cross(k, i)

        self.rMtrx = np.array([i, j, k])

        #print("ijk:", i, j, k)
        #transform 3d coordinate to 2d coordinate
        rR = squish(r, self.rMtrx)
        vR = squish(v, self.rMtrx)

        self.angleIn = None
        self.angleOut = None


        # dA/dt = r * v / 2
        arealVelocity = mag(rR) * mag(vR) / 2
        self.av = arealVelocity

        if(self.elements['ECC']<=1):
            return

        #print("results:", rR, vR)

        #
        #find total area sweeped by the object inside the sphere of influence
        #
        #focal distance = rp + semi major axis, take negative value
        foc = -1 * (abs(self.elements["RP"]) + abs(self.elements["A"]))
        A = self.elements['A']
        RP = self.elements['RP']
        E = self.elements['ECC']
        #x coordinate, when setting the actual origin instead
        #of the focus as the origin
        X = lambda x: foc + x
        # scipy integration -- quad (formula, lower bound, upper bound)
        Area = lambda r: 2 * abs (quad(lambda x: math.sqrt(x**2-A**2), X(r[0]), X(RP))[0] * math.sqrt(E**2 - 1) + .5 * np.sign(r[0])*abs(r[0]*r[1]) )
        #print(Area(rR))

        self.deltaT = Area(rR)/ arealVelocity
        """
        #exit state using symmetry
        vfR = np.array([vR[0]*-1, vR[1]])
        rfR = np.array([rR[0], rR[1]*-1])

        #convert back to 3d J2000 rather than 2d orbital-plane coords
        self.vf = unSquish(vfR, self.rMtrx)
        self.rf = unSquish(rfR, self.rMtrx)
        """

        #exit state using deltaT
        self.exitState = sp.prop2b(self.GM, state, self.deltaT)

        #print("deltaT: ", self.deltaT, "\nvf:", self.vf, "\nrf: ", self.rf)

        if E >= 1:
            self.angleIn = angleFromR(r, self)
            self.angleOut = angleFromR(self.exitState[0:3], self)

def angleFromR(r, trajectory):
    rR = squish(r, trajectory.mtrx)
    return np.arctan2(rR[1], rR[0])

def swingby(pivot, time, state):

    #convert to relative position to the planet, but still in the xyz frame
    state = state - pivot.state(time)

    #get trajectory, here traj.rf and traj.vf are relative to the planet
    traj = trajectory (pivot, time, state)
    deltaT = timedelta(seconds = traj.deltaT)

    fState = traj.exitState
    #print(fState)
    fState = np.array(pivot.state(time + deltaT)) + fState
    #print(fState)

    return fState, traj.deltaT

def wait(pivot, state, deltaT):
    GM = pivot.Gmass[0]
    return sp.prop2b(GM, state, deltaT)

if __name__ == '__main__':
    E = ephemeris(sp, '/Users/labohem/Desktop/school/independent study/GravAssist')
    earth = E.get_body('EARTH')
    mars = E.get_body('MARS')
    jupiter = E.get_body('JUPITER')

    d = datetime(2000,1,1)
    #print(earth.state(d))
    tI = time.time()
    #for i in range(1000):
    print(swingby(earth, d, [200000,70000,50000,-.5,-6,0]+earth.state(d)))
    #tF = time.time()
    #print("used time: ", tI-tF)
