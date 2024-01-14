#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import inspect
import yocto_codename_list as cn
import yvm_git as yvm

SEP1 = "================================================================================"
SEP2 = "--------------------------------------------------------------------------------"

def main():
    parser = argparse.ArgumentParser(
        description="""Search for yocto related content and migrate them
         to the newest common codename.
        """)
    parser.add_argument('-y', '--yes', action='store_true',
                         help="Do not prompt using yes for all answers.")
    action = parser.add_mutually_exclusive_group(required=False)
    action.add_argument('-c', '--codename',
                         help="Changes from searching for newest possible" +
                         " common codename to specified codename.")
    action.add_argument('-m', '--allow_minor', action='store_true',
                         help="Allow different codenames as long as they are" +
                         " the same major version.")
    parser.add_argument('-a', '--all', action='store_true',
                         help="Do not prompts for inclusion of detected folders" +
                         " and include all of them.")
    parser.add_argument('-s', '--simulate', action='store_true',
                         help="Run all checks but do not update branch.")
    parser.add_argument('--include_build_dirs', action='store_true',
                         help="Do not filter out folders with git repos from within a build path.")
    parser.add_argument('path',
                         help="The path to look for yocto content to update.")
    args = parser.parse_args()
    script_directory = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    if not os.path.isdir(args.path):
        print(f"The specified path '{args.path}' is not valid.")
        sys.exit(1)

    if args.codename is not None:
        if args.codename.lower() not in cn.versions:
            print(f"Codename '{args.codename}' is not valid.")
            print("If you believe this to be incorrect, update the yocto_codename_list.py file.")
            sys.exit(1)

    search_result = yvm.get_search_and_ignore(args.path, script_directory, args.include_build_dirs)
    if len(search_result) == 0:
        print(f"No git folders found in '{args.path}'.")
        sys.exit(1)

    branch_collection, current_branches = yvm.get_branches(search_result,
                                                            (args.all or args.yes),
                                                             args.codename)

    print(SEP1)
    if args.codename is not None:
        newest_codename = args.codename.lower()
        incompatable_repos = []
        for key in branch_collection:
            if len(branch_collection[key]) == 0:
                incompatable_repos.append(key)
        if len(incompatable_repos) > 0:
            print(f"Codename '{newest_codename}' not found for repositories in" +
                  f" {incompatable_repos}.")
            sys.exit(1)
        newest_version = cn.versions[newest_codename]
        print(f"Specified codename '{newest_codename}'({newest_version})\n")
    elif args.allow_minor is True:
        target_versions = yvm.find_newest_within_major(branch_collection)
    else:
        newest_codename = yvm.find_newest_common(branch_collection)
        if newest_codename is None:
            print("No common code name found.  Check the paths included.")
            sys.exit(1)
        newest_version = cn.versions[newest_codename]
        print(f"Newest common version found '{newest_codename}'({newest_version})\n")

    if args.allow_minor is True:
        branches_current = {}
        branches_need_update = {}
        for key in target_versions:
            if target_versions[key] == current_branches[key]:
                branches_current[key] = target_versions[key]
            else:
                branches_need_update[key] = target_versions[key]

        yvm.display_branch(branches_current, branches_need_update, current_branches)

    else:
        branches_current, branches_need_update = yvm.at_target_branch(newest_codename,
                                                                      current_branches)
        yvm.display_branch(branches_current, branches_need_update, current_branches)

        if args.simulate is not True and len(branches_need_update) > 0:
            do_update = args.yes
            if do_update is not True:
                print(SEP2)
                do_update = input("Update the branches? [Y]/N: ")
                do_update = do_update in ('', 'y', 'Y')

            if do_update is True:
                for update_dir in branches_need_update:
                    print(f"Updating {update_dir} to {branches_need_update[update_dir]}")
                    subprocess.run(['git', '-C', update_dir, 'checkout',
                                     branches_need_update[update_dir]])
                    subprocess.run(['git', '-C', update_dir, 'pull'])
            else:
                print("Aborting branch change...")

if __name__ == '__main__':
    main()
