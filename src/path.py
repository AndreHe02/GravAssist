from datetime import datetime, timedelta
import numpy as np
import spiceypy as sp

class path(object):

    def __init__(self, launchTime, deltaV, duration, entranceTimes, trajectories):
        #this is just for demo
        self.launch = launchTime

        #other basic info for display
        self.deltaV = deltaV

        #in timedelta form
        self.duration = duration

        #a list of times on which the probe enters a trajectory,
        #the length of this array should match that of the length of trajectories
        self.entranceTimes = entranceTimes
        self.trajectories = trajectories

        self.flyby = []
        for i in self.trajectories:
            self.flyby.append(i.body.name)

    #what absolute position is the probe at 'time'
    def getPosition(self, flightTime):
        t = self.getTrajTime(flightTime)
        traj = self.getTrajectory(flightTime)

        area = traj.av * t
        absTime = self.launch+timedelta(seconds=flightTime)
        #print('t: ', self.launch+timedelta(seconds=flightTime))
        #print('tName: ', type(absTime).__name__)
        return np.array(traj.body.state(absTime)[0:3]) + np.array(sp.prop2b(traj.GM, traj.entranceState, t)[0:3])

    def getRelPosition(self, flightTime):
        t = self.getTrajTime(flightTime)
        traj = self.getTrajectory(flightTime)

        area = traj.av * t
        absTime = self.launch+timedelta(seconds=flightTime)
        #print('t: ', self.launch+timedelta(seconds=flightTime))
        #print('tName: ', type(absTime).__name__)
        return np.array(sp.prop2b(traj.GM, traj.entranceState, t)[0:3])

    #what trajectory is the probe in at 'time'
    def getTrajectory(self, flightTime):
        for i, e in reversed(list(enumerate(self.entranceTimes))):
            if flightTime >= (e - self.launch).total_seconds():
                return self.trajectories[i]

    #time in orbit
    def getTrajTime(self, flightTime):
        for i, e in reversed(list(enumerate(self.entranceTimes))):
            if flightTime >= (e - self.launch).total_seconds():
                return flightTime - (e-self.launch).total_seconds()

