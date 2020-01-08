import numpy as np
import vpython as vp

class body:
    def __init__(self, name, sp, mode, observer):
        self.name = name
        self.sp = sp
        self.observer = observer
        self.mode = mode
        self.Gmass = self.const('GM', 1)
        self.radii = self.const('RADII', 3)
        
        self.visual = None
        self.vradius = 10
        self.color = vp.color.white
        self.make_trail = False
        
    def const(self, const_name, dim):
        return np.array(self.sp.bodvrd(self.name, const_name, dim)[1])

    def state(self, time):
        def convert(dateObj):
            return self.sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
        if self.name=='SUN':barycenter = 'SOLAR SYSTEM BARYCENTER'
        else:barycenter = self.name + ' BARYCENTER'
        [state, ltime] = self.sp.spkezr(barycenter, convert(time), 'J2000', self.mode, self.observer)
        return np.array(state)

    def pos(self, time):
        return self.state(time)[:3]

    def vel(self, time):
        return self.state(time)[3:6]  
    
    def set_visuals(self, vradius=10, color=vp.color.white, make_trail=False):
        self.vradius = vradius
        self.color = color
        self.make_trail = make_trail
    
    def draw(self, time, scale=1/(10**6)):
        if not self.visual:
            self.visual = vp.sphere(pos=vp.vector(*(self.pos(time)*scale)), 
                                    radius=self.vradius, 
                                    color=self.color,
                                    make_trail = self.make_trail,
                                    trail_type = 'points')
        else:
            self.visual.pos = vp.vector(*(self.pos(time)*scale))
        