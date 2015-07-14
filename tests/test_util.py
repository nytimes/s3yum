#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
Test module for s3yum.util
"""

import logging
import unittest
import sys
import io
import hashlib
import datetime
from mock import (
    Mock,
    MagicMock,
    patch,
    mock_open
    )

from s3yum.util import (
    s3join,
    md5_matches,
    s3time_to_datetime,
    )


class TestS3YumUtil(unittest.TestCase):
    """
    Test s3yum utility methods
    """

    def test_s3join(self):
        """
        Verify that s3 pathing is assembled correctly
        """
        self.assertEqual(s3join('a','b','c'),'a/b/c')
        # Double slashes should become single slashes:
        self.assertEqual(s3join('a/','/b/','/c'),'a/b/c')
        # Verify that trailing / is preserved:
        self.assertEqual(s3join('a','b','c/'),'a/b/c/')
        return

    def test_md5_matching(self):
        """
        Verify that md5 matching works properly
        """
        filepath = 'my/random/file'
        file_contents = 'Random file contents'
        checksum = hashlib.md5(file_contents).hexdigest()

        m = MagicMock(spec=file,
            return_value=io.BytesIO(file_contents))
        with patch('s3yum.util.open', m, create=True):
            self.assertTrue(md5_matches(filepath,checksum))

        m.assert_called_once_with(filepath, 'r')
        return

    def test_s3_timestamp(self):
        """
        Verify that both kinds of s3 timestamps are handled properly
        """
        ts1 = 'Wed, 12 Oct 2009 17:50:00 GMT'
        self.assertEqual(s3time_to_datetime(ts1),
            datetime.datetime(2009,10,12,17,50))

        ts2 = '2015-07-08T14:50:48.000Z'
        self.assertEqual(s3time_to_datetime(ts2),
            datetime.datetime(2015,7,8,14,50,48))
        return


if __name__ == '__main__':

    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

