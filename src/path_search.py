import numpy as np
from src.lambert import lambert_transfer

def eval_transfer(body1, body2, t0, T, GM):
    s1 = body1.state(t0)
    p1, v1 = s1[:3], s1[3:]
    s2 = body2.state(t0+T)
    p2, v2 = s2[:3], s2[3:]
    solutions = lambert_transfer(p1, p2, T, GM)
    minDV, optimal = None, None
    for s in solutions:
        v0, vf = s['v1'], s['v2']
        #initial impulse and final brake
        DV = np.linalg.norm(v0-v1) + np.linalg.norm(vf-v2)
        if not minDV or DV < minDV:
            minDV, optimal = DV, s
    return optimal, minDV

def opt_transfer(body1, body2, Tlo, Thi, GM, precision=10):
    minDV, optimal = None, None
    t0opt, Topt = None, None
    for t0i in range(precision):
        t0 = Tlo + (Thi - Tlo) * t0i / precision
        for Ti in range(precision):
            T =  (Thi - t0) * Ti / precision
            sol, DV = eval_transfer(body1, body2, t0, T, GM)
            if sol and (not minDV or DV < minDV):
                minDV, optimal = DV, sol
                t0opt, Topt = t0, T
    return optimal, minDV, t0opt, Topt
