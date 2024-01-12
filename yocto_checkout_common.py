#!/usr/bin/env python3

import yocto_codename_list as cn
import yvm_git as yvm
import subprocess
import argparse
import os
import inspect


def main():
    parser = argparse.ArgumentParser(description="Search for yocto related content and migrate them to the newest common codename.")
    parser.add_argument('-y', '--yes', action='store_true', help="Do not prompt using yes for all answers.")
    parser.add_argument('-c', '--codename', help="Changes from searching for newest possible common codename to specified codename.")
    parser.add_argument('-a', '--all', action='store_true', help="Do not prompts for inclusion of detected folders and include all of them.")
    parser.add_argument('-s', '--simulate', action='store_true', help="Run all checks but do not update branch.")
    parser.add_argument('--include_build_dirs', action='store_true', help="Do not filter out folders with git repos from within a build path.")
    parser.add_argument('path', help="The path to look for yocto content to update.")
    args = parser.parse_args()
    script_directory = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    
    if not os.path.isdir(args.path):
        print(f"The specified path '{args.path}' is not valid.")
        exit(1)
    
    if args.codename is not None:
        if args.codename.lower() not in cn.names:
            print(f"Codename '{args.codename}' is not valid.")
            print("If you believe this to be incorrect, update the yocto_codename_list.py file.")
            exit(1)
    
    search_result = yvm.get_search_and_ignore(args.path, script_directory, args.include_build_dirs)
    if len(search_result) == 0:
        print(f"No git folders found in '{args.path}'.")
        exit(1)
    
    branch_collection, current_branches = yvm.get_branches(search_result, (args.all or args.yes), args.codename)

    print("================================================================================")
    if args.codename is None:
        newest_codename = yvm.find_newest_common(branch_collection)
        if newest_codename is None:
            print("No common code name found.  Check the paths included.")
            exit(1)
        newest_version = cn.versions[newest_codename]
        print(f"Newest common version found '{newest_codename}'({newest_version})\n")
    else:
        newest_codename = args.codename.lower()
        incompatable_repos = []
        for key in branch_collection:
            if len(branch_collection[key]) == 0:
                incompatable_repos.append(key)
        if len(incompatable_repos) > 0:        
            print(f"Codename '{newest_codename}' not found for repositories in {incompatable_repos}.")
            exit(1)
        newest_version = cn.versions[newest_codename]
        print(f"Specified codename '{newest_codename}'({newest_version})\n")

    branches_current, branches_need_update = yvm.at_target_branch(newest_codename, current_branches)

    branch_cur_str = ", ".join(branches_current)
    branch_update_str = ", ".join(branches_need_update)
    if len(branches_current) > 0:
        print(f"Branches in ({branch_cur_str}) are already at {newest_codename}.")
    if len(branches_need_update) > 0:
        if args.simulate == True:
            print(f"Branches in ({branch_update_str}) would need to be updated to {newest_codename}({newest_version})")
        else:
            do_update = args.yes
            if do_update != True:
                print("--------------------------------------------------------------------------------")
                do_update = input(f"Update the branches for ({branch_update_str}) to {newest_codename}({newest_version})? [Y]/N: ")
                do_update = yvm.default_yes(do_update)
            
            if do_update == True:
                print(f"Updating to '{newest_codename}' branch...")
                for update_dir in branches_need_update:
                    print(f"{update_dir} {newest_codename}")                
                    subprocess.run(['git', '-C', update_dir, 'checkout', newest_codename])
                    subprocess.run(['git', '-C', update_dir, 'pull'])
            else:
                print("Aborting branch change...")

if __name__ == '__main__':
    main()
