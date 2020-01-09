import numpy as np
import vpython as vp
from math import sqrt

class gravsystem:
    
    def __init__(self, config, ephemeris, t0):
        
        bodies_config = config.bodies

        #planets and stars that move by set orbits
        self.body_list = {}
        for body_name in bodies_config:
            body_config = bodies_config[body_name]
            body = ephemeris.get_body(body_config)
            self.body_list[body_name] = body
        
        #bodies affected by gravity
        self.passive_body_list = {}
        
        #time is datetime obj
        self.time = t0
    
    def add_passive_body(self, passive_body):
        self.passive_body_list[passive_body.name] = passive_body

    def grav_field(self, pos):
        
        def mag(vec):
            return sqrt(np.sum(vec * vec))
  
        net_field = np.zeros(3)
        for key in self.body_list:
            body = self.body_list[key]
       
            if body.nograv: pass
            
            GM = body.Gmass
            r = body.pos(self.time) - pos
            g = r * GM/(mag(r)**3)
            net_field += g
            
        return net_field
            
    #timestep is timedelta object
    def update(self, timestep):
        for key in self.passive_body_list:
            passive_body = self.passive_body_list[key]
            passive_body.update(timestep.total_seconds(),
                                               self.grav_field(passive_body.pos))
        #other bodies automatically update with time
        self.time += timestep
    
    def draw(self, scale=1/(10**6)):
        for key in self.body_list:
            self.body_list[key].draw(self.time, scale)
        for key in self.passive_body_list:
            self.passive_body_list[key].draw(scale)

