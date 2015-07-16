# s3yum

## Introduction
A simple command line utility for maintaining s3-based yum repos in concert
with [yum-s3-iam](https://github.com/seporaitis/yum-s3-iam).

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

### Environment Variables:
 * `CREATEREPO` - path to 'createrepo' executable
 * `AWS_CREDENTIAL_FILE` - path to credential file for AWS auth
 * `AWS_ACCESS_KEY_ID` - aws access key
 * `AWS_SECRET_ACCESS_KEY` - aws secrety key

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
Copyright 2013,2014,2015 New York Times Company

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
