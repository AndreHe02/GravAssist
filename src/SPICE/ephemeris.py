import os
from body import body

class ephemeris:      
    
    def __init__(self, sp, config):
        self.sp = sp
        
        os.chdir(config.root_dir + '/spice/')
        self.sp.furnsh(config.metadata)
        os.chdir(config.root_dir)
        
        self.mode = config.mode
        self.observer = config.observer
        self.config = config
    
    def get_body(self, body_config):
        return body(self.sp, body_config, self.mode, self.observer)
    
    def __del__(self):
        self.sp.unload(self.config.metadata)
    
        
        