import numpy as np
import vpython as vp
from math import sqrt
SOLAR_SYSTEM = ['SUN', 'MERCURY', 'VENUS', 'EARTH', 'MARS', 'JUPITER', 'SATURN', 'URANUS', 'NEPTUNE', 'PLUTO']
COLORS = [vp.color.orange, vp.color.gray(0.5), vp.color.yellow, 
          vp.color.blue, vp.color.red, vp.color.yellow, 
          vp.color.yellow, vp.color.green, vp.color.blue, 
          vp.color.gray(0.5)]
#just for graphics
REL_VRADII = [10, 10, 10, 10, 10, 20, 30, 50, 50, 50]

class gravsystem:
    
    def __init__(self, ephemeris, t0, body_name_list=SOLAR_SYSTEM, colors=COLORS, rel_vradii=REL_VRADII):

        #planets and stars that move by set orbits
        self.body_list = []
        for i, body_name in enumerate(body_name_list):
            body = ephemeris.get_body(body_name)
            body.set_visuals(rel_vradii[i], colors[i], True)
            self.body_list.append(body)
        
        #bodies affected by gravity
        self.passive_body_list = []
        
        #time is datetime obj
        self.time = t0
    
    def add_passive_body(self, passive_body):
        self.passive_body_list.append(passive_body)

    def grav_field(self, pos):
        
        def mag(vec):
            return sqrt(np.sum(vec * vec))
  
        net_field = np.zeros(3)
        for body in self.body_list:
            GM = body.Gmass
            r = body.pos(self.time) - pos
            g = r * GM/(mag(r)**3)
            net_field += g
            
        return net_field
            
    #timestep is timedelta object
    def update(self, timestep):
        for passive_body in self.passive_body_list:
            passive_body.update(timestep.total_seconds(), self.grav_field(passive_body.pos))
        self.time += timestep
    
    def draw(self, scale=1/(10**6)):
        for body in self.body_list:
            body.draw(self.time, scale)
        for passive_body in self.passive_body_list:
            passive_body.draw(scale)

