from __future__ import print_function
from builtins import input
import spiceypy

def print_ver():
        """Prints the TOOLKIT version
        """
        print(spiceypy.tkvrsn('TOOLKIT'))

def getsta():
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
    utctim = input( 'Input UTC Time: ' )

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
    [state, ltime] = spiceypy.spkezr( 'PHOEBE', et,      'J2000',
                                      'LT+S',   'CASSINI'       )

    print( '   Apparent state of Phoebe as seen '
           'from CASSINI in the J2000\n'
           '      frame (km, km/s):'              )

    print( '      X = {:16.3f}'.format(state[0])       )
    print( '      Y = {:16.3f}'.format(state[1])       )
    print( '      Z = {:16.3f}'.format(state[2])       )
    print( '     VX = {:16.3f}'.format(state[3])       )
    print( '     VY = {:16.3f}'.format(state[4])       )
    print( '     VZ = {:16.3f}'.format(state[5])       )

if __name__ == '__main__':
    getsta()
