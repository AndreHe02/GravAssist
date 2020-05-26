import numpy as np
from numpy.linalg import norm as norm
from numpy import array as arr
from datetime import timedelta

def ternary_search(f, lo, hi, precision):
    while abs(hi-lo)> precision:
        left_third = (2*lo + hi) / 3
        right_third = (lo + 2*hi) / 3
        if f(left_third) > f(right_third): lo, hi = left_third, hi
        else: lo, hi = lo, right_third
    return (lo+hi) / 2

def binary_search(f, lo, hi, target, up, precision):
    if abs(hi-lo) < precision: return None
    mid = (lo + hi) / 2
    while abs(hi - lo) > precision:
        if (f(mid) <= target):
            if up: lo = mid
            else: hi = mid
        else:
            if up: hi = mid
            else: lo = mid
        mid = (lo + hi) / 2
    if abs(f(mid) - target) > timedelta(days=1): return None
    return mid

def lambert_transfer(p1, p2, T, GM, prec):
    #vectors/variables followed by R, H, E are:
    #R - in dimension reduced 2D vector space
    #H - in vector space defined by hyperbola axes
    #E - in vector space defined by ellipse axes

    #keep p1 as shorter leg
    mirrored = norm(p2) < norm(p1)  
    if mirrored: p1, p2 = p2, p1
    #compute dimension reduction matrix
    i = p1 / norm(p1)
    p2n = p2 / norm(p2)
    k = np.cross(i, p2n)
    k = k / norm(k)
    j = np.cross(k, i)
    Rinv_ = np.transpose(arr([i, j, k]))
    R_ = np.linalg.inv(Rinv_)
    R = lambda v: np.matmul(R_, v)
    Rinv = lambda v: np.matmul(Rinv_, v)
    p1R = R(p1)
    p2R = R(p2)
    #compute hyperbola paremeters
    #defined according to lambert's method
    aH = abs(norm(p2R) - norm(p1R))/2
    dH = norm(p2R - p1R) / 2
    bH = np.sqrt(dH**2 - aH**2)

    def time_transfer(lH, solve=False):
        #compute f2=(x,y) with respect to hyperbola axes
        xH = aH + abs(lH)
        yH = bH * np.sqrt(xH**2/aH**2 - 1)
        iH_ = (p2R - p1R)
        iH = iH_ / norm(iH_)
        kH_ = np.cross(iH,  (p1R + p2R) / 2)
        kH = kH_ / norm(kH_)
        jH_ = np.cross(iH, kH)
        jH = jH_ / norm(jH_)
        #linear transformation from hyperbola axes
        #to reduced 2D space
        if lH >= 0: f2R = iH * xH + jH * yH + (p1R + p2R) / 2
        else: f2R = iH * xH - jH * yH + (p1R + p2R) / 2
        
        #compute elliptical orbit parameters
        aE = (norm(p1R) + norm(p1R - f2R)) / 2
        cE = norm(f2R) / 2
        bE = np.sqrt(aE**2 - cE**2)
        TE = timedelta(seconds=((4 * np.pi**2 * aE**3 / GM) ** 0.5))
        
        #compute time to transfer from p1 to p2
        #on computed elliptical orbit
        ctR = f2R / 2
        r1R = p1R - ctR
        r2R = p2R - ctR
        #linear transformation from reduced 2D
        #to vector with ellipse axes as basis
        iE = f2R / norm(f2R) * aE
        kE_ = np.cross(iE, arr([1,1,0]))
        kE = kE_ / norm(kE_)
        jE_ = np.cross(iE, kE)
        jE = jE_ / norm(jE_) * bE
        E2R = np.transpose(arr([iE, jE, kE]))
        R2E = np.linalg.inv(E2R)
        r1E = np.matmul(R2E, r1R)
        r2E = np.matmul(R2E, r2R)

        #calculate time by Keplar's area law
        th = np.arccos(min(1, max(-1, np.sum(r1E * r2E) / norm(r1E) / norm(r2E))))
        if th > np.pi: th = np.pi - th
        AreaE = aE * bE * np.pi
        ActR = th / (2*np.pi) * AreaE
        tctR = norm(np.cross(r1R, r2R))/2
        tfR = norm(np.cross(p1R, p2R))/2
        refR = r1R - r2R
        rrefR = np.cross(r1R, refR); rrefR = rrefR / norm(rrefR)
        prefR = np.cross(p1R, refR); prefR = prefR / norm(prefR)
        if norm(rrefR + prefR) > norm(rrefR): AfR = ActR - tctR + tfR
        else: AfR = ActR - tctR - tfR
        dt = AfR / AreaE * TE
        if not solve: return dt, TE-dt
        
        #compute initial and final velocities
        #get speed from energy equation
        s1 = np.sqrt(GM * (2 / norm(p1) - 1/aE))
        s2 = np.sqrt(GM * (2 / norm(p2) - 1/aE))
        if mirrored: 
            rhref = np.cross(r2E, r1E)
            r1E, r2E = r2E, r1E
            s1, s2 = s2, s1
        else: rhref = np.cross(r1E, r2E)
        v1E = np.cross(rhref, r1E)
        v2E = np.cross(rhref, r2E)
        v1R = np.matmul(E2R, v1E)
        v2R = np.matmul(E2R, v2E)
        v1 = Rinv(v1R)
        v2 = Rinv(v2R)
        v1 = v1 / norm(v1) * s1
        v2 = v2 / norm(v2) * s2
        return [{'v1':v1, 'v2':v2, 'dt':dt}, {'v1':-v1, 'v2':-v2, 'dt':TE-dt}]
        
    #fit time constraint
    def fit_time_constraint(tsf, lH_range=1e9):
        left_min = ternary_search(tsf, -lH_range, 0, prec)
        right_min = ternary_search(tsf, 0, lH_range, prec)
        valid_lHs = [binary_search(tsf, -lH_range, left_min, T, False, prec),
            binary_search(tsf, left_min, 0, T, True, prec),
            binary_search(tsf, 0, right_min, T,False, prec),
            binary_search(tsf, right_min, lH_range, T, True, prec)]
        return [lH for lH in valid_lHs if lH]
    
    TSF1 = lambda lH: time_transfer(lH)[0]
    TSF2 = lambda lH: time_transfer(lH)[1]
    short_lHs = fit_time_constraint(TSF1)
    long_lHs = fit_time_constraint(TSF2)
    short_solutions = [time_transfer(lH, solve=True)[0] for lH in short_lHs]
    long_solutions = [time_transfer(lH, solve=True)[1] for lH in long_lHs]  
    return short_solutions + long_solutions