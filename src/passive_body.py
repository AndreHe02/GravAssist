import vpython as vp

class passive_body:
    #all units in SI. pos and vel are type np.array
    def __init__(self, name, pos, vel):
        self.name = name
        self.pos = pos
        self.vel = vel
        
        self.visual = None
        self.vradius = 10
        self.color = vp.color.white
        self.make_trail = False
    
    #Semi-implicit Euler method, timestep is scalar in seconds
    def update(self, timestep, acc):
        self.vel = self.vel + acc * timestep
        self.pos = self.pos + self.vel * timestep
     
    def set_visuals(self, vradius=10, color=vp.color.white, make_trail=False):
        self.vradius = vradius
        self.color = color
        self.make_trail = make_trail
    
    def draw(self, scale=1/(10**6)):
        if not self.visual:
            self.visual = vp.sphere(pos=vp.vector(*(self.pos*scale)), 
                                    radius=self.vradius, 
                                    color=self.color,
                                    make_trail = self.make_trail,
                                    trail_type = 'points')
        else:
            self.visual.pos = vp.vector(*(self.pos*scale))
            self.visual.radius = self.vradius
            self.visual.color = self.color
            self.visual.make_trail = self.make_trail