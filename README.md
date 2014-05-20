# s3yum

## Introduction
A tool for maintaining private yum repos in s3 allowing access via a smart proxy 
A 3rd-party plugin that makes private S3 repos accessible can be found here: https://github.com/seporaitis/yum-s3-iam

## Overview

 * A developer with AWS credentials places a set of RPMs in a local directory.
 * The developer uses s3yum to maintain a copy of the RPMs in a bucket in S3; corresponding yum metadata is transparently maintained by s3yum.
 * The S3 bucket is private; access is allowed using signed URL's/IAM credentials.
 * The developer creates an IAM role and adds a policy allowing access to the S3 bucket.
 * Instances started with that role may use it to sign requests for bucket access.
 * A config file is deployed to /etc/yum/repos.d on the instance which directs yum to the S3 bucket.
 * The download then completes using the URL with temporary access credentials appended in the query string of the URI.

## Usage
The general format of an s3yum command is

    s3yum ACTION [OPTIONS] [RPM1] [RPM2] ... [RPM2]
    
Where ACTION is one of:
 * create: create a new yum repo
 * get: copy the entirety of a given repo to a local directory
 * list: list repo contents
 * help: provide help for a given action
 * update: update a yum repo by adding or deleting rpm's

For detailed usage, try the following:
 * s3yum --help - display general command line usage
 * s3yum help - display available commands

#### Example 1: Create a new repo from a set of RPM's
    s3yum CREATE -v \
        -b my_bucket.amazon.s3.com -p '/my_path' my_pkg1.rpm my_pkg2.rpm

#### Example 2: Adding a new RPM to a repo:
    s3yum UPDATE -v \
        -b my_bucket.amazon.s3.com -p '/my_path' my_pkg3.rpm

#### Example 3: Downloading an entire repo, including repo metadata:
    s3yum GET -v \
        -b my_bucket.amazon.s3.com -o my_repo_dir
 
#### Example 4: Deleting an entire repo:
    s3yum DELETE -v \
        -b my_bucket.amazon.s3.com -p '/my_path/'
 
## License
Copyright 2013,2014 New York Times

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
