from __future__ import print_function
from builtins import input
from datetime import datetime
import spiceypy

#test function to see if spiceypy is installed correctly
def print_ver():
        """Prints the TOOLKIT version
        """
        print(spiceypy.tkvrsn('TOOLKIT'))

#get relative position and velocity of target from POV of observer at TIME, using correction mode mode
def getsta(target, TIME, mode = "LT+S", observer = "SOLAR SYSTEM BARYCENTER"):
    # https://spiceypy.readthedocs.io/en/master/remote_sensing.html
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
    utctim = parseDate(TIME)

    #print( 'Converting UTC Time: {:s}'.format(utctim)  )

    #
    #Convert utctim to ET.
    #
    et = spiceypy.str2et( utctim )

    #print( '   ET seconds past J2000: {:16.3f}'.format(et) )

    #
    # Compute the apparent state of target as seem from
    # observer in the J2000 frame.  All of the ephemeris
    # readers return states in units of kilometers and
    # kilometers per second.
    #
    [state, ltime] = spiceypy.spkezr( target, et,      'J2000',
                                      mode,   observer       )

    #print( '   Apparent state of MARS BARYCENTER (4) as seen '
           #'from SSB (0) in the J2000\n'
           #'      frame (km, km/s):'              )

    #print( '      X = {:16.3f}'.format(state[0])       )
    #print( '      Y = {:16.3f}'.format(state[1])       )
    #print( '      Z = {:16.3f}'.format(state[2])       )
    #print( '     VX = {:16.3f}'.format(state[3])       )
    #print( '     VY = {:16.3f}'.format(state[4])       )
    #print( '     VZ = {:16.3f}'.format(state[5])       )

    spiceypy.unload( METAKR )

    return state

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
