import numpy as np

#walk steepest path down to minimal gridpoint
def steep_descent(f, ranges, steps, pinit, condition):
    p = pinit
    k = len(ranges)
    visited = [p]
    fmin = f(*p)
    if not fmin: return None
    
    #descend until no lower gridpoint exists
    while True:
        fadj, pnext = None, None       
        #iterate through adjacent gridpts
        for idx in range(pow(3, k)):
            #generate new params
            pnew = p[:]
            for j in range(k):
                sign, idx = idx % 3, idx // 3
                pnew[j] += (sign-1) * steps[j]
                pnew[j] = max(ranges[j][0], min(ranges[j][1], pnew[j]))
            if pnew in visited or (condition and not condition(*pnew)): continue
            
            #if pnew valid, evaluate new parameters
            fval = f(*pnew)
            if fval:
                if not fadj or fval < fadj: 
                    fadj, pnext = fval, pnew            
            visited.append(pnew)
                    
        #return if no adjacent function value is smaller
        if fadj == None or fadj >= fmin: return p
        fmin, p = fadj, pnext
    
#descent in decaying step sizes,
#giving increasingly accurate result
def decaying_descent(f, ranges, steps, pinit, condition, iters, decay_factor):
    ranges = np.array(ranges)
    steps = np.array(steps)
    p = steep_descent(f, ranges, steps, pinit, condition)
    if p == None: return None
    
    for _ in range(1, iters):
        upper = p + steps
        lower = p - steps
        ranges = np.array([x for x in zip(lower, upper)])
        steps = steps / decay_factor
        p = steep_descent(f, ranges, steps, p, condition)
        
    return p
