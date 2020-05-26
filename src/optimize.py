import random
import numpy as np

#walk steepest path down to minimal gridpoint
def steep_descent(f, ranges, steps, tolerance, pinit, condition):
    #random initialization until valid
    if not pinit: 
        p = [lo + (hi-lo) * random.random() for lo, hi in ranges]
        c = 0
        while not condition(*p) or f(*p) == None: 
            if c > 10: return None   #failed to initialize
            else: c += 1
            p = [lo + (hi-lo) * random.random() for lo, hi in ranges]          
    else: p = pinit
    k = len(ranges)
    flat = 0
    fmin_yet = f(*p)
    visited = [p]
    #descend until no lower gridpoint exists
    while True:
        fmin, pnext = None, None       
        for idx in range(pow(3, k)):
            #generate new parameters
            pnew = p[:]
            for j in range(k):
                sign, idx = idx % 3, idx // 3
                pnew[j] += (sign-1) * steps[j]
                pnew[j] = max(ranges[j][0], min(ranges[j][1], pnew[j]))
            #evaluate new parameters
            if condition and condition(*pnew) and pnew not in visited:
                    fval = f(*pnew)
                    if fval != None and (fmin == None or fval < fmin): fmin, pnext = fval, pnew            
                    visited.append(pnew)
        #return if no adjacent function value is smaller
        if fmin == None or fmin >= fmin_yet: return p
        fmin_yet, p = fmin, pnext
    
#descent in decaying step sizes,
#giving increasingly accurate result
def decaying_descent(f, ranges, steps, condition, iters, decay_factor, tolerance, pinit):
    ranges = np.array(ranges)
    steps = np.array(steps)
    p = steep_descent(f, ranges, steps, tolerance, pinit, condition)
    if p == None: return None #failed to initialize
    for _ in range(1, iters):
        upper = p + steps
        lower = p - steps
        ranges = np.array([x for x in zip(lower, upper)])
        steps = steps / decay_factor
        p = steep_descent(f, ranges, steps, tolerance, p, condition)
    return p