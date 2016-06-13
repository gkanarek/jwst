#! /usr/bin/env python
# Author: Dave Grumm
# Program: compare_cr_navg_files.py
# Purpose: routine to compare locations of created crs to detected crs
# History: 11/23/10 - first version, base on compare_cr_files.py, but here navg is a required command line argument
#
# Required Input:
#   'created_file':  file of generated GCR/SPs that was output by mc_single_2d or mc_3d
#   'found_file':  file of detected GCR/SPs that was generated by ramp_fit or ramp_fit_arr
#   'sim_file' : file containing a simulated (2d) image which was the input to create_cube
#   'slope_file' : file of calculated slope averages that was calculated and output by ramp_fit or ramp_fit_arr
#   'navg': number of reads that are averaged over
#
# Optional Input:
#  'verb': level of verbosity for print statements; verb=2 is extremely verbose, verb=1 is moderate,
#           verb=0 is minimal; default = 0
#
# Arrays output to files:
#  'f_only.fits': 2d array of pixels that were found but not created
#  'c_only.fits': 2d array of pixels that were created but not found
#  'neither.fits: 2d array of pixels that were neither created nor found
#  'both.fits': 2d array of pixels that were both created and found
#  'c_navg.fits': data cube of averaged values of pixels with created CRs
#
# Usage from linux command line:
# ./compare_cr_files.py cr_and_sp.fits foundcr.fits test_sim_30.fits fslopes.fits 4
#   ... where the file of the created CRs (created_file) = 'cr_and_sp.fits',
#   the file of the detected CRs (found_file) = 'foundcr.fits',
#   the sample image file (sim_file) = 'test_sim_30.fits',
#   the calculated count rate file (slope_file) = 'fslopes.fits',
#   the number of reads averaged over = 4
#
# Usage within pyraf :
# --> a1 = compare_cr_navg_files.compare_cr_navg_files("cr_and_sp.fits","foundcr.fits","sim_2k_30.fits","fslopes.fits",4)
# --> status = a1.compare()
#

from __future__ import division, print_function
import sys, os, time
from astropy.io import fits
import numpy as N


ERROR_RETURN = 2

class compare_cr_navg_files:

    def __init__(self, created_file, found_file, sim_file, slope_file, navg, verb=1):
        """ Constructor
        @param created_file: file of generated GCR/SPs
        @type created_file: string
        @param found_file: file of detected GCR/SPs
        @type found_file: string
        @param sim_file: file of simulated image
        @type sim_file: string
        @param slope_file: file of calculated slope averages
        @type slope_file: string
        @param navg: number of reads to average over
        @type navg: int
        @param verb: verbosity level
        @type verb: integer
        """

        print(' Starting compare_cr_navg_files.py: ')
        print(' current time (start) = ', time.asctime())
        print(' Input parameters: ')
        print('   created_file :', created_file)
        print('   found_file :', found_file)
        print('   sim_file :', sim_file)
        print('   slope_file :', slope_file)
        print('   navg :', navg)
        print('   verb :', verb)

        self.created_file = created_file
        self.found_file = found_file
        self.sim_file = sim_file
        self.slope_file = slope_file
        self.navg = navg
        self.verb = verb

    def compare(self):
        """ Compare the detected CRs in the averaged data with the created CRs
        """
        verb = int(self.verb)

        tstart = time.time()

        # open all 4 files
        fh_c = open_file(created_file)  # file of generated GCR/SPs
        fh_f = open_file(found_file)    # file of detected GCR/SPs
        fh_true = open_file(sim_file)   # file of simulated image
        fh_avg = open_file(slope_file)    # file of calculated slope averages

        data_c = fh_c[0].data
        data_f = fh_f[0].data
        data_true = fh_true[0].data
        data_avg = fh_avg[0].data

        xx_size_c = data_c.shape[2]; yy_size_c = data_c.shape[1]
        xx_size_f = data_f.shape[2]; yy_size_f = data_f.shape[1]
        xx_size_true = data_true.shape[1]; yy_size_true = data_true.shape[0]
        xx_size_avg = data_avg.shape[1]; yy_size_avg = data_avg.shape[0]

        if (verb > 0):
            print('  ')
            print('The number of reads averaged over (navg) : ', navg)
            print('The dimensions of the created array: ', xx_size_c, yy_size_c)
            print('The dimensions of the found array: ', xx_size_f, yy_size_f)
            print('The dimensions of the true array: ', xx_size_true, yy_size_true)
            print('The dimensions of the average (calculated) array: ', xx_size_avg, yy_size_avg)
            print('  ')

        # Check for compatibility of array sizes
        if ((xx_size_c != xx_size_f) or(yy_size_c != yy_size_f)):
            print(' arrays in found and created files have incompatible sizes, so maybe using the wrong created file ')
            sys.exit(ERROR_RETURN)
        if ((xx_size_c != xx_size_true) or(yy_size_c != yy_size_true)):
            print(' arrays in true and created files have incompatible sizes, so maybe using the wrong created file ')
            sys.exit(ERROR_RETURN)
        if ((xx_size_c != xx_size_avg) or(yy_size_c != yy_size_avg)):
            print(' arrays in calculated(averaged) and created files have incompatible sizes, so maybe using the wrong created file ')
            sys.exit(ERROR_RETURN)

        xx_size = xx_size_c; yy_size = yy_size_c # all sizes compatible, so use more generic names ?????

        NSTACK = data_c.shape[0]  # number of slices

        # create 1d arrays for later stats
        data_true_1 = data_true.ravel()
        data_avg_1 = data_avg.ravel()
        data_diff_1 = data_avg_1 - data_true_1

        true_nonneg = N.where(data_true_1 >= 0.)
        avg_neg1 = N.where(data_avg_1 == -1.0)  # calculated slopes where data was insufficient

        # set arrays for nonnegative pixels values
        data_diff_nonneg = navg * data_avg_1[true_nonneg] - data_true_1[true_nonneg]

        avg_nonneg = data_avg_1[true_nonneg]
        true_nonneg = data_true_1[true_nonneg]

        total_c = N.add.reduce(N.add.reduce(N.add.reduce(N.where(data_c > 0.0, 1, 0)))) # number of created GCR/SPs
        if (verb > 0):
            print('The total number of gcr/sps created in ', created_file, ' is ', total_c)
            print('For all data in which the true count rates are nonnegative: ')
            print('  the calculated (avg) data: min, mean, max, std = ', avg_nonneg.min(), avg_nonneg.mean(), avg_nonneg.max(), avg_nonneg.std())
            print('  the true data: min, mean, max, std = ', true_nonneg.min(), true_nonneg.mean(), true_nonneg.max(), true_nonneg.std())
            print('  the navg*avg-true: min, mean, max, std = ', data_diff_nonneg.min(), data_diff_nonneg.mean(), data_diff_nonneg.max(), data_diff_nonneg.std())
            print('   ')
            print('The number of pixels for which there is insufficient data: ', len(data_avg_1[avg_neg1]))
            print('  ')

        c_only_along_stack = N.zeros((yy_size, xx_size), dtype=N.int32)   # pixels with crs created but not found
        f_only_along_stack = N.zeros((yy_size, xx_size), dtype=N.int32)   # pixels with crs foundd but not created
        neither_along_stack = N.zeros((yy_size, xx_size), dtype=N.int32)  # pixels with no crs created or found
        both_along_stack = N.zeros((yy_size, xx_size), dtype=N.int32)     # pixels with crs both created and found


        # the following apply to each pixel in each stack
        tot_c_only = 0 # number of pixels with crs created but not found
        tot_f_only = 0  # number of pixels with crs found but not created
        tot_neither = 0 # number of pixels with no crs created or found
        tot_both = 0    # number of pixels with crs both created and found

        max_reads = int(NSTACK / navg) # number of reads in averaged data
        c_navg_pixel = N.zeros((max_reads, yy_size, xx_size), dtype=N.int32) # average of created (subvectors)

        for xx_pix in range(xx_size):
            for yy_pix in range(yy_size):

                if verb > 1:
                    print(' xx, yy: ', xx_pix, ',', yy_pix)

                c_pix_whole_stack = data_c[:, yy_pix, xx_pix]
                f_pix_whole_stack = data_f[:, yy_pix, xx_pix]

                if verb > 1:
                    print(' For this pixel, the created unaveraged stack values: ')
                    print(c_pix_whole_stack)
                    print(' For this pixel, the found averaged stack values: ')
                    print(f_pix_whole_stack)

                max_reads = int(NSTACK / navg)

                c_navg_line = N.zeros((max_reads), dtype=N.float32)

                for which_read in range(0, max_reads - 1):

                    low_index = which_read * navg
                    hi_index = low_index + navg

                    c_line_piece = data_c[low_index: hi_index, yy_pix, xx_pix]
                    c_navg_line[which_read] = c_line_piece.mean()

                    if verb > 1:
                        print(' The corresponding subvectors of :')
                        print(' ... the averaged created data [', which_read, ' ]= ', c_navg_line[which_read])
                        print(' ... the averaged found data for the current pixel: ', f_pix_whole_stack[which_read])
                        print(' ... the averaged found data for the next pixel: ', f_pix_whole_stack[which_read + 1])

                    c_navg_pixel[which_read, yy_pix, xx_pix] = c_navg_line[which_read]

                    if ((c_navg_line[which_read] > 0.0) and (f_pix_whole_stack[which_read] == 0.0) and (f_pix_whole_stack[which_read + 1] == 0.0)):
                        tot_c_only += 1
                        c_only_along_stack[yy_pix, xx_pix] += 1
                        if verb > 1: print('       The subvector above is created only ')

                    elif ((c_navg_line[which_read] == 0.0) and (f_pix_whole_stack[which_read] > 0.0)):
                        tot_f_only += 1
                        f_only_along_stack[yy_pix, xx_pix] += 1
                        if verb > 1: print('       The subvector above is found only ')

                    elif ((c_navg_line[which_read] > 0.0) and ((f_pix_whole_stack[which_read] > 0.0) or (f_pix_whole_stack[which_read + 1] > 0.0))):
                        tot_both += 1
                        both_along_stack[yy_pix, xx_pix] += 1
                        if verb > 1: print('       The subvector above is both ')

                    else:  # pixel has no created or found cosmic rays
                        tot_neither += 1
                        neither_along_stack[yy_pix, xx_pix] += 1
                        if verb > 1: print('       The subvector above is neither ')



        if (verb > 1):
            for xx_pix in range(xx_size):
                for yy_pix in range(yy_size):
                    if (c_only_along_stack[yy_pix, xx_pix] > 0):
                        c_only_flag = '* C_ONLY * '
                    else:
                        c_only_flag = ' '

                    if (f_only_along_stack[yy_pix, xx_pix] > 0):
                        f_only_flag = '* F_ONLY *'
                    else:
                        f_only_flag = ' '

                    if (yy_pix % 50 == 0):
                        print('xx, yy = : c_only, f_only , neither, both, [ CFLAG / FFLAG ]  ')

                    print(xx_pix, yy_pix, ' : ', c_only_along_stack[yy_pix, xx_pix], f_only_along_stack[yy_pix, xx_pix], neither_along_stack[yy_pix, xx_pix], both_along_stack[yy_pix, xx_pix], c_only_flag, f_only_flag)

        try:
            os.remove('c_only.fits')
        except:
            pass
        print('  '); print(' For the 2d array of created only pixels:  ')
        write_to_file(c_only_along_stack, 'c_only.fits')

        try:
            os.remove('f_only.fits')
        except:
            pass
        print('  '); print(' For the 2d array of found only pixels:  ')
        write_to_file(f_only_along_stack, 'f_only.fits')

        try:
            os.remove('both.fits')
        except:
            pass
        print('  '); print(' For the 2d array of both created and found pixels:  ')
        write_to_file(both_along_stack, 'both.fits')

        try:
            os.remove('neither.fits')
        except:
            pass
        print('  '); print(' For the 2d array of neither created or found pixels:  ')
        write_to_file(neither_along_stack, 'neither.fits')

        try:
            os.remove('c_navg.fits')
        except:
            pass
        print('  '); print(' The created pixels, averaged over subvectors: ')
        write_to_file(c_navg_pixel, 'c_navg.fits')
        print('   ')

        print('The total number of pixels with CRs that were created: ', total_c)
        print('The number of pixels with CRs that were created but not found: ', tot_c_only)
        print('The number of pixels with CRS that were found but not created: ', tot_f_only)
        print('The number of pixels with CRs that were both created and found: ', tot_both)
        print('The number of pixels not having CRs that were neither created nor found: ', tot_neither)

        print('The fraction of all pixels with CRs that were found only: ', float(tot_f_only) / (tot_both + tot_neither + tot_f_only + tot_c_only))
        print('The fraction of all pixels with CRs that were created only: ', float(tot_c_only) / (tot_both + tot_neither + tot_f_only + tot_c_only))
        print('The ratio of the number of pixels that were created only to the total number of pixels that were created (in the created file):', float(tot_c_only) / total_c)
        print('The total number of all pixels in all slices: ', tot_both + tot_neither + tot_f_only + tot_c_only)

        tstop = time.time()
        print('The elapsed time: ', tstop - tstart, ' seconds')
        print('The current time (start): ', time.asctime())

def write_to_file(data, filename):
    """ Write the specified data to the specified file name
    @param data: output array
    @type data: float
    @param filename: file being output
    @type filename: string
    """

    fimg = fits.HDUList()
    fimghdu = fits.PrimaryHDU()
    fimghdu.data = data
    fimg.append(fimghdu)
    fimg.writeto(filename)
    print(' output data to: ', filename)

def open_file(filename):
    """ Open the specified file
    @param filename: file being output
    @type filename: string
    """

    try:
        fh = fits.open(filename)
    except Exception as errmess:
        print('FatalERROR: ', errmess)
        sys.exit(ERROR_RETURN)

    return fh


if __name__ == "__main__":
    """Get input file and other arguments, and call calc_slope.

            @param cmdline: command-line arguments
            @type cmdline: list of strings
    """
    usage = "usage:  %prog [options] created_file found_file sim_file slope_file navg"

    if (len(sys.argv) < 6):
        print('FATAL ERROR : missing argument(s), usage = ', usage)
        sys.exit(ERROR_RETURN)

    if (sys.argv[1]): created_file = sys.argv[1]
    if (sys.argv[2]): found_file = sys.argv[2]
    if (sys.argv[3]): sim_file = sys.argv[3]
    if (sys.argv[4]): slope_file = sys.argv[4]
    if (sys.argv[5]): navg = int(sys.argv[5])

    if (len(sys.argv) > 6):
        verb = sys.argv[6]
    else:
        verb = 1

    try:
        a1 = compare_cr_navg_files(created_file, found_file, sim_file, slope_file, navg, verb=verb)
        status = a1.compare()

    except Exception as errmess:
        print('Fatal ERROR: ', errmess)
