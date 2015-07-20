### v1.6.0 2015/07/20:
#### Features:
 - Repeat `--verbose` options turn on and increase boto log output
 - Updated default download behavior:
   - Always download if local file does not exist or `--force-download`
   - Else: Download if local md5 and remote md5 differ and remote is newer
 - Updated default upload behavior:
   - Always upload if remote file does not exist or `--force-upload`
   - Else: Upload if local md5 and remote etag differ and local is newer

#### Misc:
 - Move from distutils -> setuptools
 - Restrucutre s3yum as setuptools "console_script" + associated module (for testability)
 - Added tests
 - Updated docs
 - More pep8 compliant + silence pyflakes warnings
 - Refactor to split functions into three submodules for ease of maintenance
 - Refactor to use a "Context" object internally, rather than monkey-patching the optparse object

### v1.5.0 2015/07/06:
Added *--region* parameter:
 - If absent: connect to the local region in EC2; default region from outside AWS
 - If present: connect to the specified region

### v1.4.0 2014/12/6:
Added *assume role* functionality:

 * --assume-role: to provide role ARN
 * --role-session-name: to provide an explicit session name (default is s3yum_<timestampe>, otherwise)
 * --role-external-id: optional external id (if required)

### v1.3.2 2014/11/06:
BUGFIX: fixed error message in download_directory.

### v1.3.1 2014/11/06:
BUGFIX: force upload of input arguments, regardless of --force-upload status.

### v1.3.0 2014/10/31:
Added new options:
 * --working-dir: specify a persistent working dir instead of temp
 * --force-upload: force upload of all files
 * --force-download: force download of all files

By default now, s3yum will not download files already present in the working dir
or upload files already present in the S3 bucket.

At present, the existence checks are based on *name only*.

### v1.2.2 2014/10/31:
* More patches to update command
* Do not use --update, in case the existing repodata is corrupt

### v1.2.2 2014/10/29:
* Fixed UPDATE command to perform a GET and then update the repodata.

### v1.2 2014/05/2:
* Removed yum_proxyd.

