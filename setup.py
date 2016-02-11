"""initd: module for simplifying creation of initd daemons.

This module provides functionality for starting, stopping and
restarting daemons.  It also provides a simple utility for reading the
command line arguments and determining which action to perform from
them.
"""

from setuptools import setup

doclines = __doc__.splitlines()

setup(
    name = 'django-initd',
    version = '0.0.3',
    py_modules = ['initd', 'daemon_command'],
    platforms = ['POSIX'],

    install_requires = ['django>=1.0'],

    author = 'Daniel Roseman',
    author_email = 'daniel@roseman.org.uk',

    description = doclines[0],
    long_description = '\n'.join(doclines[2:]),

    license = 'http://www.gnu.org/licenses/gpl.html',
    url = 'http://github.com/danielroseman/django-initd',
    test_suite = 'test.test_initd.suite',

    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Boot :: Init',
    ],
)
