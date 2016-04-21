#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re

from setuptools import setup, find_packages


def get_readme():
    """Get the contents of the ``README.rst`` file as a Unicode string."""
    try:
        import pypandoc
        description = pypandoc.convert('README.md', 'rst')
    except (IOError, ImportError):
        description = open('README.md').read()

    return description

def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(directory, *args)


def get_version():
    """Get the version of `package` (by extracting it from the source code)."""
    module_path = get_absolute_path('pip_save', '__init__.py')
    with open(module_path) as handle:
        for line in handle:
            match = re.match(r'^__version__\s*=\s*["\']([^"\']+)["\']$', line)
            if match:
                return match.group(1)
    raise Exception("Failed to extract version from %s!" % module_path)


requirements = [
    'six == 1.9.0',
]

test_requirements = [
]

setup(
    name='pip-save',
    version=get_version(),
    description="A wrapper around pip to add `npm --save` style functionality to pip",
    long_description=get_readme(),
    author="Ritesh Kadmawala",
    author_email='k.g.ritesh@gmail.com',
    url='https://github.com/kgritesh/pip-save',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['pip-save = pip_save.cli:main'],
    },
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='pip-save',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Software Distribution',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
