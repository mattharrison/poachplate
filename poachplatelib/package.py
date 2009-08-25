#!/usr/bin/env python
# Copyright (c) 2009 Matt Harrison

import sys
import optparse
import ConfigParser
import os
import datetime

from poachplatelib import meta

DEFAULT_CONFIG = """
[properties]
author : 'FILL IN'
email : 'FILL IN'
version : 0.1
"""

CONFIG_LOC = os.path.expanduser('~/.config/poachplate.ini')
YEAR = datetime.date.today().strftime('%Y')

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
    def __init__(self, name, libname=None, scriptname=None, opt=None, cfg_loc=None):
        self.name = name
        pep8name = self.name.lower()
        self.libname = libname or pep8name+'lib'

        for filename in [pep8name, self.libname]:
            if not filename[0].isalpha():
                raise NameError, '%s should start with alpha character' % filename
        self.scriptname = scriptname or pep8name

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
        if os.path.exists(self.name):
            raise NameError, '%s project directory already exists' % self.name

        os.makedirs(self.name)
        cur_dir = os.getcwd()
        os.chdir(self.name)

        script_copyright = '# Copyright (c) %(year)s %(author)s' % {'author':self.author,'year':YEAR}

        os.makedirs(self.libname)        
        create_file(fout(os.path.join(self.libname, '__init__.py')), '''#!/usr/bin/env python
%(script_copyright)s

import sys
import optparse

import meta

def main(prog_args):
    parser = optparse.OptionParser(version=meta.__version__)
    opt, args = parser.parse_args(prog_args)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

''' % {'script_copyright':script_copyright})

        self.gen_meta(script_copyright)
        self.gen_setup(script_copyright)
        create_file(fout('README'), 'FILL IN')
        create_file(fout('LICENSE'), 'FILL IN')
        create_file(fout('INSTALL'), 'FILL IN')
        create_file(fout('MANIFEST.in'), """include README
include LICENSE
include INSTALL
""")
        self.gen_script(script_copyright)
        self.gen_test(script_copyright)

        os.chdir(cur_dir)

    def gen_test(self, script_copyright):
        os.makedirs('test')
        create_file(fout(os.path.join('test', 'test%s.py' % self.libname)), """%(script_copyright)s

import unittest

import %(libname)s

class Test%(libnamecap)s(unittest.TestCase):
    def test_main(self):
        pass

if __name__ == '__main__':
    unittest.main()
""" %{'libname':self.libname,
      'libnamecap':self.libname.capitalize(),
      'script_copyright':script_copyright})
        

    def gen_script(self, script_copyright):
        """
        Make a nice non .py script for end users.  It catches
        exceptions and just prints out the error rather than a stack
        trace, so as to not scare the end user.
        """
        if self.scriptname:
            os.makedirs('bin')
            create_file(fout(os.path.join('bin', self.scriptname)), """#!/usr/bin/env python
%(script_copyright)s

import sys

import %(libname)s

if __name__ == '__main__':
    try:
        sys.exit(%(libname)s.main(sys.argv))
    except Exception, e:
        sys.stderr.write('%%s\\n'%%str(e))
        sys.exit(1)  

""" % {'libname':self.libname,
       'script_copyright':script_copyright})
        
    def gen_meta(self, script_copyright):
        create_file(fout(os.path.join(self.libname, 'meta.py')),"""%(script_copyright)s

__version__ = '%(version)s'
__author__ = '%(author)s'
__email__ = '%(email)s'
""" % {'version':self.version,
       'author':self.author,
       'email':self.email,
       'script_copyright':script_copyright})

    def gen_setup(self, script_copyright):
        if self.scriptname:
            script = """scripts=['bin/%(file)s'],""" % {'file':self.scriptname}
        else:
            script = ''

        create_file(fout('setup.py'), '''%(script_copyright)s
from distutils.core import setup
#from setuptools import setup

from %(libname)s import meta

setup(name='%(name)s',
      version=meta.__version__,
      author=meta.__author__,
      description='FILL IN',
      %(script)s
      package_dir={'%(libname)s':'%(libname)s'},
      packages=['%(libname)s'],
)
''' % {'name':self.name,
       'script':script,
       'libname':self.libname,
       'script_copyright':script_copyright})


def main(prog_args):
    usage = """Specify a library name for your script.  If your library name has capital letters
in it, they will be converted to lowercase for package and script names."""
    parser = optparse.OptionParser(usage=usage, version=meta.__version__)
    opt, args = parser.parse_args(prog_args)

    if len(sys.argv) > 1:
        p = Package(sys.argv[1], opt=opt, cfg_loc=CONFIG_LOC)
        p.generate()
    else:
        parser.print_help()
        
    

if __name__ == '__main__':
    sys.exit(main(sys.argv) or 0)
    
