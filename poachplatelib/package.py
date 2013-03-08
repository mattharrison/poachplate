#!/usr/bin/env python
# Copyright (c) 2009 Matt Harrison

import ConfigParser
from contextlib import contextmanager
import datetime
import optparse
import os
import sys


from poachplatelib import meta

DEFAULT_CONFIG = """
[properties]
author : 'FILL IN'
email : 'FILL IN'
version : 0.1
"""

CONFIG_LOC = os.path.expanduser('~/.config/poachplate.ini')
YEAR = datetime.date.today().strftime('%Y')

COPYRIGHT = '# Copyright (c) %(year)s %(author)s'

INIT = '''#!/usr/bin/env python
%(script_copyright)s

import sys
import optparse

import meta

def main(prog_args):
    parser = optparse.OptionParser(version=meta.__version__)
    opt, args = parser.parse_args(prog_args)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

'''


MANIFEST =  """include README
include LICENSE
include INSTALL
"""

TEST = """%(script_copyright)s

import unittest

import %(libname)s

class Test%(libnamecap)s(unittest.TestCase):
    def test_main(self):
        pass

if __name__ == '__main__':
    unittest.main()
"""

SCRIPT = """#!/usr/bin/env python
%(script_copyright)s

import sys

import %(libname)s

if __name__ == '__main__':
    try:
        sys.exit(%(libname)s.main(sys.argv))
    except Exception, e:
        sys.stderr.write('%%s\\n'%%str(e))
        sys.exit(1)

"""

META = """%(script_copyright)s

__version__ = '%(version)s'
__author__ = '%(author)s'
__email__ = '%(email)s'
"""

SETUP = """%(script_copyright)s
#from distutils.core import setup
from setuptools import setup

from %(libname)s import meta

setup(name='%(name)s',
      version=meta.__version__,
      author=meta.__author__,
      description='FILL IN',
      %(script)s
      package_dir={'%(libname)s':'%(libname)s'},
      packages=['%(libname)s'],
)
"""

MAKEFILE = """# variables to use sandboxed binaries
PIP := PIP_DOWNLOAD_CACHE=$${HOME}/.pip_download_cache env/bin/pip
NOSE := env/bin/nosetests
PY := env/bin/python

# -------- Environment --------
# env is a folder so no phony is necessary
env:
	virtualenv env

.PHONY: deps
deps: env packages/.done
	# see http://tartley.com/?p=1423&cpage=1
	$(PIP) install --no-index --find-links=file://$${PWD}/packages -r requirements.txt

packages/.done:
	mkdir packages; \
	$(PIP) install --download packages -r requirements.txt;\
	touch packages/.done

# rm_env isn't a file so it needs to be marked as "phony"
.PHONY: rm_env
rm_env:
	rm -rf env

# --------- Testing ----------
.PHONY: test
test: deps $(NOSE)
	$(NOSE)

# nose depends on the nosetests binary
$(NOSE): packages/.done-nose
	$(PIP) install --upgrade --no-index --find-links=file://$${PWD}/packages nose

packages/.done-nose:
	# need to drop this marker. otherwise it
	# downloads everytime
	$(PIP) install --download packages nose;\
	touch packages/.done-nose

# --------- PyPi ----------

.PHONY: build
build:
	$(PY) setup.py sdist

.PHONY: upload
upload:
	$(PY) setup.py sdist upload

"""

@contextmanager
def push_pop_dir(dirname):
    cur_dir = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(cur_dir)

class _Unset(object):
    """ We need a value to represent unset for configuration.  None
    doesn't really work since the user might want None to be a valid
    value
    """
    pass


def cascade_value(opt=None, opt_name=None, # optparse
                  env_name=None, # os.environ
                  cfg=None, cfg_section=None, cfg_name=None, # ConfigParser
                  default=None):
    """
    Allow a posix style cascading config
    """
    # get from cmd line
    value = _Unset()
    if opt and opt_name:
        try:
            value = opt.__getattr__(opt_name)
        except AttributeError, e:
            pass
    if not isinstance(value, _Unset):
        return value

    # get from env
    if env_name:
        try:
            value = os.environ[env_name]
        except KeyError, e:
            pass
    if not isinstance(value, _Unset):
        return value

    # get from config file
    if cfg and cfg_section and cfg_name:
        try:
            value = cfg.get(cfg_section, cfg_name)
        except ConfigParser.NoOptionError, e:
            pass
    if not isinstance(value, _Unset):
        return value

    return default


def create_config():
    if not os.path.exists(CONFIG_LOC):
        create_file(fout(CONFIG_LOC), DEFAULT_CONFIG)

def create_file(fout, content=None):
    if not content is None:
        fout.write(content)

def fout(name):
    out = open(name, 'w')
    return out

class Package(object):
    def __init__(self, name, libname=None, scriptname=None, opt=None, cfg_loc=None,
                 bin_dir='bin', test_dir='test'):
        self.name = name
        pep8name = self.name.lower()
        self.libname = libname or pep8name+'lib'

        for filename in [pep8name, self.libname]:
            if not filename[0].isalpha():
                raise NameError, '%s should start with alpha character' % filename
        self.bin_dir = bin_dir
        self.scriptname = scriptname or pep8name
        self.scriptpath = """scripts=['%(bin_dir)s/%(file)s'],""" % \
            {'bin_dir':self.bin_dir,'file':self.scriptname} if \
            self.scriptname else ''

        self.test_dir = test_dir

        cfg = None
        if cfg_loc and os.path.exists(cfg_loc):
            cfg = ConfigParser.ConfigParser()
            cfg.read(cfg_loc)

        self.author = cascade_value(opt=opt, opt_name='author',
                                    cfg=cfg, cfg_section='properties', cfg_name='author',
                                    default='FILL IN')
        self.version = cascade_value(opt=opt, opt_name='version',
                                    cfg=cfg, cfg_section='properties', cfg_name='version',
                                    default='0.1')
        self.email = cascade_value(opt=opt, opt_name='email',
                                    cfg=cfg, cfg_section='properties', cfg_name='email',
                                    default='FILL IN')




    def generate(self):
        self._copyright = COPYRIGHT % {'author':self.author,'year':YEAR}
        self._init = INIT  % {'script_copyright':self._copyright}
        self._meta = META % {'version':self.version,
                            'author':self.author,
                            'email':self.email,
                            'script_copyright':self._copyright}
        self._setup = SETUP % {'name':self.name,
                               'script':self.scriptpath,
                               'libname':self.libname,
                               'script_copyright':self._copyright}
        self._requirements = ''
        self._makefile = MAKEFILE
        self._script = SCRIPT % {'libname':self.libname,
                                 'script_copyright':self._copyright}
        self._test = TEST %{'libname':self.libname,
                            'libnamecap':self.libname.capitalize(),
                            'script_copyright':self._copyright}

    def write(self):
        self.generate()
        if os.path.exists(self.name):
            raise NameError, '%s project directory already exists' % self.name

        os.makedirs(self.name)
        with push_pop_dir(self.name):

            os.makedirs(self.libname)
            with open(os.path.join(self.libname, '__init__.py'), 'w') as fout:
                fout.write(self._init)
            with open(os.path.join(self.libname, 'meta.py'), 'w') as fout:
                fout.write(self._meta)
            with open('setup.py', 'w') as fout:
                fout.write(self._setup)
            with open('requirements.txt', 'w') as fout:
                fout.write(self._requirements)
            with open('Makefile', 'w') as fout:
                fout.write(MAKEFILE)

            for fname in ['README', 'LICENSE', 'INSTALL']:
                with open(fname, 'w') as fout:
                    fout.write('FILL IN')

            with open('MANIFEST.in', 'w') as fout:
                fout.write(MANIFEST)

            if self.scriptname:
                # Make a nice non .py script for end users.  It catches
                # exceptions and just prints out the error rather than a stack
                # trace, so as to not scare the end user.
                os.makedirs(self.bin_dir)
                with open(os.path.join(self.bin_dir, self.scriptname), 'w') as fout:
                    fout.write(self._script)

            os.makedirs(self.test_dir)
            with open(os.path.join(self.test_dir, 'test%s.py' % self.libname), 'w') as fout:
                fout.write(self._test)



def main(prog_args):
    usage = """Specify a library name for your script.  If your library name has capital letters
in it, they will be converted to lowercase for package and script names."""
    parser = optparse.OptionParser(usage=usage, version=meta.__version__)
    opt, args = parser.parse_args(prog_args)

    if len(sys.argv) > 1:
        p = Package(sys.argv[1], opt=opt, cfg_loc=CONFIG_LOC)
        p.write()
    else:
        parser.print_help()



if __name__ == '__main__':
    sys.exit(main(sys.argv) or 0)
