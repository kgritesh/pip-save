#!/usr/bin/env python

from __future__ import absolute_import

import argparse
import operator
import subprocess
import sys
from collections import OrderedDict
from configparser import ConfigParser

import functools
from pip.req import InstallRequirement
from pkg_resources import WorkingSet, Requirement

CONFIG_FILE = '.pipconfig'

DEFAULT_OPTIONS = {
    'requirement': 'requirements.txt',
    'use_compatible': False
}


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run Pip Command')
    parser.add_argument('command', help="command to execute")
    parser.add_argument('-e', '--editable', dest='editables',
                        action='append', default=[],
                        metavar='path/url',
                        help=('Install a project in editable mode (i.e. setuptools '
                            '"develop mode") from a local project path or a VCS url.'), )
    return parser


def parse_config():
    config_dict = {}
    config = ConfigParser(DEFAULT_OPTIONS)
    config.read(CONFIG_FILE)
    config_dict['requirement'] = config.get('pip-save', 'requirement')

    config_dict['use_compatible'] = config.getboolean('pip-save',
                                                      'use_compatible')
    return config_dict


def execute_pip_command(command, args):
    pip_cmd = ['pip', command]
    pip_cmd.extend(args)
    return subprocess.call(pip_cmd)


class RequirementFileUpdater(object):

    def __init__(self, config_dict, command, packages, editables):
        self.requirement_file = config_dict['requirement']
        self.use_compatible = config_dict.get('use_compatible', False)
        self.command = command
        self.existing_requirements = OrderedDict()
        self.read_requirements()
        self.current_packages = []

        for pkg in packages:
            self.update(pkg)

        for pkg in editables:
            self.update(pkg, editable=True)

        self.write_requirement_file()

    def sort_requirements(self):
        def compare(pkg1, pkg2):
            name1, req_str1 = pkg1
            name2, req_str2 = pkg2

            if req_str2.startswith('-e'):
                return -1
            elif req_str1.startswith('-e'):
                return 1
            elif name1.lower() < name2.lower():
                return -1
            else:
                return 1

        return sorted(self.existing_requirements.items(),
                      key=functools.cmp_to_key(compare))

    def find_installed_requirement(self, pkgstring):
        req = Requirement.parse(pkgstring)
        working_set = WorkingSet()
        if not req.specs:
            dist = working_set.find(req)
            if not dist:
                specs = None
            else:
                comparator = '~=' if self.use_compatible else '=='
                specs = "%s%s" % (comparator, dist.version)
        else:
            specs = str(req.specifier)

        return req.project_name, specs

    def write_requirement_file(self):
        with open(self.requirement_file, "w") as fd:
            for _, req_str in self.sort_requirements():
                fd.write('{}\n'.format(req_str))

    @staticmethod
    def parse_requirement(pkgstring, editable=False):
        if editable:
            ins = InstallRequirement.from_editable(pkgstring)
        else:
            ins = InstallRequirement.from_line(pkgstring)

        specs = '-e ' if editable else ''

        if ins.link:
            return ins.name, specs + str(ins.link)
        else:
            return ins.name, specs + str(ins.specifier)

    def read_requirements(self):
        with open(self.requirement_file, "r+") as fd:
            for line in fd.readlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                editable = line.startswith('-e')
                line = line.replace('-e ', '').strip()
                pkg_name, specifier = self.parse_requirement(line, editable)
                if editable:
                    self.existing_requirements[pkg_name] = specifier
                else:
                    self.existing_requirements[pkg_name] = '{}{}'.format(pkg_name, specifier)

    def update(self, pkgstring, editable=False):

        if not editable and self.command == 'install':
            pkg_name, specs = self.find_installed_requirement(pkgstring)
            req_str = '{}{}'.format(pkg_name, specs)
        else:
            pkg_name, specs = self.parse_requirement(pkgstring, editable)
            req_str = specs

        if self.command == 'install':
            self.existing_requirements[pkg_name] = req_str
        else:
            self.existing_requirements.pop(pkg_name, None)


def main():
    parser = parse_arguments()

    args, remaining_args = parser.parse_known_args()

    if args.command not in ['install', 'uninstall', 'upgrade']:
        raise NameError("Unsupported command %s" % args.command)

    packages = []
    for arg in remaining_args:
        if not arg.startswith('-'):
            packages.append(arg)

    for editable in args.editables:
        remaining_args.extend(['-e', '{}'.format(editable)])

    pip_output = execute_pip_command(args.command, remaining_args)

    if pip_output != 0:
        return

    config_dict = parse_config()

    RequirementFileUpdater(config_dict, args.command, packages,
                           args.editables)

    return 0

if __name__ == '__main__':
    sys.exit(main())
