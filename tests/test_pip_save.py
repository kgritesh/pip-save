#!/usr/bin/env python

from __future__ import absolute_import
import os
import mock
import functools

from pip import get_installed_distributions
from six.moves.configparser import ConfigParser
from pip_save.cli import parse_config, parse_requirement
from pip.operations.freeze import freeze


def get_installed_packages():
    installed_packages = []
    for line in freeze:
        installed_packages.append(line)

os.chdir(os.path.abspath(os.path.dirname(__file__)))

INSTALLED_PACKAGES = get_installed_distributions()


def prepare_config_file(config_options):

    def read(config_parser, config_file):
        config_parser.add_section('pip-save')
        for key, value in config_options.items():
            config_parser.set('pip-save', key, str(value))

        return config_parser

    return read


def test_parse_config_file_not_exists():
    default_options = {
        'requirement': 'requirements.txt',
        'use_compatible': False,
        'requirement_dev': 'requirements.txt'
    }

    config_dict = parse_config('xyz.txt')

    assert config_dict == default_options


def test_parse_config_with_requirements_dev():
    config_dict = parse_config('fixtures/default_config')
    assert config_dict == {
        'requirement': 'requirements.txt',
        'use_compatible': False,
        'requirement_dev': 'requirements_dev.txt'
    }


def test_parse_config_without_requirements_dev():
    config_dict = parse_config('fixtures/config_without_requirement_dev')
    assert config_dict == {
        'requirement': 'requirements.txt',
        'use_compatible': False,
        'requirement_dev': 'requirements.txt',
    }


def test_parse_requirement_installed_package_name():
    pkg = INSTALLED_PACKAGES[0]
    pkgname, specs = parse_requirement(pkg.key)
    assert pkgname == pkg.key
    assert specs == '=={}'.format(pkg.version)


def test_parse_requirement_installed_with_specifier():
    pkg = INSTALLED_PACKAGES[-1]
    pkgstring = '{}~={}'.format(pkg.key, pkg.version)
    pkgname, specs = parse_requirement(pkgstring)
    assert pkgname == pkg.key
    assert specs == '~={}'.format(pkg.version)


def test_parse_requirement_uninstalled_without_specifier():
    pkgname, specs = parse_requirement('xyz')
    assert pkgname == 'xyz'
    assert specs is ''


def test_parse_requirement_uninstalled_with_specifier():
    pkgname, specs = parse_requirement('xyz==1.0.2')
    assert pkgname == 'xyz'
    assert specs == '==1.0.2'



