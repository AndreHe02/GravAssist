import numpy as np
import vpython as vp
from math import sqrt
SOLAR_SYSTEM = ['SUN', 'MERCURY', 'VENUS', 'EARTH', 'MARS', 'JUPITER', 'SATURN', 'URANUS', 'NEPTUNE', 'PLUTO']
BARYCENTERS = ['SOLAR SYSTEM BARYCENTER', None, None, None, None, None, None, None, None, None] 
COLORS = [vp.color.orange, vp.color.gray(0.5), vp.color.yellow, 
          vp.color.blue, vp.color.red, vp.color.yellow, 
          vp.color.yellow, vp.color.green, vp.color.blue, 
          vp.color.gray(0.5)]
#just for graphics, not to scale
REL_VRADII = [10, 10, 10, 10, 10, 20, 30, 50, 50, 50]

class gravsystem:
    
    def __init__(self, ephemeris, t0, body_name_list=SOLAR_SYSTEM,
                 barycenter_list=BARYCENTERS, colors=COLORS, rel_vradii=REL_VRADII):

        #planets and stars that move by set orbits
        self.body_list = {}
        for i, body_name in enumerate(body_name_list):
            body = ephemeris.get_body(body_name, barycenter_list[i])
            body.set_visuals(rel_vradii[i], colors[i], True)
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

