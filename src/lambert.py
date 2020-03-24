import numpy as np
from numpy.linalg import norm as norm
from numpy import array as arr
from datetime import timedelta

def lambert_transfer(p1, p2, t0, T, GM):
    #vectors/variables followed by R, H, E are:
    #R - in dimension reduced 2D vector space
    #H - in vector space defined by hyperbola axes
    #E - in vector space defined by ellipse axes
    
    #keep p1 as shorter leg
    mirrored = norm(p2) < norm(p1)
    if mirrored:
        temp = p1
        p1 = p2
        p2 = temp
    
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
    
    def transfer_paths(lH):
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
        TE = timedelta(seconds=((4 * np.pi**2 * aE**3 / GM) ** 0.5)[0])

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
        th = np.arccos(np.sum(r1E * r2E) / norm(r1E) / norm(r2E))
        if th > np.pi: th = np.pi - th
        dt = th / (2*np.pi) * TE
        
        #compute initial and final velocities
        if mirrored: rhref = np.cross(r2E, r1E)
        else: rhref = np.cross(r1E, r2E)
        v1E = np.cross(rhref, r1E)
        v2E = np.cross(rhref, r2E)
        v1R = np.matmul(E2R, v1E)
        v2R = np.matmul(E2R, v2E)
        v1 = Rinv(v1R)
        v2 = Rinv(v2R)
        s1 = np.sqrt(GM * (2 / norm(p1) - 1/aE))
        s2 = np.sqrt(GM * (2 / norm(p2) - 1/aE))
        v1 = v1 / norm(v1) * s1
        v2 = v2 / norm(v2) * s2

        #short path and long path
        return [{'dt':dt, 'aE':aE, 'bE':bE, 'f2':Rinv(f2R), 'v1':v1, 'v2':v2, 'Rinv':Rinv},
                {'dt':TE-dt, 'aE':aE, 'bE':bE, 'f2':Rinv(f2R), 'v1':-v1, 'v2':-v2, 'Rinv':Rinv}]

    #find the lH value that yields a transfer path
    #satisfying the time constraint T
    def fit_time_constraint(tsf_func, lH_range):
        
        def ternary_search(f, left, right, absolute_precision):
            if abs(right - left) < absolute_precision:
                return (left + right) / 2
            left_third = (2*left + right) / 3
            right_third = (left + 2*right) / 3
            if f(left_third) > f(right_third):
                return ternary_search(f, left_third, right, absolute_precision)
            else:
                return ternary_search(f, left, right_third, absolute_precision)

        def binary_search(f, lo, hi, target, incr=True, precision=1):
            if hi-lo < 1e-2 * lH_range: return None #no interval, stop search
            mid = (lo + hi) / 2
            while abs(hi - lo) > precision:
                if (f(mid) <= target):
                    if incr: lo = mid
                    else: hi = mid
                else:
                    if incr: hi = mid
                    else: lo = mid
                mid = (lo + hi) / 2
            if abs(f(mid) - target) > timedelta(days=1): return None
            return mid

        tsf_time = lambda lH: tsf_func(lH)['dt']
        left_min = ternary_search(tsf_time, -lH_range, 0, 10)
        right_min = ternary_search(tsf_time, 0, lH_range, 10)
        valid_lHs = [binary_search(tsf_time, -lH_range, left_min, T, incr=False),
            binary_search(tsf_time, left_min, 0, T, incr=True),
            binary_search(tsf_time, 0, right_min, T, incr=False),
            binary_search(tsf_time, right_min, lH_range, T, incr=True)]
        
        return [tsf_func(lH) for lH in valid_lHs if lH]
        
    search_range= 1e9
    short_solutions = fit_time_constraint(lambda lH: transfer_paths(lH)[0], search_range)
    long_solutions = fit_time_constraint(lambda lH: transfer_paths(lH)[1], search_range)
    return short_solutions + long_solutions