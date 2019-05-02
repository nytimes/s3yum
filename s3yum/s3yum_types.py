#!python
# -*- coding: utf-8 -*-
#==============================================================================
#
# s3yum: Repo creation/maintenance tool for S3-based yum repos
#
# Copyright 2013-2019 The New York Times Company
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

"""s3yum.s3yum_types: Types used by the s3yum command line module."""

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


#--------------------------
#     Utility Classes:
#--------------------------
class S3YumContext(object):

    """
    Simple class used to carry around contextual data for an s3yum invocation
    """

    def __init__(self):
        """
        Basic init.
        """
        self.action = None # Action being performed (e.g. LIST, GET, CREATE)
        self.args = None # All non-option command line arguments
        self.opts = None # Command line options
        self.parser = None # The parser object used to get options
        self.rpm_args = None # Filename command line arguments
        self.s3_bucket = None # boto.s3.Bucket object used for session
        self.s3_conn = None # boto.s3.Connection object used for AWS
        self.s3_repodata_items = None # List of s3 repodata items
        self.s3_repodata_path = None # The path within the bucket to repodata
        self.s3_rpm_items = None # List of s3 rpm items
        self.working_dir = None # The local working directory
        self.working_dir_repodata = None # Path to local repodata folder
        return

# EOF
