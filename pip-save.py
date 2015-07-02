from __future__ import absolute_import
import argparse
import os
import subprocess
import pip
from pip._vendor.packaging.specifiers import Specifier
from pkg_resources import WorkingSet, Requirement, pkg_resources
import ConfigParser

CONFIG_FILE = '.pipconfig'

DEFAULT_OPTIONS = {
    'requirement': 'requirements.txt',
    'use_compatible': False
}


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run Pip Command')
    parser.add_argument('command', help="command to execute")
    parser.add_argument('pkg',
                        help="pkg to be installed/updated/uninstalled")

    parser.add_argument('-r', '--requirement',
                        help='Save requirements to specified requirement file')

    parser.add_argument('--use-compatible', action='store_true',
                        help='Will use the compatible release version '
                             'specifier(~=) for dependencies rather than using '
                             'the default exact version matching specifier(==)')

    return parser


def parse_config(args):

    #http://stackoverflow.com/a/2819788/911557
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
        config = ConfigParser.ConfigParser(DEFAULT_OPTIONS)
        config.readfp(FakeSecHead(open(CONFIG_FILE)))
        return dict(config.items('default', 0, vars=args_dict))

    else:
        config_dict = dict(DEFAULT_OPTIONS)
        config_dict.update(args_dict)

    return config_dict


def execute_pip_command(command, pkg, args):
    pip_cmd = ['pip', command, pkg]
    pip_cmd.extend(args)
    return subprocess.call(pip_cmd)


def parse_package_name(pkgstring):
    req = Requirement.parse(pkgstring)
    return req.project_name.lower()


def get_requirement_str(config_dict, req):
    if not req.specs:
        dist = pkg_resources.working_set.find(req)
        comparator = '~=' if config_dict.get('use_compatible') else '=='
        specs = "%s%s" % (comparator, dist.version)
        req.specifier = Specifier(specs)

    return str(req)


def update_requirements(config_dict, req, command):
    pkg = req.project_name.lower()
    with open(config_dict['requirement'], "a+") as fd:
        requirements = fd.readlines()

        found_requirement = -1
        for index, pkgstring in enumerate(requirements):
            reqpkg = parse_package_name(pkgstring)
            if reqpkg == pkg:
                found_requirement = index

        if command == 'install':
            req_str = get_requirement_str(config_dict, req)
            if found_requirement == -1:
                requirements.append(req_str)
                requirements = sorted(requirements)
            else:
                requirements[found_requirement] = str(req_str)

        elif command == 'uninstall':
            if found_requirement > -1:
                requirements.remove(requirements[found_requirement])

    with open(config_dict['requirement'], "w") as fd:
        for req in requirements:
            fd.write("%s" % req)


def main():
    parser = parse_arguments()

    args, remaining_args = parser.parse_known_args()

    if args.command not in ['install', 'uninstall', 'upgrade']:
        raise NameError("Unsupported command %s" % args.command)

    if args.command == 'upgrade':
        args.command = 'install'
        remaining_args.append('--upgrade')

    pip_output = execute_pip_command(args.command, args.pkg, remaining_args)

    if pip_output != 0:
        return

    config_dict = parse_config(args)

    req = Requirement.parse(args.pkg)

    update_requirements(config_dict, req, args.command)


if __name__ == '__main__':
    main()
