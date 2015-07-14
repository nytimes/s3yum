#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""@package s3yum
"""
__author__ =  'NYTD Fabrik Team'

import pkg_resources
try:
    __version__ = pkg_resources.get_distribution('s3yum').version
except pkg_resources.DistributionNotFound:
    __version__ = '{0} local source'.format(__name__)

__all__ = [
    's3yum_cli',
    'util'
    ]
# EOF

