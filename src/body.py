import numpy as np
import vpython as vp

class body:
    def __init__(self, sp, body_config, mode, observer):
        
        self.sp = sp
        self.config = body_config
        self.observer = observer
        self.mode = mode
 
        self.name = body_config.name
        self.barycenter = body_config.barycenter
        
        self.Gmass = self.const('GM', 1)
        self.radii = self.const('RADII', 3)
        self.nograv = body_config.nograv
        
        self.visual = None
        
    def const(self, const_name, dim):
        return np.array(self.sp.bodvrd(self.name, const_name, dim)[1])

    def state(self, time):
        def convert(dateObj):
            return self.sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
        [state, ltime] = self.sp.spkezr(self.barycenter, convert(time), 'J2000', self.mode, self.observer)
        return np.array(state)

    def pos(self, time):
        return self.state(time)[:3]

    def vel(self, time):
        return self.state(time)[3:6]  
    
    def draw(self, time, scale=1/(10**6)):
        if not self.visual:
            if not self.config.other:
                self.visual = vp.sphere(pos=vp.vector(*(self.pos(time)*scale)), 
                                        radius=self.config.radius, 
                                        color=vp.vector(*self.config.color))
            else:
                #import all other visual attr from config
                self.visual = vp.sphere(pos=vp.vector(*(self.pos(time)*scale)), 
                                        radius=self.config.radius, 
                                        color=vp.vector(*self.config.color),
                                        **self.config.other)  
        else:
            self.visual.pos = vp.vector(*(self.pos(time)*scale))

    def change_visual(self, attr, arg):
        setattr(self.visual, attr, arg)
        
        