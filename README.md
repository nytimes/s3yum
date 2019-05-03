# s3yum

A simple command line utility for maintaining s3-based yum repos in concert
with [yum-s3-iam](https://github.com/seporaitis/yum-s3-iam).

#### Contents
- [Overview](#overview)
- [Build and Installation](#build-and-installation)
- [Development](#development)
- [Usage](#usage)
  - [Environment Variables](#environment-variables)
  - [Authentication](#authentication)
  - [Upload/Download Semantic](#upload/download-semantic)
  - [Examples](#examples)
- [License](#license)

## Overview

 * A developer with AWS credentials places a set of RPMs in a local directory.
 * The developer uses s3yum to maintain a copy of the RPMs in a bucket in S3;
   corresponding yum metadata is transparently maintained by s3yum.
 * The S3 bucket is private; access is allowed via signed URL's/IAM.
 * The developer creates an IAM role and adds a policy allowing
   access to the S3 bucket.
 * Instances started with that role may use it to sign requests
   for bucket access.
 * A config file is deployed to /etc/yum/repos.d on the instance which directs
   yum to the S3 bucket.


## Build and Installation
```Shell
# Install dependencies:
pip2.7 install -r ./requirements.txt
python2.7 ./setup.py install

# For more info (packaging, etc):
python2.7 ./setup.py --help-commands
```

## Development
:warning: As of version [1.6.4](https://github.com/nytimes/s3yum/releases/tag/v1.6.4),
s3yum is still developed with _python2.7_ - any future major releases will
be ported to python3.

```Shell
# Install additional development dependencies:
pip2.7 install -r dev-requirements.txt

# If you don't have virtualenv (python2.7):
pip2.7 install virtualenv

# If you already have virtualenv for a different python version:
virtualenv -p $( which python2.7 ) venv

# Source your virtual environment:
source ./venv/bin/activate

# Run tests:
nosetests -v

# If additional dependencies are added:
pip2.7 freeze > ./requirements.txt

# Deactivate when done:
deactivate
```

## Usage
The general format of an s3yum command is
`s3yum ACTION [OPTIONS] [RPM1] [RPM2] ... [RPM2]`
    
Where ACTION is one of:
 * `create`: create a new yum repo
 * `get`: copy the entirety of a given repo to a local directory
 * `list`: list repo contents
 * `help`: provide help for a given action
 * `update`: update a yum repo by adding or deleting rpm's

For detailed usage, try the following:
 * s3yum --help - display general command line usage
 * s3yum help - display available commands

### Environment Variables
 * `CREATEREPO` - path to 'createrepo' executable
 * `AWS_CREDENTIAL_FILE` - path to credential file for AWS auth
 * `AWS_ACCESS_KEY_ID` - aws access key
 * `AWS_SECRET_ACCESS_KEY` - aws secrety key

### Authentication
There are three main ways you can autenticate using s3yum:
 * Using environment variables, as described above
 * Using a [boto config](http://boto.cloudhackers.com/en/latest/boto_config_tut.html)
 * By [assuming a role](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html) using `--asume-role`

### Upload/Download Semantics
Unless `--force-upload` or `--force-download` is speicifed, s3yum uses the
following criteria to decide whether or not to upload or download a file:
 - If the source file does not exist at the destination: transfer
 - If the source file does exist at the destination, and the checksums of
   source and destination are different: transfer if the mtime of the source
   is greater than the mtime of the destination
 - If the source file exists at the destination and the checksums match:
   don't transfer the file.

### Examples
#### Example 1: Create a new repo from a set of RPM's
```Shell
s3yum CREATE -v \
    -b my_bucket.amazon.s3.com -p '/my_path' my_pkg1.rpm my_pkg2.rpm
```

#### Example 2: Adding a new RPM to a repo:
```Shell
s3yum UPDATE -v \
    -b my_bucket.amazon.s3.com -p '/my_path' my_pkg3.rpm
```

#### Example 3: Adding a new RPM to a repo, saving a copy on the local disk for re-use:
```Shell
s3yum UPDATE -v \
    -w ./my_local_path \
    -b my_bucket.amazon.s3.com -p '/my_path' my_pkg4.rpm

# This time, nothing new is downloaded and only my_pkg5.rpm and the
# new repodata will get uploaded!
s3yum UPDATE -v \
    -w ./my_local_path \
    -b my_bucket.amazon.s3.com -p '/my_path' my_pkg5.rpm
```

#### Example 4: Downloading an entire repo, including repo metadata:
```Shell
s3yum GET -v \
    -b my_bucket.amazon.s3.com -o my_repo_dir
```
 
#### Example 5: Deleting an entire repo:
```Shell
s3yum DELETE -v \
    -b my_bucket.amazon.s3.com -p '/my_path/'
```
 
## License
Copyright 2013-2019 New York Times Company

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
