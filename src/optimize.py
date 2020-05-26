import random
import numpy as np

#walk steepest path down to local minima
def greedy_descent(f, ranges, steps, tolerance=10):
    #random initialization
    p = [lo + (hi-lo) * random.random() for lo, hi in ranges]
    min_f_yet = f(*p)
    k = len(ranges)
    flat = 0
    while flat < tolerance:
        min_f, next_p = None, None       
        for idx in range(pow(3, k)):
            new_p = p[:]
            for j in range(k):
                sign, idx = idx % 3, idx // 3
                new_p[j] += (sign-1) * steps[j]
                new_p[j] = max(ranges[j][0], min(ranges[j][1], new_p[j]))
            val_f = f(*new_p)
            if (min_f == None) or val_f < min_f: min_f, next_p = val_f, new_p            
        if min_f > min_f_yet: return p
        elif min_f == min_f_yet: flat += 1
        min_f_yet, p = min_f, next_p
    return p

#descent in decaying step sizes,
#giving increasingly accurate result
def greedy_minimize(f, ranges, steps, iters=1, decay_factor=5, tolerance=10):
    ranges = np.array(ranges)
    steps = np.array(steps)
    p = greedy_descent(f, ranges, steps)
    for _ in range(iters):
        upper = p + (ranges[:, 1] - ranges[:, 0]) / decay_factor
        lower = p - (ranges[:, 1] - ranges[:, 0]) / decay_factor
        ranges = np.array([x for x in zip(lower, upper)])
        steps = steps / decay_factor
        p = greedy_descent(f, ranges, steps, tolerance)
    return p