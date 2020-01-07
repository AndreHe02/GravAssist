from __future__ import print_function
from getDist import getDist
import os
from datetime import datetime, timedelta

if __name__ == '__main__':
    os.chdir("./getDist/")
    getDist.getsta("EARTH",datetime(2008,6,6))
