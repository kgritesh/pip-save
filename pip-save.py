#!/usr/bin/env python

from __future__ import absolute_import
import argparse
from collections import OrderedDict
import os
import subprocess
import operator

from pip._vendor.packaging.specifiers import Specifier
from pip.req import InstallRequirement
from pkg_resources import WorkingSet, Requirement
import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

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

    parser.add_argument('packages', action='append', nargs='*',
                        help="pkg to be installed/upd   ated/uninstalled")

    parser.add_argument('-r', '--requirement',
                        help='Save requirements to specified requirement file')

    parser.add_argument('--use-compatible', action='store_true',
                        help='Will use the compatible release version '
                             'specifier(~=) for dependencies rather than using '
                             'the default exact version matching specifier(==)')

    return parser


def parse_config(args):
    # http://stackoverflow.com/a/2819788/911557
    class FakeSecHead(object):
        def __init__(self, fp):
            self.fp = fp
            self.sechead = '[default]\n'

        def readline(self):
            if self.sechead:
                try:
                    return self.sechead
                finally:
                    self.sechead = None
            else:
                return self.fp.readline()

    args_dict = {key: val for key, val in vars(args).items() if val is not None}
    if os.path.exists(CONFIG_FILE):
        config = configparser.configparser(DEFAULT_OPTIONS)
        config.readfp(FakeSecHead(open(CONFIG_FILE)))
        return dict(config.items('default', 0, vars=args_dict))

    else:
        config_dict = dict(DEFAULT_OPTIONS)
        config_dict.update(args_dict)

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
        for pkg in packages:
            self.update(pkg)

        for pkg in editables:
            self.update(pkg, editable=True)

        self.write_requirement_file()

    def sort_requirements(self):
        return sorted(self.existing_requirements.items(),
                      key=operator.itemgetter(0))

    def find_installed_requirement(self, pkgstring):
        req = Requirement.parse(pkgstring)
        working_set = WorkingSet()
        if not req.specs:
            dist = working_set.find(req)
            comparator = '~=' if self.use_compatible else '=='
            specs = "%s%s" % (comparator, dist.version)
            req.specifier = Specifier(specs)
        return str(req)

    def get_requirement_str(self, insreq):
        req_str = ''
        if insreq.editable:
            req_str += '-e '

        if insreq.link:
            req_str += insreq.link.url
        else:
            req_str += self.find_installed_requirement(insreq.name)

        return req_str

    def write_requirement_file(self):
        with open(self.requirement_file, "w") as fd:
            for _, req in self.sort_requirements():
                req_str = self.get_requirement_str(req)
                fd.write(req_str + '\n')

    @staticmethod
    def parse_requirement(pkgstring, editable=False):
        if editable:
            ins = InstallRequirement.from_editable(pkgstring)
        else:
            ins = InstallRequirement.from_line(pkgstring)
        return ins

    def read_requirements(self):
        with open(self.requirement_file, "r+") as fd:
            for line in fd.readlines():
                editable = line.startswith('-e')
                line = line.replace('-e ', '').strip()
                insreq = self.parse_requirement(line, editable)
                self.existing_requirements[insreq.name.lower()] = insreq

    def update(self, pkgstring, editable=False):
        req = self.parse_requirement(pkgstring, editable)
        req_project_name = req.name.lower()
        existing_req = req_project_name in self.existing_requirements

        if self.command == 'install':
            self.existing_requirements[req_project_name] = req
        else:
            if existing_req:
                del self.existing_requirements[req_project_name]


def main():
    parser = parse_arguments()

    args, remaining_args = parser.parse_known_args()

    if args.command not in ['install', 'uninstall', 'upgrade']:
        raise NameError("Unsupported command %s" % args.command)

    if args.command == 'upgrade':
        args.command = 'install'
        remaining_args.append('--upgrade')

    for editable in args.editables:
        remaining_args.extend(['-e', '{}'.format(editable)])

    packages = args.packages[0]

    remaining_args.extend(packages)

    pip_output = execute_pip_command(args.command, remaining_args)

    if pip_output != 0:
        return

    config_dict = parse_config(args)

    RequirementFileUpdater(config_dict, args.command, packages,
                           args.editables)

    return 0

if __name__ == '__main__':
    sys.exit(main())
