class passive_body:
    #all units in SI. pos and vel are type np.array
    def __init__(self, name, pos, vel):
        self.name = name
        self.pos = pos
        self.vel = vel
    
    def update(self, timedelta):
        