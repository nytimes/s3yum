v1.3.2 2014/11/06:
------------------

BUGFIX: fixed error message in download_directory.

v1.3.1 2014/11/06:
------------------

BUGFIX: force upload of input arguments, regardless of --force-upload status.

v1.3.0 2014/10/31:
------------------

Added new options:
 * --working-dir: specify a persistent working dir instead of temp
 * --force-upload: force upload of all files
 * --force-download: force download of all files

By default now, s3yum won't download files already present in the working dir
or upload files already present in the S3 bucket.

At present, the existence checks are based on *name only*.

v1.2.2 2014/10/31:
---------------

* More patches to update command
* Don't use --update, in case the existing repodata is corrupt

v1.2.2 2014/10/29:
---------------

* Fixed UPDATE command to perform a GET and then update the repodata.

v1.2 2014/05/2:
---------------

* Removed yum_proxyd.

