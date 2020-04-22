import numpy as np
import vpython as vp

#constants for visuals
opacityConst = 1.0

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
        self.emissive = False


    def const(self, const_name, dim):
        return np.array(self.sp.bodvrd(self.name, const_name, dim)[1])

    def state(self, time):
        def convert(dateObj):
            return self.sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
        if self.name=='SUN':barycenter = 'SOLAR SYSTEM BARYCENTER'
        elif self.name=='MOON': barycenter = 'MOON'
        else:barycenter = self.name + ' BARYCENTER'
        [state, ltime] = self.sp.spkezr(barycenter, convert(time), 'J2000', self.mode, self.observer)
        return np.array(state)

    def pos(self, time):
        return self.state(time)[:3]

    def vel(self, time):
        return self.state(time)[3:6]

    def soi(self, time):
        # Basyal-(2.17) : R(SoI) = (semi-major axis)*((planetMass)/(sunMass))**(2/5)
        dist = self.sp.vnorm(self.state(time)[0:3])
        GM_S = self.sp.bodvrd ( "SUN", "GM", 1)
        return dist*(self.Gmass[0]/GM_S[1][0]) ** (2/5)

    def set_visuals(self, vradius=10, color=vp.color.white, make_trail=False, em=False, trail='points'):
        self.vradius = vradius
        self.color = color
        self.trail = trail
        self.make_trail = make_trail
        self.emissive = em

    def draw(self, time, scale=1/(10**6)):
        if not self.visual:
            self.visual = vp.sphere(pos=vp.vector(*(self.pos(time)*scale)),
                                    radius=self.vradius,
                                    color=self.color,
                                    emissive = self.emissive,
                                    make_trail = self.make_trail,
                                    trail_type = self.trail,
                                    retain=100,
                                    opacity = opacityConst)
        else:
            self.visual.pos = vp.vector(*(self.pos(time)*scale))
