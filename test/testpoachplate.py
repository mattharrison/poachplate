import unittest

from poachplatelib import package

class TestScript(unittest.TestCase):
    def setUp(self):
        self.p = package.Package('test')
        self.p.generate()

    def test_setup(self):
        self.assertEqual(self.p._setup, """# Copyright (c) 2013 FILL IN
from distutils.core import setup
#from setuptools import setup

from testlib import meta

setup(name='test',
      version=meta.__version__,
      author=meta.__author__,
      description='FILL IN',
      scripts=['bin/test'],
      package_dir={'testlib':'testlib'},
      packages=['testlib'],
)
""")

    def test_script(self):
        self.assertEqual(self.p._script, """#!/usr/bin/env python
# Copyright (c) 2013 FILL IN

import sys

import testlib

if __name__ == '__main__':
    try:
        sys.exit(testlib.main(sys.argv))
    except Exception, e:
        sys.stderr.write('%s\\n'%str(e))
        sys.exit(1)

""")

if __name__ == "__main__":
    unittest.main()
