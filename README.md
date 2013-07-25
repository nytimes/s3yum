# s3yum

## Introduction
A tool for maintaining private yum repos in s3 allowing access via a smart proxy 

## Overview

 * A developer with AWS credentials places a set of RPMs in a local directory.
 * The developer uses s3yum to maintain a copy of the RPMs in a bucket in S3; corresponding yum metadata is transparently maintained by s3yum.
 * The S3 bucket is private; access is allowed using signed URL's.
 * The developer creates an IAM role and adds a policy allowing access to the S3 bucket.
 * Instances started with that role may use it to sign requests for bucket access.
 * A config file is deployed to /etc/yum/repos.d on the instance which directs yum to the S3 bucket.
 * The config file also specifies a proxy for requests to S3.
 * The yum_proxyd service retrieves the IAM Role metadata for the instance from AWS.
 * When yum_proxyd receives a request from yum it signs the requested URL with temporary credentials from the IAM Role.
 * The download then completes using the URL with temporary access credentials appended in the query string of the URI.
 
## Status
Experimental

## License
Copyright 2013 New York Times

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.