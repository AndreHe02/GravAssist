from src.path import path
from src.traj import trajectory
from src.swingby import *
from src.optimize import *
from datetime import datetime, timedelta

Rsoi = {'EARTH': 0.929e6, 'MERCURY':0.112e6, 'VENUS':0.616e6,
       'MARS':0.578e6, 'JUPITER':48.2e6, 'SATURN':54.5e6,
       'URANUS':51.9e6, 'NEPTUNE':86.8e6}

def voyager1_recreated(ephem):
    earth = ephem.get_body('EARTH')
    jupiter = ephem.get_body('JUPITER')
    saturn = ephem.get_body('SATURN')
    sun = ephem.get_body('SUN')
    
    def convert(dateObj): return sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
    voyst = lambda t: sp.spkezr('VOYAGER 1', convert(t), 'J2000', 'LT+S', 'SOLAR SYSTEM BARYCENTER')[0]
    
    #earth to jupiter
    D = 10 
    tfE = datetime(1977, 9, 6, 14, 54)
    t0J = datetime(1979, 1, 16, 13, 54)
    tfJ = datetime(1979, 4, 22, 11, 7)
    t0S = datetime(1980, 10, 3, 1, 32)
    tfS = datetime(1980, 12, 24, 4, 35)
    timesE2J = []
    trajE2J = []
    for i in range(D):
        tE2J = (t0J - tfE) * i / D + tfE
        state = voyst(tE2J)    
        timesE2J.append(tE2J)
        trajE2J.append(trajectory(sun, tE2J, state, tE2J + (t0J - tfE) / D))
    
    #swingby at jupiter
    st0J = voyst(t0J) - jupiter.state(t0J)
    stfJ = voyst(tfJ) - jupiter.state(tfJ)
    GMJ = jupiter.const('GM', 1)[0]

    def dVJ(th1, th2):
        enpt = entrance(Rsoi['JUPITER'], st0J[3:], th1, th2)
        exst = swingby(Rsoi['JUPITER'], np.concatenate((enpt, st0J[3:])), GMJ)
        return np.linalg.norm(stfJ[3:] - exst[3:])

    th1J, th2J = decaying_descent(dVJ, [[-np.pi, np.pi], [-np.pi, np.pi]], [0.2, 0.2], [np.pi/20, 0], None, iters=5, decay_factor=5)
    enptJ = entrance(Rsoi['JUPITER'], st0J[3:], th1J, th2J)
    sIntoJ = np.concatenate((enptJ, st0J[3:]+jupiter.state(t0J)[3:]))
    trajByJ = trajectory(jupiter, t0J, sIntoJ, tfJ)
    
    #jupiter to saturn
    timesJ2S = []
    trajJ2S = []
    for i in range(D):
        tJ2S = (t0S - tfJ) * i / D + tfJ
        state = voyst(tJ2S)    
        timesJ2S.append(tJ2S)
        trajJ2S.append(trajectory(sun, tJ2S, state, tJ2S + (t0S - tfJ) / D))
        
    #swingby at saturn
    st0S = voyst(t0S) - saturn.state(t0S)
    stfS = voyst(tfS) - saturn.state(tfS)
    GMS = saturn.const('GM', 1)[0]

    def dVS(th1, th2):
        enpt = entrance(Rsoi['SATURN'], st0S[3:], th1, th2)
        exst = swingby(Rsoi['SATURN'], np.concatenate((enpt, st0S[3:])), GMS)
        return np.linalg.norm(stfS[3:] - exst[3:])

    th1S, th2S = decaying_descent(dVS, [[-np.pi, np.pi], [-np.pi, np.pi]], [0.2, 0.2], [np.pi/20, 0], None, iters=5, decay_factor=5)
    enptS = entrance(Rsoi['SATURN'], st0S[3:], th1S, th2S)
    sIntoS = np.concatenate((enptS, st0S[3:]+saturn.state(t0S)[3:]))
    trajByS = trajectory(saturn, t0S, sIntoS, tfS)

    #after saturn
    after = timedelta(days=1500)
    trajAftS = trajectory(sun, tfS, voyst(tfS), tfS + after)
    
    entranceTimes = []
    entranceTimes.extend(timesE2J)
    entranceTimes.append(t0J)
    entranceTimes.extend(timesJ2S)
    entranceTimes.append(t0S)
    entranceTimes.append(tfS)
    trajs = []
    trajs.extend(trajE2J)
    trajs.append(trajByJ)
    trajs.extend(trajJ2S)
    trajs.append(trajByS)
    trajs.append(trajAftS)

    voyager = path(launchTime = tfE, deltaV = 'Recreated', duration = tfS - tfE + after, entranceTimes=entranceTimes, trajectories=trajs)
    return voyager

def voyager1_original(ephem):
    earth = ephem.get_body('EARTH')
    jupiter = ephem.get_body('JUPITER')
    saturn = ephem.get_body('SATURN')
    sun = ephem.get_body('SUN')
    
    def convert(dateObj): return sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
    voyst = lambda t: sp.spkezr('VOYAGER 1', convert(t), 'J2000', 'LT+S', 'SOLAR SYSTEM BARYCENTER')[0]
    
    #earth to jupiter
    D = 10 
    tfE = datetime(1977, 9, 6, 14, 54)
    t0J = datetime(1979, 1, 16, 13, 54)
    tfJ = datetime(1979, 4, 22, 11, 7)
    t0S = datetime(1980, 10, 3, 1, 32)
    tfS = datetime(1980, 12, 24, 4, 35)
    timesE2J = []
    trajE2J = []
    for i in range(D):
        tE2J = (t0J - tfE) * i / D + tfE
        state = voyst(tE2J)    
        timesE2J.append(tE2J)
        trajE2J.append(trajectory(sun, tE2J, state, tE2J + (t0J - tfE) / D))
    
    #swingby at jupiter
    trajByJ = trajectory(jupiter, t0J, voyst(t0J)-jupiter.state(t0J), tfJ)
    
    #jupiter to saturn
    timesJ2S = []
    trajJ2S = []
    for i in range(D):
        tJ2S = (t0S - tfJ) * i / D + tfJ
        state = voyst(tJ2S)    
        timesJ2S.append(tJ2S)
        trajJ2S.append(trajectory(sun, tJ2S, state, tJ2S + (t0S - tfJ) / D))
        
    #swingby at saturn
    trajByS = trajectory(saturn, t0S, voyst(t0S)-saturn.state(t0S), tfS)

    #after saturn
    after = timedelta(days=1500)
    trajAftS = trajectory(sun, tfS, voyst(tfS), tfS + after)
    
    entranceTimes = []
    entranceTimes.extend(timesE2J)
    entranceTimes.append(t0J)
    entranceTimes.extend(timesJ2S)
    entranceTimes.append(t0S)
    entranceTimes.append(tfS)
    trajs = []
    trajs.extend(trajE2J)
    trajs.append(trajByJ)
    trajs.extend(trajJ2S)
    trajs.append(trajByS)
    trajs.append(trajAftS)

    voyager = path(launchTime = tfE, deltaV = 'Original', duration = tfS - tfE + after, entranceTimes=entranceTimes, trajectories=trajs)
    return voyager

def voyager2_recreated(ephem):
    earth = ephem.get_body('EARTH')
    jupiter = ephem.get_body('JUPITER')
    saturn = ephem.get_body('SATURN')
    uranus = ephem.get_body('URANUS')
    neptune = ephem.get_body('NEPTUNE')
    sun = ephem.get_body('SUN')
    
    def convert(dateObj): return sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
    voyst2 = lambda t: sp.spkezr('VOYAGER 2', convert(t), 'J2000', 'LT+S', 'SOLAR SYSTEM BARYCENTER')[0]
    
    D = 10 
    tfE = datetime(1977, 8, 21, 16, 40)
    t0J = datetime(1979, 5, 6, 15, 33)
    tfJ = datetime(1979, 9, 12, 22, 19)
    t0S = datetime(1981, 6, 29, 17, 20)
    tfS = datetime(1981, 10, 22, 18, 26)
    t0U = datetime(1985, 12, 15, 5, 6)
    tfU = datetime(1986, 3, 6, 13, 52)
    t0N = datetime(1989, 6, 26, 12, 6)
    tfN = datetime(1989, 10, 24, 7, 6)
    
    
    timesE2J = []
    trajE2J = []
    for i in range(D):
        tE2J = (t0J - tfE) * i / D + tfE
        state = voyst2(tE2J)    
        timesE2J.append(tE2J)
        trajE2J.append(trajectory(sun, tE2J, state, tE2J + (t0J - tfE) / D))
    
    #swingby at jupiter
    st0J = voyst2(t0J) - jupiter.state(t0J)
    stfJ = voyst2(tfJ) - jupiter.state(tfJ)
    GMJ = jupiter.const('GM', 1)[0]

    def dVJ(th1, th2):
        enpt = entrance(Rsoi['JUPITER'], st0J[3:], th1, th2)
        exst = swingby(Rsoi['JUPITER'], np.concatenate((enpt, st0J[3:])), GMJ)
        return np.linalg.norm(stfJ[3:] - exst[3:])

    th1J, th2J = decaying_descent(dVJ, [[-np.pi, np.pi], [-np.pi, np.pi]], [0.2, 0.2], [np.pi/20, 0], None, iters=5, decay_factor=5)
    enptJ = entrance(Rsoi['JUPITER'], st0J[3:], th1J, th2J)
    sIntoJ = np.concatenate((enptJ, st0J[3:]))
    trajByJ = trajectory(jupiter, t0J, sIntoJ, tfJ)
    
    #jupiter to saturn
    timesJ2S = []
    trajJ2S = []
    for i in range(D):
        tJ2S = (t0S - tfJ) * i / D + tfJ
        state = voyst2(tJ2S)    
        timesJ2S.append(tJ2S)
        trajJ2S.append(trajectory(sun, tJ2S, state, tJ2S + (t0S - tfJ) / D))
        
    #swingby at saturn
    st0S = voyst2(t0S) - saturn.state(t0S)
    stfS = voyst2(tfS) - saturn.state(tfS)
    GMS = saturn.const('GM', 1)[0]

    def dVS(th1, th2):
        enpt = entrance(Rsoi['SATURN'], st0S[3:], th1, th2)
        exst = swingby(Rsoi['SATURN'], np.concatenate((enpt, st0S[3:])), GMS)
        return np.linalg.norm(stfS[3:] - exst[3:])

    th1S, th2S = decaying_descent(dVS, [[-np.pi, np.pi], [-np.pi, np.pi]], [0.2, 0.2], [np.pi/20, 0], None, iters=5, decay_factor=5)
    enptS = entrance(Rsoi['SATURN'], st0S[3:], th1S, th2S)
    sIntoS = np.concatenate((enptS, st0S[3:]))
    trajByS = trajectory(saturn, t0S, sIntoS, tfS)

    #saturn to uranus
    timesS2U = []
    trajS2U = []
    for i in range(D):
        tS2U = (t0U - tfS) * i / D + tfS
        state = voyst2(tS2U)    
        timesS2U.append(tS2U)
        trajS2U.append(trajectory(sun, tS2U, state, tS2U + (t0U - tfS) / D))
    
    #swingby at uranus
    st0U = voyst2(t0U) - uranus.state(t0U)
    stfU = voyst2(tfU) - uranus.state(tfU)
    GMU = uranus.const('GM', 1)[0]

    def dVU(th1, th2):
        enpt = entrance(Rsoi['URANUS'], st0U[3:], th1, th2)
        exst = swingby(Rsoi['URANUS'], np.concatenate((enpt, st0U[3:])), GMU)
        return np.linalg.norm(stfU[3:] - exst[3:])

    th1U, th2U = decaying_descent(dVU, [[-np.pi, np.pi], [-np.pi, np.pi]], [0.2, 0.2], [np.pi/20, 0], None, iters=5, decay_factor=5)
    enptU = entrance(Rsoi['URANUS'], st0U[3:], th1U, th2U)
    sIntoU = np.concatenate((enptU, st0U[3:]))
    trajByU = trajectory(uranus, t0U, sIntoU, tfU)
    
    #uranus to neptune
    timesU2N = []
    trajU2N = []
    for i in range(D):
        tU2N = (t0N - tfU) * i / D + tfU
        state = voyst2(tU2N)    
        timesU2N.append(tU2N)
        trajU2N.append(trajectory(sun, tU2N, state, tU2N + (t0N - tfU) / D))
    
    #swingby at neptune
    st0N = voyst2(t0N) - neptune.state(t0N)
    stfN = voyst2(tfN) - neptune.state(tfN)
    GMN = neptune.const('GM', 1)[0]

    def dVN(th1, th2):
        enpt = entrance(Rsoi['NEPTUNE'], st0N[3:], th1, th2)
        exst = swingby(Rsoi['NEPTUNE'], np.concatenate((enpt, st0N[3:])), GMN)
        return np.linalg.norm(stfN[3:] - exst[3:])

    th1N, th2N = decaying_descent(dVN, [[-np.pi, np.pi], [-np.pi, np.pi]], [0.2, 0.2], [np.pi/20, 0], None, iters=5, decay_factor=5)
    enptN = entrance(Rsoi['NEPTUNE'], st0N[3:], th1N, th2N)
    sIntoN = np.concatenate((enptN, st0N[3:]))
    trajByN = trajectory(neptune, t0N, sIntoN, tfN)
    
    #after neptune
    after = timedelta(days=1500)
    trajAftN = trajectory(sun, tfN, voyst2(tfN), tfN + after)
    
    entranceTimes = []
    entranceTimes.extend(timesE2J)
    entranceTimes.append(t0J)
    entranceTimes.extend(timesJ2S)
    entranceTimes.append(t0S)
    entranceTimes.extend(timesS2U)
    entranceTimes.append(t0U)
    entranceTimes.extend(timesU2N)
    entranceTimes.append(t0N)
    entranceTimes.append(tfN)
    trajs = []
    trajs.extend(trajE2J)
    trajs.append(trajByJ)
    trajs.extend(trajJ2S)
    trajs.append(trajByS)
    trajs.extend(trajS2U)
    trajs.append(trajByU)
    trajs.extend(trajU2N)
    trajs.append(trajByN)
    trajs.append(trajAftN)

    voyager = path(launchTime = tfE, deltaV = 'Recreated', duration = tfN - tfE + after, entranceTimes=entranceTimes, trajectories=trajs)
    return voyager


def voyager2_original(ephem):
    earth = ephem.get_body('EARTH')
    jupiter = ephem.get_body('JUPITER')
    saturn = ephem.get_body('SATURN')
    uranus = ephem.get_body('URANUS')
    neptune = ephem.get_body('NEPTUNE')
    sun = ephem.get_body('SUN')
    
    def convert(dateObj): return sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
    voyst2 = lambda t: sp.spkezr('VOYAGER 2', convert(t), 'J2000', 'LT+S', 'SOLAR SYSTEM BARYCENTER')[0]
    
    D = 10 
    tfE = datetime(1977, 8, 21, 16, 40)
    t0J = datetime(1979, 5, 6, 15, 33)
    tfJ = datetime(1979, 9, 12, 22, 19)
    t0S = datetime(1981, 6, 29, 17, 20)
    tfS = datetime(1981, 10, 22, 18, 26)
    t0U = datetime(1985, 12, 15, 5, 6)
    tfU = datetime(1986, 3, 6, 13, 52)
    t0N = datetime(1989, 6, 26, 12, 6)
    tfN = datetime(1989, 10, 24, 7, 6)
    
    
    timesE2J = []
    trajE2J = []
    for i in range(D):
        tE2J = (t0J - tfE) * i / D + tfE
        state = voyst2(tE2J)    
        timesE2J.append(tE2J)
        trajE2J.append(trajectory(sun, tE2J, state, tE2J + (t0J - tfE) / D))
    
    #swingby at jupiter
    trajByJ = trajectory(jupiter, t0J, voyst2(t0J)-jupiter.state(t0J), tfJ)
    
    #jupiter to saturn
    timesJ2S = []
    trajJ2S = []
    for i in range(D):
        tJ2S = (t0S - tfJ) * i / D + tfJ
        state = voyst2(tJ2S)    
        timesJ2S.append(tJ2S)
        trajJ2S.append(trajectory(sun, tJ2S, state, tJ2S + (t0S - tfJ) / D))
        
    #swingby at saturn
    trajByS = trajectory(saturn, t0S, voyst2(t0S)-saturn.state(t0S), tfS)

    #saturn to uranus
    timesS2U = []
    trajS2U = []
    for i in range(D):
        tS2U = (t0U - tfS) * i / D + tfS
        state = voyst2(tS2U)    
        timesS2U.append(tS2U)
        trajS2U.append(trajectory(sun, tS2U, state, tS2U + (t0U - tfS) / D))
    
    #swingby at uranus
    trajByU = trajectory(uranus, t0U, voyst2(t0U)-uranus.state(t0U), tfU)
    
    #uranus to neptune
    timesU2N = []
    trajU2N = []
    for i in range(D):
        tU2N = (t0N - tfU) * i / D + tfU
        state = voyst2(tU2N)    
        timesU2N.append(tU2N)
        trajU2N.append(trajectory(sun, tU2N, state, tU2N + (t0N - tfU) / D))
    
    #swingby at neptune
    trajByN = trajectory(neptune, t0N, voyst2(t0N)-neptune.state(t0N), tfN)
    
    #after neptune
    after = timedelta(days=1500)
    trajAftN = trajectory(sun, tfN, voyst2(tfN), tfN + after)
    
    entranceTimes = []
    entranceTimes.extend(timesE2J)
    entranceTimes.append(t0J)
    entranceTimes.extend(timesJ2S)
    entranceTimes.append(t0S)
    entranceTimes.extend(timesS2U)
    entranceTimes.append(t0U)
    entranceTimes.extend(timesU2N)
    entranceTimes.append(t0N)
    entranceTimes.append(tfN)
    trajs = []
    trajs.extend(trajE2J)
    trajs.append(trajByJ)
    trajs.extend(trajJ2S)
    trajs.append(trajByS)
    trajs.extend(trajS2U)
    trajs.append(trajByU)
    trajs.extend(trajU2N)
    trajs.append(trajByN)
    trajs.append(trajAftN)

    voyager = path(launchTime = tfE, deltaV = 'Original', duration = tfN - tfE + after, entranceTimes=entranceTimes, trajectories=trajs)
    return voyager
