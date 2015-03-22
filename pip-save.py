from __future__ import absolute_import
import argparse
import subprocess
import pip
from pkg_resources import WorkingSet


def run_pip():
    parser = argparse.ArgumentParser(description='Run Pip Command')
    parser.add_argument('command', help="command to execute")
    parser.add_argument('pkg',
                        help="pkg to be installed/updated/uninstalled")

    args, remaining_args = parser.parse_known_args()

    if args.command == 'upgrade':
        args.command = 'install'
        remaining_args.append('--upgrade')

    pip_cmd = ['pip', args.command, args.pkg]
    pip_cmd.extend(remaining_args)
    pip_output = subprocess.call(pip_cmd)
    if pip_output != 0:
        return

    pkg = args.pkg.strip().split("==")[0].lower()

    with open('requirements.txt', "r") as fd:
        requirements = fd.readlines()

    found_requirement = -1
    for index, req in enumerate(requirements):
        req_split = req.split('==')
        if req_split[0].lower() == pkg:
            found_requirement = index

    if args.command == 'install':
        frozen_requirement = get_frozen_requirement(pkg)
        if found_requirement == -1:
            requirements.append(str(frozen_requirement))
            requirements = sorted(requirements)
        else:
            requirements[found_requirement] = str(frozen_requirement)

    elif args.command == 'uninstall':
        if found_requirement > -1:
            requirements.remove(requirements[found_requirement])

    with open('requirements.txt', "w") as fd:
        for req in requirements:
            fd.write("%s" % req)


def get_frozen_requirement(pkg):
    ws = WorkingSet()
    dists = ws.require(pkg)

    for dist in dists:
        if dist.project_name.lower() == pkg:
            return pip.FrozenRequirement.from_dist(dist, [], [])



if __name__ == '__main__':
    run_pip()
