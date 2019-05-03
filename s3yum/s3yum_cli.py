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


"""s3yum.s3yum_cli: Command line interface for s3yum.

This module contains the entry point, inteface functions, and business logic
for the s3yum utility.
"""


#----------------
#    Imports:
#----------------
import os
import sys
import time
import string
import optparse
import boto
import boto.s3
import boto.s3.connection
import boto.sts
import tempfile
import shutil
import re
import traceback
import subprocess
import fnmatch

from s3yum.s3yum_types import (
    UserError,
    ServiceError,
    S3YumContext
)
from s3yum.util import (
    s3join,
    get_print_fn,
    get_progress_fn,
    md5_matches,
    get_s3item_md5,
    mtime_as_datetime,
    s3time_as_datetime
)


#----------------------------------------------
#                   Globals:
#----------------------------------------------
verbose = None  # <-- verbose flag used by get_print_fn

# Program metadata:
USAGE = "usage: %prog ACTION [OPTIONS] [RPM1] [RPM2] ... [RPM2]"
DESCRIPTION = "Create/maintain s3-based yum repos"
VERSION = "1.6.4"

# s3yum actions:
HELP = 'help'
LIST = 'list'
CREATE = 'create'
UPDATE = 'update'
GET = 'get'
DELETE = 'delete'

ACTIONS_HELP = {
    HELP: 'provide help for a given action',
    LIST: 'list repo contents',
    CREATE: 'create a new yum repo',
    UPDATE: "update a yum repo by adding or deleting rpm's",
    GET: "copy the entirety of a given repo to a local directory",
    DELETE: "remove an entire repo (DANGEROUS!)",
}

ACTIONS = (
    HELP,
    LIST,
    CREATE,
    UPDATE,
    GET,
    DELETE,
)

ACTIONS_DESC = string.join(ACTIONS, '|')
EPILOG = """
Actions: %s (try %s)
Environment:
    CREATEREPO - path to 'createrepo' executable
    AWS_CREDENTIAL_FILE - path to credential file for AWS auth
     or
    AWS_ACCESS_KEY_ID - aws access key
    AWS_SECRET_ACCESS_KEY - aws secrety key
""" % (ACTIONS_DESC, HELP)

# Constants:
REPODATA = 'repodata'
CREATEREPO = os.environ.get('CREATEREPO', 'createrepo')
FOLDER_SUFFIX = "_$folder$"


#----------------------------------------------
#                 Interface:
#----------------------------------------------
def parse_args(context, argv):
    """
    Parse input arguments.
    """
    class EpilogParser(optparse.OptionParser):

        def format_epilog(self, formatter):
            return self.epilog

    parser = EpilogParser(
        usage=USAGE, version=VERSION,
        description=DESCRIPTION,
        epilog=EPILOG)

    parser.add_option(
        "-v", "--verbose",
        help='Verbose output - repeat usage increases level, adds boto logs',
        action='count', default=0)

    parser.add_option(
        "-b", "--bucket",
        help='S3 bucket in which to store/update repo data',
        type='string', default=None)

    parser.add_option(
        "--region",
        help='ec2 region to connect to',
        type='string', default=None)

    parser.add_option(
        "-p", "--path",
        help='Root path of the repo (RPM destination) relative to bucket',
        type='string', default='dev')

    parser.add_option(
        "-o", "--output",
        help='Where to download the repo for GET action.',
        type='string', default=None)

    parser.add_option(
        "-w", "--working-dir",
        help='Download and create repo from this directory instead of tmpdir',
        type="string", default=None)

    parser.add_option(
        "-r", "--remove",
        help="Remove one or more rpm's from the repo (file globs)",
        type='string', action='append', default=[])

    parser.add_option(
        "--force-download",
        help="Force all rpms to download, instead of just the missing ones.",
        action='store_true', default=False)

    parser.add_option(
        "--force-upload",
        help="Force all rpms to upload, instead of just the missing ones.",
        action='store_true', default=False)

    parser.add_option(
        "--dry-run",
        help='Indicate what would happen, ' +
        'without actually modifying the *remote* repo',
        action='store_true', default=False)

    parser.add_option(
        '--assume-role',
        help='Indicate that s3yum should assume the role given in the arn',
        type='string', action='store', default=None)

    default_session_name = "s3yum_{0}".format(time.time())
    parser.add_option(
        '--role-session-name',
        help='Optional session name for --assume-role',
        type='string', action='store', default=default_session_name)

    parser.add_option(
        '--role-external-id',
        help='Optional external id for --assume-role',
        type='string', action='store', default=None)

    (opts, args) = parser.parse_args(argv)
    context.opts = opts
    context.args = args
    context.parser = parser

    if len(args) > 1:
        context.action = args[1].lower()
    else:
        context.action = None

    opts.path = re.sub(r'^\/+', '', opts.path)
    context.rpm_args = args[2:]
    return opts


def confirm_delete(context):
    """
    Make sure we really want to do this.
    """
    print "ALL of yum metadata and RPM's will be deleted from:"
    print "%s/%s" % (context.opts.bucket, context.opts.path)

    answer = None
    count = 0
    while not answer and count < 5:
        answer = raw_input(
            "Are you sure you want to delete this repo? (yes/no):")
        if answer not in ['yes', 'no']:
            print 'Please type "yes" or "no"'
            answer = None
        count += 1

    if answer == 'yes':
        return True
    return False


#----------------------------------------------
#             Filesystem Functions:
#----------------------------------------------
def init_workingdir(context):
    """
    Make sure we have a valid working directory.
    If the user passed -w, use the input directory.
    Otherwise, create a temp directory.
    Attempt to create the dirctory if it doesn't exist, bailing on OSError.
    """
    try:
        # Create temp dir:
        if context.opts.working_dir:
            context.working_dir = context.opts.working_dir
            context.working_dir_repodata = os.path.join(
                context.working_dir,
                REPODATA)
            if not os.path.exists(context.working_dir):
                verbose('Working directory "%s" does not exist. Creating..',
                        context.working_dir)
                os.makedirs(context.working_dir)

        else:
            context.working_dir = tempfile.mkdtemp()
            context.working_dir_repodata = os.path.join(
                context.working_dir,
                REPODATA)
    except OSError as ex:
        err_msg = 'Unable to initialize working directory: "%s": %s (%i)' % (
            ex.filename, ex.strerror, ex.errno)
        raise ServiceError(err_msg)
    return


def copy_rpms(context):
    """
    Copy input rpm's into the working directory.
    """
    for rpm_path in context.rpm_args:
        try:
            verbose("Copying %s to tmp...", rpm_path)
            shutil.copy(rpm_path, context.working_dir)
        except IOError as ex:
            err_msg = 'Error copying "%s": %s (%i)' % (
                ex.filename, ex.strerror, ex.errno)
            raise ServiceError(err_msg)
    return


#----------------------------------------------
#                 S3: Connect
#----------------------------------------------
def connect_to_bucket(context):
    """
    Connect to s3 and get the specified bucket, if it exists.
    """
    try:
        # If we're assuming a role, attempt to get temporary credentials:
        if context.opts.assume_role:
            sts_conn = boto.sts.STSConnection()
            assumedRoleObject = sts_conn.assume_role(
                role_arn=context.opts.assume_role,
                role_session_name=context.opts.role_session_name,
                external_id=context.opts.role_external_id)
            if context.opts.region:
                conn = boto.s3.connect_to_region(
                    region_name=context.opts.region,
                    aws_access_key_id=assumedRoleObject.credentials.access_key,
                    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
                    security_token=assumedRoleObject.credentials.session_token)
            else:
                conn = boto.connect_s3(
                    aws_access_key_id=assumedRoleObject.credentials.access_key,
                    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
                    security_token=assumedRoleObject.credentials.session_token)
        # Otherwise, create an s3 connection using the default creds:
        else:
            if context.opts.region:
                conn = boto.s3.connect_to_region(
                    region_name=context.opts.region)
            else:
                conn = boto.connect_s3()

        bucket = boto.s3.bucket.Bucket(conn, context.opts.bucket)
        context.s3_conn = conn
        context.s3_bucket = bucket
    except boto.exception.BotoServerError as ex:
        raise ServiceError(str(ex))
    except boto.exception.S3ResponseError as ex:
        raise ServiceError("S3 Error: %s" % ex.error_message)
    return


#----------------------------------------------
#                  S3: List
#----------------------------------------------
def print_lists(context):
    """
    Print repo info and bail.
    """
    def list_item(item):
        print "\t%s - %ib - %s" % (
            item.name, item.size, item.last_modified)

    print "Repo info for %s:" % (s3join(context.opts.bucket, context.opts.path))
    for metadata_item in context.s3_repodata_items:
        list_item(metadata_item)

    for rpm_item in context.s3_rpm_items:
        list_item(rpm_item)
    return


def list_metadata(context):
    """
    List the current repo metadata items in s3, storing in s3_repodata_items.
    """
    context.s3_repodata_path = s3join(context.opts.path, REPODATA)
    key_list = context.s3_bucket.list(prefix=context.s3_repodata_path)

    context.s3_repodata_items = []
    for item in key_list:
        if item.name.find(FOLDER_SUFFIX) != -1:
            continue

        context.s3_repodata_items.append(item)

    return


def list_rpms(context):
    """
    List the current rpm items in s3, storing in s3_rpm_items.
    """
    key_list = context.s3_bucket.list(prefix=context.opts.path)
    context.s3_rpm_items = []
    for item in key_list:
        if not item.name.endswith('.rpm'):
            continue
        context.s3_rpm_items.append(item)
    return


#----------------------------------------------
#                 S3: Download
#----------------------------------------------
def should_download(item, filepath, force_download):
    """
    Return true if item should be downloaded to filepath, false otherwise.

    We download if any of the following are true:
     - force_download is True
     - the file doesn't exist
     - the checksums differ and the remote file is newer
    """
    if force_download or not os.path.exists(filepath):
        return True

    local_mtime = mtime_as_datetime(filepath)
    remote_mtime = s3time_as_datetime(item.last_modified)
    files_differ = not md5_matches(filepath, get_s3item_md5(item))
    return files_differ and remote_mtime >= local_mtime


def download_items(context, items, dest_dir, force_download=False):
    """
    Download the s3 items given by 'items' into the destination directory
    given by 'dest_dir'. If force_download is true, download *everything* in
    the list. Otherwise, skip downloads for items which are already present
    in the working directory.
    """
    try:
        no_items = 0
        for item in items:
            # Skip folder keys:
            if item.name.find(FOLDER_SUFFIX) != -1:
                verbose("Not downloading: %s", item.name)
                continue

            filename = os.path.basename(item.name)
            filepath = os.path.join(dest_dir, filename)

            if should_download(item, filepath, force_download):
                f = open(filepath, 'w')

                item.get_file(f, cb=get_progress_fn(
                    context.opts.verbose, "Downloading %s" % item.name))

                f.close()

                # Verify the checksum of the downloaded item:
                if not md5_matches(filepath, get_s3item_md5(item)):
                    raise ServiceError(
                        "\nDownload failed: md5 mismatch for %s" % (filename))
            else:
                verbose('File "%s" already exists in "%s" skipping download',
                        filename, dest_dir)
            no_items += 1

        return no_items
    except IOError as ex:
        err_msg = "Error opening %s: %s (%i)" % (
            ex.filename, ex.strerror, ex.errno)
        raise ServiceError(err_msg)
    return


def get_repo(context, dest_dir):
    """
    Download the entire repo to 'dest_dir' on the local disk.
    """
    repodata_dir = os.path.join(dest_dir, REPODATA)
    if not os.path.exists(repodata_dir):
        try:
            os.makedirs(repodata_dir)
        except OSError as ex:
            err_msg = 'Unable to create "%s": %s' % (
                repodata_dir, ex.strerror)
            raise ServiceError(err_msg)

    download_items(context, context.s3_repodata_items, repodata_dir, True)
    download_items(
        context,
        context.s3_rpm_items,
        dest_dir,
        context.opts.force_download)
    return


#----------------------------------------------
#                 S3: Upload
#----------------------------------------------
def should_upload(filepath, item, force_upload):
    """
    Return true if the file at filepath should be uploaded, false otherwise.

    We upload if any of the following are true:
     - force_upload is True
     - the remote item doesn't exist
     - the checksums differ and the local file is newer
    """
    if force_upload or not item:
        return True

    local_mtime = mtime_as_datetime(filepath)
    remote_mtime = s3time_as_datetime(item.last_modified)
    files_differ = not md5_matches(filepath, get_s3item_md5(item))
    return files_differ and local_mtime >= remote_mtime


def upload_directory(context, dir_path, upload_prefix, check_items=[]):
    """
    Upload all the files in the directory 'dir_path' into the s3 bucket.
    The variable 'upload_prefix' is the path relative to the s3 bucket.
    The list item 'check_items' is a list of existing s3 items at this path.
    If an item to be uploaded is found in check_items, it is skipped.
    """

    items_by_name = dict(zip(map(
        lambda x: os.path.basename(x.name), check_items), check_items))

    # Upload RPM's:
    for filename in os.listdir(dir_path):
        filepath = os.path.join(dir_path, filename)
        remote_item = items_by_name.get(filename, None)

        # Skip any non-file arguments:
        if not os.path.isfile(filepath):
            continue

        # Skip anything that doesn't need to be uploaded:
        if not should_upload(filepath, remote_item, context.opts.force_upload):
            verbose(
                'File "%s" already exists in S3 location "%s" skipping upload',
                filename, upload_prefix)
            continue

        # Perform the upload:
        dest_path = s3join(upload_prefix, filename)
        item_key = boto.s3.key.Key(context.s3_bucket)
        item_key.key = dest_path
        if not context.opts.dry_run:
            item_key.set_contents_from_filename(
                filepath, cb=get_progress_fn(
                    context.opts.verbose, "Uploading: %s" % dest_path))
        else:
            verbose("Uploading: %s" % dest_path)
    return


def upload_repodata(context):
    """
    Upload repodata to the specified bucket.
    """
    upload_directory(
        context,
        context.working_dir,
        context.opts.path,
        context.s3_rpm_items)

    # ALWAYS delete the existing s3 metadata items and upload the new ones.
    # We NEVER use check_items here:
    # Delete old metadata:
    for item in context.s3_repodata_items:
        verbose("Deleting old metadata file: %s", item.name)
        if not context.opts.dry_run:
            item.delete()

    # Delete any --remove'd RPM's:
    for item in context.s3_rpm_items:
        for remove_rpm in context.opts.remove:
            if fnmatch.fnmatch(item.name, remove_rpm):
                verbose("Deleting: %s", item.name)
                if not context.opts.dry_run:
                    item.delete()

    # Upload new metadata:
    repo_dest = s3join(context.opts.path, REPODATA)
    upload_directory(context, context.working_dir_repodata, repo_dest)
    return


#----------------------------------------------
#                S3: Delete
#----------------------------------------------
def delete_repo(context):
    """
    Delete the repo metadata and all rpm's.
    """
    delete_ok = confirm_delete(context)
    if not delete_ok:
        print "Delete aborted!"
        return False

    # Delete old metadata:
    for item in context.s3_repodata_items:
        verbose("Deleting old metadata file: %s", item.name)
        if not context.opts.dry_run:
            item.delete()

    # Delete any --remove'd RPM's:
    for item in context.s3_rpm_items:
        verbose("Deleting: %s", item.name)
        if not context.opts.dry_run:
            item.delete()
    return True


#----------------------------------------------
#                    yum:
#----------------------------------------------
def create_repodata(context):
    """
    Invoke 'createrepo' to create the repodata folder to upload.
    """
    try:
        verbose("Generating yum repo metadata")
        if os.path.exists(context.working_dir_repodata):
            verbose(
                'Removing old repodata: "%s"',
                context.working_dir_repodata)
            shutil.rmtree(context.working_dir_repodata)

        args = [CREATEREPO]
        args.append(context.working_dir)
        cmd_line = ' '.join(args)
        verbose("Executing: %s", cmd_line)

        if sys.version_info >= (2, 7):
            output = subprocess.check_output(args)
            verbose(output)
        else:
            subprocess.check_call(args)

    except subprocess.CalledProcessError as ex:
        err_msg = "'%s' failed with status code %i: %s" % (
            CREATEREPO, ex.returncode, ex.output)
        raise ServiceError(err_msg)

    except OSError as ex:
        err_msg = "Unable to invoke '%s': %s" % (
            CREATEREPO, ex.strerror)
        raise ServiceError(err_msg)

    return


#----------------------------------------------
#                  s3yum:
#----------------------------------------------
def perform_action(context):
    """
    Perform specific action, as indicated on command line.
    """
    # Create: mktmp, copy rpms, configure, and upload
    if context.action == CREATE:
        init_workingdir(context)
        copy_rpms(context)
        create_repodata(context)
        upload_repodata(context)

    # Update: mktmp, get into tmp, copy rpms, configure, and upload
    elif context.action == UPDATE:
        init_workingdir(context)
        get_repo(context, context.working_dir)
        copy_rpms(context)
        create_repodata(context)
        upload_repodata(context)

    # List: just print
    elif context.action == LIST:
        print_lists(context)

    # Get: copy to output directory
    elif context.action == GET:
        get_repo(context, context.opts.output)

    # Destroy the repo!
    elif context.action == DELETE:
        delete_repo(context)
    return


def main(argv=None):
    """
    Main logic.
    """
    if argv is None:
        argv = sys.argv

    context = S3YumContext()
    try:
        parse_args(context, argv)

        global verbose
        verbose = get_print_fn(context.opts.dry_run, context.opts.verbose)

        # Validate args:
        if not context.action:
            raise UserError("Please specify an action")

        if context.action not in ACTIONS:
            raise UserError("Bad action: '%s'. Action must be one of: %s" % (
                str(context.action), ACTIONS_DESC))

        if context.action == HELP:
            print "Valid actions:"
            for action, usage in ACTIONS_HELP.items():
                print "\t%s: %s" % (action, usage)
            sys.exit(0)

        if context.action in (
                CREATE, UPDATE) and not context.rpm_args and not context.opts.remove:
            raise UserError("Please specify at least one RPM to add/remove.")

        if not context.opts.bucket:
            raise UserError("Please specify a bucket.")

        if context.action in (GET) and not context.opts.output:
            raise UserError("Please specify an output directory.")

        # Init tmp, copy rpms, get the bucket, create repodata, upload:
        connect_to_bucket(context)
        list_metadata(context)
        list_rpms(context)
        perform_action(context)
    except IOError as ex:
        print("Error: Unable to read from %s: %s (%i)" % (
            ex.filename, ex.strerror, ex.errno))

    except UserError as ex:
        print(ex.strerror)
        context.parser.print_help()

    except ServiceError as ex:
        print(ex.strerror)

    except Exception:
        traceback.print_exc()

    #==============
    #=- Cleanup: -=
    #==============

    # Remove *temp* working dir, but not user-specified:
    if context.working_dir is not None and not context.opts.working_dir:
        shutil.rmtree(context.working_dir)
    return


if __name__ == '__main__':
    main(sys.argv)
# EOF
