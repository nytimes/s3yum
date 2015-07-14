#!python
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

#----------------
#    Imports:    
#----------------
import sys
import string
import re
import logging
import hashlib

#--------------------------
#    Exception Classes:    
#--------------------------
class UserError(Exception):
    """
    Exception type raised to indicate a user error
    """

    def __init__(self, msg):
        self.strerror = msg


class ServiceError(Exception):
    """
    Exception type raised to indicate that the service has encountered an error
    """

    def __init__(self, msg):
        self.strerror = msg


#----------------------------------------------
#            s3yum Utility Functions:
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

def get_print_fn(opts):
    """
    Called at init to get a verbose function, based on -v switch.
    """
    def verbose(msg, *args):
        if opts.dry_run:
            msg_prefix = "(Dry run): "
        else:
            msg_prefix = ''

        if opts.verbose > 0:
            out_msg = msg%(args)
            print >>sys.stderr, msg_prefix + out_msg
        return

    # If extra verbosity was specified, turn on boto logging:
    if opts.verbose > 1:
        boto_logger = logging.getLogger('boto')
        FORMAT = '%(module)s:%(funcName)s (%(levelname)s): %(message)s'
        logging.basicConfig(format=FORMAT, stream=sys.stderr)

        # For every additional -v option, we increase the log verbosity:
        addl_verbose = opts.verbose - 2 # -1 for -v
        lvl_delta = logging.ERROR - logging.WARNING
        log_level = max(logging.ERROR - (addl_verbose*lvl_delta),logging.DEBUG)
        boto_logger.setLevel(log_level)
        verbose("Verbosity: %i; Boto log level: %s",
            opts.verbose, logging.getLevelName(log_level))
        
    return verbose

def get_progress_fn(opts, name):
    """
    Utility function to print upload/download progress.
    """
    def progress_fn(recv, total):
        if opts.verbose:
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

# EOF

