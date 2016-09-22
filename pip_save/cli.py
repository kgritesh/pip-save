#!/usr/bin/env python

from __future__ import absolute_import

import argparse
import operator
import os
import subprocess
import sys
from collections import OrderedDict
from six.moves.configparser import ConfigParser

import functools
from pip.req import InstallRequirement
from pkg_resources import WorkingSet, Requirement

DEFAULT_CONFIG_FILE = '.pipconfig'

DEFAULT_OPTIONS = {
    'requirement': 'requirements.txt',
    'use_compatible': False,
    'requirement_dev': '%(requirement)s'
}


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run Pip Command')
    parser.add_argument('command',
                        choices=['install', 'uninstall'],
                        help="command to execute")
    parser.add_argument('-e', '--editable', dest='editables',
                        action='append', default=[],
                        metavar='path/url',
                        help=('Install a project in editable mode (i.e. setuptools '
                              '"develop mode") from a local project path or a '
                              'VCS url.'), )

    parser.add_argument('--config', dest='config_file',
                        default=DEFAULT_CONFIG_FILE,
                        help=(
                            'Config File To be used'
                        ))

    parser.add_argument('--dev', dest='dev_requirement',
                        default=False, action='store_true',
                        help=('Mark the requirement as a dev requirement and hence its '
                              'removed or added to the dev requirement file'))
    return parser


def parse_config(config_file=DEFAULT_CONFIG_FILE):
    if not os.path.exists(config_file):
        config_dict = dict(DEFAULT_OPTIONS)
        config_dict['requirement_dev'] = config_dict['requirement']
        return config_dict

    config_dict = {}
    config = ConfigParser(DEFAULT_OPTIONS)
    config.read(config_file)
    config_dict['requirement'] = config.get('pip-save', 'requirement')

    config_dict['use_compatible'] = config.getboolean('pip-save',
                                                      'use_compatible')

    config_dict['requirement_dev'] = config.get('pip-save', 'requirement_dev')
    return config_dict


def execute_pip_command(command, args):
    pip_cmd = ['pip', command]
    pip_cmd.extend(args)
    return subprocess.call(pip_cmd)


def parse_requirement(pkgstring, comparator='=='):
    ins = InstallRequirement.from_line(pkgstring)
    pkg_name, specs = ins.name, str(ins.specifier)
    if specs:
        return pkg_name, specs

    req = Requirement.parse(pkg_name)
    working_set = WorkingSet()
    dist = working_set.find(req)
    if dist:
        specs = "%s%s" % (comparator, dist.version)

    return req.project_name, specs


def parse_editable_requirement(pkgstring):
    ins = InstallRequirement.from_editable(pkgstring)
    specs = '-e '

    if ins.link:
        return ins.name, specs + str(ins.link)
    else:
        return ins.name, specs + str(ins.specifier)


def sort_requirements(requirements_dict):
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

    return sorted(requirements_dict.items(),
                  key=functools.cmp_to_key(compare))


def read_requirements(requirement_file):
    existing_requirements = OrderedDict()
    with open(requirement_file, "r+") as fd:
        for line in fd.readlines():
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-r'):
                continue
            editable = line.startswith('-e')
            line = line.replace('-e ', '').strip()
            if editable:
                pkg_name, link = parse_editable_requirement(line)
                existing_requirements[pkg_name] = link
            else:
                pkg_name, specifier = parse_requirement(line)
                existing_requirements[pkg_name] = '{}{}'.format(pkg_name,
                                                                specifier)
    return existing_requirements


def write_requirements(requirement_file, requirements_dict):
    with open(requirement_file, "w") as fd:
        for _, req_str in sort_requirements(requirements_dict):
            fd.write('{}\n'.format(req_str))


def update_requirement_file(config_dict, command, packages, editables,
                            dev_requirement=False):
    requirement_file = config_dict['requirement_dev'] \
        if dev_requirement else config_dict['requirement']

    existing_requirements = read_requirements(requirement_file)
    update_requirements = OrderedDict()

    for pkg in packages:
        pkg_name, specs = parse_requirement(pkg)
        update_requirements[pkg_name] = '{}{}'.format(pkg_name, specs)

    for pkg in editables:
        pkg_name, link = parse_editable_requirement(pkg)
        update_requirements[pkg_name] = link

    if command == 'install':
        existing_requirements.update(update_requirements)
    else:
        for key in update_requirements:
            if key in existing_requirements:
                del existing_requirements[key]

    write_requirements(requirement_file, existing_requirements)


def main():
    parser = parse_arguments()

    args, remaining_args = parser.parse_known_args()

    packages = []
    for arg in remaining_args:
        if not arg.startswith('-'):
            packages.append(arg)

    for editable in args.editables:
        remaining_args.extend(['-e', '{}'.format(editable)])

    pip_output = execute_pip_command(args.command, remaining_args)

    if pip_output != 0:
        return

    config_dict = parse_config(args.config_file)

    update_requirement_file(config_dict, args.command, packages,
                            args.editables, args.dev_requirement)

    return 0

if __name__ == '__main__':
    sys.exit(main())
