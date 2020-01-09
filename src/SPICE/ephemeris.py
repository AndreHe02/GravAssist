import os
from body import body

class ephemeris:      
    
    def __init__(self, sp, root_dir, METADATA='metadata.tm', mode='LT+S', observer='SOLAR SYSTEM BARYCENTER'):
        self.sp = sp
        os.chdir(root_dir + '/src/spice/')
        self.sp.furnsh(METADATA)
        os.chdir(root_dir)
        self.mode = mode
        self.observer = observer
    
    def get_body(self, target, barycenter_name=None):
        return body(target, self.sp, self.mode, self.observer, barycenter_name)
    
    
        
        