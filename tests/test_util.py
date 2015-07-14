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
from mock import (
    Mock,
    MagicMock,
    patch,
    mock_open
    )

from s3yum.util import (
    s3join,
    md5_matches
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

if __name__ == '__main__':

    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

