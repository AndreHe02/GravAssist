import json

class dotdict(dict):
    """modified from https://stackoverflow.com/questions/2352181"""
    """dot.notation access to dictionary attributes"""
    def __getattr__(*args): 
        val = dict.get(*args)
        return dotdict(val) if type(val) is dict else val
  
    def __getitem__(*args):
        val = dict.get(*args)
        return dotdict(val) if type(val) is dict else val
        
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def parse_config(dir='config.json'):
    with open(dir, 'r') as file:
        return dotdict(json.loads(file.read().replace('\n', '')))