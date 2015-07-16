#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
Test module for s3yum.util
"""

import logging
import unittest
import sys
import datetime
from mock import (
    MagicMock,
    patch,
    )

from s3yum.s3yum_types import S3YumContext
from s3yum.s3yum_cli import should_download


class TestS3YumCliDownloads(unittest.TestCase):
    """
    Test s3yum command line interface functions
    """

    #-----------------------------
    # Download: True
    #-----------------------------
    def test_force_download(self):
        """
        Download: --force-download causes unconditional file downloads
        """
        item = MagicMock()
        filepath = '/some/file'
        self.assertTrue(should_download(item, filepath, True))

    def test_download_missing(self):
        """
        Download: Missing files are downloaded
        """
        item = MagicMock()
        filepath = '/path/to/a/missing/file.rpm'
        with patch('os.path.exists',MagicMock(return_value=False)):
            self.assertTrue(should_download(item, filepath, False))
        return

    def test_md5_diff_remote_newer(self):
        """
        Download: md5 differs, remote is newer
        """
        item = MagicMock()
        filepath = '/path/to/a/missing/file.rpm'
        with patch('os.path.exists',MagicMock(return_value=True)), \
             patch('s3yum.s3yum_cli.mtime_as_datetime',
                    MagicMock(return_value=datetime.datetime(2014,1,1))), \
             patch('s3yum.s3yum_cli.s3time_as_datetime',
                    MagicMock(return_value=datetime.datetime(2015,1,1))), \
             patch('s3yum.s3yum_cli.md5_matches',
                   MagicMock(return_value=False)):
            self.assertTrue(should_download(item, filepath, False))
        return

    #-----------------------------
    # Download: False
    #-----------------------------
    def test_md5_eq_mtime_eq(self):
        """
        Don't Download: Skip identical files and timestamps
        """
        item = MagicMock()
        filepath = '/path/to/a/missing/file.rpm'
        with patch('os.path.exists',MagicMock(return_value=True)), \
             patch('s3yum.s3yum_cli.mtime_as_datetime',
                    MagicMock(return_value=datetime.datetime(2015,1,1))), \
             patch('s3yum.s3yum_cli.s3time_as_datetime',
                    MagicMock(return_value=datetime.datetime(2015,1,1))), \
             patch('s3yum.s3yum_cli.md5_matches', MagicMock(return_value=True)):
            self.assertFalse(should_download(item, filepath, False))
        return

    def test_md5_eq_remote_newer(self):
        """
        Don't Download: identical md5, remote newer
        """
        item = MagicMock()
        filepath = '/path/to/a/missing/file.rpm'
        with patch('os.path.exists',MagicMock(return_value=True)), \
             patch('s3yum.s3yum_cli.mtime_as_datetime',
                    MagicMock(return_value=datetime.datetime(2014,1,1))), \
             patch('s3yum.s3yum_cli.s3time_as_datetime',
                    MagicMock(return_value=datetime.datetime(2015,1,1))), \
             patch('s3yum.s3yum_cli.md5_matches', MagicMock(return_value=True)):
            self.assertFalse(should_download(item, filepath, False))
        return

    def test_md5_eq_local_newer(self):
        """
        Don't Download: identical md5, local newer
        """
        item = MagicMock()
        filepath = '/path/to/a/missing/file.rpm'
        with patch('os.path.exists',MagicMock(return_value=True)), \
             patch('s3yum.s3yum_cli.mtime_as_datetime',
                    MagicMock(return_value=datetime.datetime(2015,1,1))), \
             patch('s3yum.s3yum_cli.s3time_as_datetime',
                    MagicMock(return_value=datetime.datetime(2014,1,1))), \
             patch('s3yum.s3yum_cli.md5_matches', MagicMock(return_value=True)):
            self.assertFalse(should_download(item, filepath, False))
        return

    def test_md5_diff_local_newer(self):
        """
        Don't Download: md5 differs, local is newer
        """
        item = MagicMock()
        filepath = '/path/to/a/missing/file.rpm'
        with patch('os.path.exists',MagicMock(return_value=True)), \
             patch('s3yum.s3yum_cli.mtime_as_datetime',
                    MagicMock(return_value=datetime.datetime(2015,1,1))), \
             patch('s3yum.s3yum_cli.s3time_as_datetime',
                    MagicMock(return_value=datetime.datetime(2014,1,1))), \
             patch('s3yum.s3yum_cli.md5_matches',
                   MagicMock(return_value=False)):
            self.assertFalse(should_download(item, filepath, False))
        return

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

