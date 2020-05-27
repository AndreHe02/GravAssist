import numpy as np
import spiceypy as sp

def entrance(Rsoi, ve, th1, th2):
    u = -ve / np.linalg.norm(ve)
    Mr1 = np.array([[np.cos(th1), 0, np.sin(th1)], [0, 1, 0], [-np.sin(th1), 0, np.cos(th1)]])
    p0 = np.matmul(Mr1, u) * Rsoi
    W = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    Mr2 = np.eye(3) + np.sin(th2) * W + 2*(np.sin(th2/2)**2) * np.matmul(W, W)
    p0 = np.matmul(Mr2, p0)
    return p0

def swingby(Rsoi, s0, GM, step=1e4):
    sf = s0[:]
    while np.linalg.norm(sf[:3]) / Rsoi < 1.001:  #need a failsafe
        sf = sp.prop2b(GM, sf, step)
    return sf
