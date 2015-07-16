#!python
# -*- coding: utf-8 -*-
#==============================================================================
#
# s3yum: Repo creation/maintenance tool for S3-based yum repos
#
# Copyright 2013,2014 The New York Times Company
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#==============================================================================

"""s3yum.util: Generic utility functions used by s3yum.

This module contains functionality utilized by s3yum in order to perform
various tasks. The functions are generic - there is no s3yum-specific business
logic in this module.
"""

#----------------
#    Imports:
#----------------
import os
import sys
import string
import re
import logging
import hashlib
import datetime

#----------------------------------------------
#                Functions:
#----------------------------------------------
def s3join(*args):
    """
    Join two strings to form an s3 path.
    """
    outstr = string.join(args, '/')
    outstr = re.sub(r'\/+', '/', outstr)
    if outstr.startswith('/'):
        outstr = outstr[1:]
    return outstr


def get_print_fn(is_dryrun, is_verbose):
    """
    Called at init to get a verbose function, based on -v switch.
    """
    def verbose(msg, *args):
        if is_dryrun:
            msg_prefix = "(Dry run): "
        else:
            msg_prefix = ''

        if is_verbose > 0:
            out_msg = msg % (args)
            print >>sys.stderr, msg_prefix + out_msg
        return

    # If extra verbosity was specified, turn on boto logging:
    if is_verbose > 1:
        boto_logger = logging.getLogger('boto')
        FORMAT = '%(module)s:%(funcName)s (%(levelname)s): %(message)s'
        logging.basicConfig(format=FORMAT, stream=sys.stderr)

        # For every additional -v option, we increase the log verbosity:
        addl_verbose = is_verbose - 2  # -1 for -v
        lvl_delta = logging.ERROR - logging.WARNING
        log_level = max(
            logging.ERROR - (addl_verbose * lvl_delta), logging.DEBUG)
        boto_logger.setLevel(log_level)
        verbose("Verbosity: %i; Boto log level: %s",
                is_verbose, logging.getLevelName(log_level))

    return verbose


def get_progress_fn(is_verbose, name):
    """
    Utility function to print upload/download progress.
    """
    def progress_fn(recv, total):
        if is_verbose:
            sys.stdout.write("\r%s: %i/%ib" % (name, recv, total))
            sys.stdout.flush()

            if recv >= total:
                sys.stdout.write('\n')
                sys.stdout.flush()
    return progress_fn


def get_file_md5(filepath):
    """
    Generate an md5 checksum of the file located at "filepath"
    """
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    with open(filepath, 'r') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()


def md5_matches(filepath, checksum_md5):
    """
    Verify that the md5 checksum of the file located at filepath matches
    the given checksum.
    """
    local_md5 = get_file_md5(filepath)
    return local_md5 == checksum_md5


def mtime_as_datetime(filepath):
    """
    Return the modified time of the file given by *filepath* as a datetime.
    """
    file_mtime = os.path.getmtime(filepath)
    return datetime.datetime.fromtimestamp(file_mtime)


def s3time_as_datetime(t_string):
    """
    The Amazon S3 API does not consistently use a single API. Rather, depending
    on which S3 command is used, AWS will return a string in one of the
    following *fwo* formats - depending on the action being invoked:
        '%Y-%m-%dT%H:%M:%S.%fZ'
                OR
        '%a, %d %b %Y %H:%M:%S %Z'

    Given one of these two time formats, this function attempts to convert
    the string representation of the datetime, into a standard python datetime
    object.

    None is returned on failure.
    """
    stamp_s3 = None
    try:
        stamp_s3 = datetime.datetime.strptime(t_string,
                                              '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        try:
            stamp_s3 = datetime.datetime.strptime(t_string,
                                                  '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            raise Exception(
                'Unable to find a matching time format for "%s"' % (t_string))
    return stamp_s3


# EOF
