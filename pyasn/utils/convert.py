#!/usr/bin/python

# Copyright (c) 2009-2017 Hadi Asghari
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# MRT RIB log import  [to convert to a text IP-ASN lookup table]
# file to use per day should be of the RouteViews or RIPE RIS series, e.g.:
# http://archive.routeviews.org/bgpdata/2009.11/RIBS/rib.20091125.0600.bz2

from __future__ import print_function, division
from pyasn import mrtx, __version__
from time import time
from sys import stdout
from glob import glob
from datetime import datetime, timedelta
from subprocess import call
from argparse import ArgumentParser


def get_parser():
    # Parse command line options
    parser = ArgumentParser(description="Script to convert MRT/RIB archives to IPASN databases.",
                            epilog="MRT/RIB archives can be downloaded using "
                            "'pyasn_util_download.py', or directly from RouteViews (or RIPE RIS).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--single", nargs=2, metavar=("RIBFILE", "IPASN.DAT"), action="store",
                       help="convert single file (use bz2 or gz suffix)")
    group.add_argument("--dump-screen", nargs=1, metavar="RIBFILE", action="store",
                       help="parse and dump archive to screen")
    group.add_argument("--bulk", nargs=2, metavar=("START-DATE", "END-DATE"), action="store",
                       help="bulk conversion (dates are Y-M-D, files need to be "
                       "named rib.xxxxxxxx.bz2 and in current directory)")
    group.add_argument("--version", action="store_true")
    # FIXME: tie --no-progress/--compress/--skip and --record-xx to respective options above
    parser.add_argument("--compress", action="store_true",  # in place of --binary (20160105)
                        help="gzip the IPASN output files (with --single)")
    parser.add_argument("--no-progress", action="store_true",
                        help="don't show conversion progress (with --single)")
    parser.add_argument("--skip-on-error", action="store_true",
                        help="skip records which fail conversion, instead of stopping (with --single)")
    parser.add_argument("--record-from", type=int, metavar="N", action="store",
                        help="start dump from record N (with --dump-screen)")
    parser.add_argument("--record-to", type=int, metavar="N", action="store",
                        help="end dump at record N (with --dump-screen)")
    return parser


def main(single=None, dump_screen=None, bulk=None, record_from=None, record_to=None, compress=False, no_progress=False, skip_on_error=False, version=False):
    if version:
        print("MRT/RIB converter version %s." % __version__)


    if single:
        prefixes = mrtx.parse_mrt_file(single[0],
                                       print_progress=not no_progress,
                                       skip_record_on_error=skip_on_error)
        mrtx.dump_prefixes_to_file(prefixes, single[1], single[0])
        if not no_progress:
            v6 = sum(1 for x in prefixes if ':' in x)
            v4 = len(prefixes) - v6
            print('IPASN database saved (%d IPV4 + %d IPV6 prefixes)' % (v4, v6))
        if compress:
            call(['gzip', single[1]])


    if dump_screen:
        mrtx.dump_screen_mrt_file(dump_screen[0],
                                  record_to=record_to,
                                  record_from=record_from,
                                  screen=stdout)


    if bulk:
        try:
            dt = datetime.strptime(bulk[0], '%Y-%m-%d').date()  # TODO:
            dt_end = datetime.strptime(bulk[1], '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("ERROR: malformed date, try YYYY-MM-DD")
        print("Starting bulk RIB conversion, from %s to %s..." % (dt, dt_end))
        stdout.flush()
        while dt <= dt_end:
            # for each day, process first file named "rib.YYYYMMDD.xxxx.bz2". (what about .gz?)
            # this is default filename used by routeviews and downloaded by pyasn_wget_rib.py
            files = glob("rib.%4d%02d%02d.????.bz2" % (dt.year, dt.month, dt.day))
            if not files:
                dt += timedelta(1)
                continue
            if len(files) > 1:
                print("warning: multiple files on %s, only converting first." % dt)
            dump_file = files[0]
            print("%s... " % dump_file[4:-4])
            stdout.flush()
            dat = mrtx.parse_mrt_file(dump_file)
            out_file = "ipasn_%d%02d%02d.dat" % (dt.year, dt.month, dt.day)
            mrtx.dump_prefixes_to_file(dat, out_file, dump_file)
            if compress:
                call(['gzip', out_file])
            dt += timedelta(1)
        #
        print('Finished!')

def climain():
    parser = get_parser()
    args = parser.parse_args()
    args_dict = vars(args)
    return main(**args_dict)

if __name__ == "__main__":
    climain()
