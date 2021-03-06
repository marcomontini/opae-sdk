# Copyright(c) 2017, Intel Corporation
#
# Redistribution  and  use  in source  and  binary  forms,  with  or  without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of  source code  must retain the  above copyright notice,
#  this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name  of Intel Corporation  nor the names of its contributors
#   may be used to  endorse or promote  products derived  from this  software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,  BUT NOT LIMITED TO,  THE
# IMPLIED WARRANTIES OF  MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT  SHALL THE COPYRIGHT OWNER  OR CONTRIBUTORS BE
# LIABLE  FOR  ANY  DIRECT,  INDIRECT,  INCIDENTAL,  SPECIAL,  EXEMPLARY,  OR
# CONSEQUENTIAL  DAMAGES  (INCLUDING,  BUT  NOT LIMITED  TO,  PROCUREMENT  OF
# SUBSTITUTE GOODS OR SERVICES;  LOSS OF USE,  DATA, OR PROFITS;  OR BUSINESS
# INTERRUPTION)  HOWEVER CAUSED  AND ON ANY THEORY  OF LIABILITY,  WHETHER IN
# CONTRACT,  STRICT LIABILITY,  OR TORT  (INCLUDING NEGLIGENCE  OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,  EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import glob
import os
import re
import sys
import subprocess

INSTALL_PATH = '/usr/local/bin'

# TODO: Use AFU IDs vs. names of AFUs
BIST_MODES = ['nlb_3', 'dma_afu']


# Return a list of all available bus numbers
def get_all_fpga_bdfs():
    pattern = '\d+:(?P<bus>\w{2}):(?P<device>\d{2})\.(?P<function>\d)'
    bdf_pattern = re.compile(pattern)
    bdf_list = []
    for fpga in glob.glob('/sys/class/fpga/*'):
        symlink = os.path.basename(os.readlink(os.path.join(fpga, "device")))
        m = bdf_pattern.match(symlink)
        data = m.groupdict() if m else {}
        if data:
            bdf_list.append(dict([(k, int(v, 16))
                            for (k, v) in data.iteritems()]))
    return bdf_list


def get_bdf_from_args(args):
    pattern = "(?P<bus>\w{2}):(?P<device>\d{2})\.(?P<function>\d).*?."
    pattern += vars(args)['device_id']
    bdf_pattern = re.compile(pattern)
    bdf_list = []
    param = ':{}:{}.{}'.format(
            vars(args)['bus']
            if vars(args)['bus'] else '',
            vars(args)['device']
            if vars(args)['device'] else '',
            vars(args)['function']
            if vars(args)['function'] else '')
    host = subprocess.check_output(['/usr/sbin/lspci', '-s', param])
    matches = re.findall(bdf_pattern, host)
    for match in matches:
        bdf_list.append({'bus': match[0], 'device': match[1],
                        'function': match[2]})
    return bdf_list


def get_mode_from_path(gbs_path):
    if not os.path.isfile(gbs_path):
        return None
    pattern = r'^(.*\/)(.*)[^gbs]'
    match = re.match(pattern, gbs_path)
    if match is None:
        return None
    return match.group(2)


def load_gbs(install_path, gbs_file, bus_num):
    print "Attempting Partial Reconfiguration:"
    fpga_conf_path = os.path.join(install_path, 'fpgaconf')
    cmd = "{} -b {} -v {}".format(fpga_conf_path, bus_num, gbs_file)
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print "Failed to load gbs file: {}".format(gbs_file)
        print "Please try a different gbs"
        sys.exit(-1)


class BistMode(object):
    name = ""
    executables = {}
    dir_path = ""

    def run(self, gbs_path, bus_num):
        raise NotImplementedError


def global_arguments(parser):
    parser.add_argument('-i', '--device-id', default='09c4',
                        type=str,
                        help='Device Id for Intel FPGA default: 09c4')

    parser.add_argument('-b', '--bus', type=int,
                        help='Bus number for specific FPGA')

    parser.add_argument('-d', '--device', type=int,
                        help='Device number for specific FPGA')

    parser.add_argument('-f', '--function', type=int,
                        help='Function number for specific FPGA')

    parser.add_argument('gbs_paths', nargs='+', type=str,
                        help='Paths for the gbs files for BIST')
