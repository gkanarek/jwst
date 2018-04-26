
from __future__ import (absolute_import, unicode_literals, division,
                        print_function)
import sys
import numpy as np
import math


#_______________________________________________________________________

def radec2std(crval1,crval2,ra,dec):
    """
    Compute the standard coordinates xi,eta from CRVAL1,CRVAL2 & ra,dec
    """

    def check_val(ra):
        ra = np.asarray(ra)
    def check_val(dec):
        dec = np.asarray(dec)

    rad2arcsec = (180.0*3600.0)/math.pi
    deg2rad = math.pi/180.0

    ra0 = crval1*deg2rad
    dec0 = crval2*deg2rad
    radiff = ra*deg2rad - ra0;
    decr = dec*deg2rad;

    h = np.sin(decr) *math.sin(dec0) + np.cos(decr)*math.cos(dec0)*np.cos(radiff);

    xi = np.cos(decr)*np.sin(radiff)/h;
    eta = ( np.sin(decr)*math.cos(dec0) - np.cos(decr)*math.sin(dec0)*np.cos(radiff) )/h;

    xi = xi * rad2arcsec
    xi = -xi # xi is made negative so it increase in the opposite direction of ra
             # to match the images the Parity of the ifu_cue is for ra is PC1_1 = -1
             
    eta = eta * rad2arcsec


    return xi,eta

#________________________________________________________________________________
def std2radec(crval1,crval2,xi,eta):

# Compute the Ra,dec from CRVAL1,CRVAL2 & xi,eta

# This program uses a ONLY tangent (gnomonic projection).

# Inputs:
#  ra,dec : right acsension and declination
# CRVAL1: ra value of reference point
# CRVAL2: dec value of reference point
# Outputs:
#  xi     - standard coordinate
#  eta    - standard coordinate



    eta = np.asarray([eta])
    xi = np.asarray([xi])

    rad2arcsec = (180.0*3600.0)/math.pi
    deg2rad = math.pi/180.0

    ra0 = crval1*deg2rad
    dec0 = crval2*deg2rad

  # tangent projection
    xi = xi/ rad2arcsec
    eta = eta/rad2arcsec
    xi = -xi # xi is made negative so it increase in the opposite direction of ra
             # to match the images the Parity of the ifu_cue is for ra is PC1_1 = -1
    # TODO: check back to float64

    ra0 = crval1 * deg2rad
    dec0 = crval2 * deg2rad
   

    beta = math.cos(dec0) - eta*math.sin(dec0)

    angle = xi/beta

    ra = np.arctan(angle) + ra0
    gamma = np.sqrt(xi*xi + beta*beta)
    angle =eta*math.cos(dec0) +  math.sin(dec0)
    angle = angle/gamma
    dec = np.arctan(angle)
    ra = ra/deg2rad
    dec = dec/deg2rad
    

    mask = ra < 0
    ra[mask] +=  360.0
    mask = ra > 360.0
    ra[mask] -=  360.0

    return ra,dec
  
#_______________________________________________________________________
def V2V32RADEC_ESTIMATE(ra_ref,dec_ref,roll_ref,v2_ref,v3_ref,v2, v3):
    """
    This routine is used for debugging purposes. It is not actually used
    in the cube_build step for routine IFU cube building.
    The conversion from V2,V3 to Ra,dec  is handled more accuarately by
    the transforms provided by assign_wcs. 
    v2_ref,v3_ref given in arc seconds 
    v2 and v3 are given in arc seconds
    ra_ref,dec_ref, roll_ref given in degrees
    it is assumed that the V2,V3 coordinates have the effects of dithering included
    """
    d2r = math.pi/180.0

    v2deg = v2.copy()/3600.0      # convert to degrees
    v3deg = v3.copy()/3600.0      # convert to degrees


    v2_ref = v2_ref/3600.0 # covert to degrees
    v3_ref = v3_ref/3600.0 # convert to degrees
    v3_ref_rad = v3_ref*d2r
    roll_ref_rad = roll_ref * d2r
        
    delta_v2 = (v2deg - v2_ref) * math.cos(v3_ref_rad)
    delta_v3 = (v3deg - v3_ref)
    delta_ra = delta_v2 * math.cos(roll_ref_rad) + delta_v3* math.sin(roll_ref_rad)
    delta_dec = -delta_v2* math.sin(roll_ref_rad) + delta_v3*math.cos(roll_ref_rad)

    ra = ra_ref + delta_ra/math.cos(dec_ref*d2r)
    dec = delta_dec + dec_ref

    return ra,dec
#_______________________________________________________________________

#_______________________________________________________________________
def RADEC2V2V3_ESTIMATE(ra_ref,dec_ref,roll_ref,v2_ref,v3_ref,ra, dec):
    """
    This routine is used for debugging purposes. It is not actually used
    in the cube_build step for routine IFU cube building.
    The conversion from Ra,Dec to V2,V3 is handled more accuarately by
    the transforms provided by assign_wcs. 

        # v2_ref,v3_ref given in arc seconds
        # v2 and v3 are given in arc seconds
        # ra_ref,dec_ref, roll_ref given in degrees
        # ra,dec are given in degrees
     """
        
    d2r = math.pi/180.0

    r2d = 180.0  / math.pi

    v3_ref_rad = (v3_ref)/3600.0* d2r # convert from arc seconds to radians
    v2_ref_rad = (v2_ref)/3600.0* d2r # convert from arc seconds to radians 

    roll_ref_rad = roll_ref * d2r

    ra_ref_rad = ra_ref*d2r
    dec_ref_rad = dec_ref*d2r
    this_ra = ra*d2r
    this_dec  = dec*d2r

    delta_ra = (this_ra - ra_ref_rad) * math.cos(dec_ref_rad)
    delta_dec = (this_dec-dec_ref_rad)

    dv2 = delta_ra* math.cos(roll_ref_rad) - delta_dec*math.sin(roll_ref_rad) 
    dv3 = delta_ra*math.sin(roll_ref_rad) + delta_dec*math.cos(roll_ref_rad)

    v2 = v2_ref_rad + dv2/math.cos(v3_ref_rad)
    v3 = v3_ref_rad + dv3

    v2 = v2*r2d*3600.0  # convert from radians to arc seconds 
    v3  = v3*r2d*3600.0 # convert from radians to arc seconds

    return v2,v3
