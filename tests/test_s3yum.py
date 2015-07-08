#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import logging
import unittest
import sys

from mock import Mock, MagicMock, patch

class TestS3Yum(unittest.TestCase):
    '''Test the cache ab service buddy'''


    def test_fake(self):
        '''Test to ensure that cache is properly invalidated'''

        self.assertTrue(True)

if __name__ == '__main__':

    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()

