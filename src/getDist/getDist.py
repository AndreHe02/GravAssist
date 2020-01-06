from __future__ import print_function
from builtins import input
from datetime import datetime, timedelta
import spiceypy

#test function to see if spiceypy is installed correctly
def print_ver():
        """Prints the TOOLKIT version
        """
        print(spiceypy.tkvrsn('TOOLKIT'))

#get relative position and velocity of target from POV of observer at TIME, using correction mode mode
def getsta(target, TIME, mode = "LT+S", observer = "SOLAR SYSTEM BARYCENTER"):
    ##the following are from https://spiceypy.readthedocs.io/en/master/remote_sensing.html
    #
    # Local parameters
    #
    METAKR = 'getsta.tm'

    #
    # Load the kernels that this program requires.  We
    # will need a leapseconds kernel to convert input
    # UTC time strings into ET.  We also will need the
    # necessary SPK files with coverage for the bodies
    # in which we are interested.
    #
    spiceypy.furnsh( METAKR )

    #
    #Prompt the user for the input time string.
    #
    utctim = TIME

    print( 'Converting UTC Time: {:s}'.format(utctim)  )

    #
    #Convert utctim to ET.
    #
    et = spiceypy.str2et( utctim )

    print( '   ET seconds past J2000: {:16.3f}'.format(et) )

    #
    # Compute the apparent state of Phoebe as seen from
    # CASSINI in the J2000 frame.  All of the ephemeris
    # readers return states in units of kilometers and
    # kilometers per second.
    #
    [state, ltime] = spiceypy.spkezr( target, et,      'J2000',
                                      mode,   observer       )

    print( '   Apparent state of MARS BARYCENTER (4) as seen '
           'from SSB (0) in the J2000\n'
           '      frame (km, km/s):'              )

    print( '      X = {:16.3f}'.format(state[0])       )
    print( '      Y = {:16.3f}'.format(state[1])       )
    print( '      Z = {:16.3f}'.format(state[2])       )
    print( '     VX = {:16.3f}'.format(state[3])       )
    print( '     VY = {:16.3f}'.format(state[4])       )
    print( '     VZ = {:16.3f}'.format(state[5])       )

def below10(num):
    if(num<10):
        return '0'
    else:
        return ''

def formatDateNumElement(num):
    return s.format(below10(num)+num)

#parses 1234.12.12 into '1234 mon 12 12:34:56"
def parseDate(dateObj):
    return dateObj.strftime("%Y %b %d %H:%M:%S").lower()


if __name__ == '__main__':
    #s = "2019 jun 11 00:00:00"

    #getsta(target, TIME, mode, observer):
    #mode is default to be LT+S, it is a method they use to correct data, which is recommended in the tutorial w/ Cassini
    #observer is default to be SSB (0), solar system barycenter
    #time is required (s = "2019 jun 11 00:00:00")
    #target is required

    tgt = 'MARS BARYCENTER' #this example uses Mars Barycenter (4)

    #for i in range(0,59):
        #print(s.format(below10(i),i),end="")
        #getsta(target = tgt, TIME = s.format(below10(i),i))

    print("date format: yyyy.mm.dd --no spaces, all numbers")
    s1 = input("starting date:")
    s2 = input("ending date:")
    print("increment is 8hrs at default, change in prgm")

    dateStart = datetime(int(s1[0:4]), int(s1[5:7]), int(s1[8:10]))
    dateEnd = datetime(int(s2[0:4]), int(s2[5:7]), int(s2[8:10]))
    dateTemp = dateStart

    dateLs = []
    tDlt = timedelta(days = 8)

    #print(dateStart)
    while dateTemp < dateEnd:
        dateLs.append(parseDate(dateTemp))
        dateTemp += tDlt
        #print(dateTemp)

    print (dateLs)

    print('---------------------------')

    for i in dateLs:
        getsta(tgt, i)
    
