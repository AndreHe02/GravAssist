class body:
    def __init__(self, name, sp, mode, observer):
        self.name = name
        self.sp = sp
        self.observer = observer
        self.mode = mode

    def const(self, const_name, dim):
        return self.sp.bodvrd(self.name, const_name, dim)[1]

    def Gmass(self):
        return self.const('GM', 1)

    def radii(self):
        return self.const('RADII', 3)

    def state(self, time):
        def convert(dateObj):
            return self.sp.str2et(dateObj.strftime("%Y %b %d %H:%M:%S").lower())
        if self.name=='SUN':barycenter = 'SOLAR SYSTEM BARYCENTER'
        else:barycenter = self.name + ' BARYCENTER'
        [state, ltime] = self.sp.spkezr(barycenter, convert(time), 'J2000', self.mode, self.observer)
        return state

    def pos(self, time):
        return self.state(time)[:3]

    def vel(self, time):
        return self.state(time)[3:6]     