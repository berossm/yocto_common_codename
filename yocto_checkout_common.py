#!/usr/bin/env python3

import yocto_codename_list as cn
import subprocess
import argparse
import os
import inspect

def get_search_and_ignore(path, script_path, keep_all=False):
    search_result = subprocess.check_output(['find', path, '-name', '.git', '-type', 'd', '-prune']).decode('utf-8').split()
    dir_result = []
    drop_dirs = []
    
    for search_dir in search_result:
        repo_dir = search_dir.rstrip('.git')  
        dir_result.append(repo_dir)
        if "build" in search_dir and keep_all != True:
            drop_dirs.append(repo_dir)
        if os.path.abspath(repo_dir) == os.path.abspath(script_path):
            drop_dirs.append(repo_dir)
    
    for to_drop in drop_dirs:
        dir_result.remove(to_drop)
        
    return dir_result

def get_branches(search_result, include_all=False, codename_override=None):    
    branch_collection = {}
    current_branches = {}
    for repo_dir in search_result:
        include_this_repo = include_all                 
        repo_url = subprocess.check_output(['git', '-C', repo_dir, 'config', '--get', 'remote.origin.url']).decode('utf-8').split()[0]
        if include_this_repo != True:
            include_url = input(f"Include {repo_dir} ({repo_url})? [Y]/N: ")
            include_this_repo = default_yes(include_url)
        if include_this_repo == True:
            branch_list = subprocess.check_output(['git', '-C', repo_dir, 'branch', '-r']).decode('utf-8').split()
            branch_list.remove("->")
            release_list = []            
            for branch in branch_list:
                split_branch = branch.split("/")
                branch_element = split_branch[1]
                if codename_override is None:
                    if branch_element in cn.names:
                        release_list.append(branch_element)
                else:
                    if branch_element == codename_override.lower():
                        release_list.append(branch_element)
            branch_collection[repo_dir] = release_list
            branch_list = subprocess.check_output(['git', '-C', repo_dir, 'branch']).decode('utf-8').split()
            current_branch = branch_list[branch_list.index('*')+1]
            current_branches[repo_dir] = current_branch
    return branch_collection, current_branches

def find_newest_common(distros, branch_collection):
    remaining = distros
    got_result = False
    for key in branch_collection:
        remaining = list(set(remaining) & set(branch_collection[key]))
    best_index = 0
    for distro in remaining:
        if distro in distros[best_index:]:
            result_index = distros.index(distro, best_index)
            best_index = result_index
            got_result = True
    if got_result:
        return distros[best_index]
    else:
        return None

def default_yes(input_answer):
    return (input_answer == "" or input_answer == "y" or input_answer == "Y")

def at_target_branch(codename, current_branches):
    current = []
    to_update = []
    for key in current_branches:
        if current_branches[key] == codename:
            current.append(key)
        else:
            to_update.append(key)
    return current, to_update

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
    
    search_result = get_search_and_ignore(args.path, script_directory, args.include_build_dirs)
    if len(search_result) == 0:
        print(f"No git folders found in '{args.path}'.")
        exit(1)
    
    branch_collection, current_branches = get_branches(search_result, (args.all or args.yes), args.codename)

    print("================================================================================")
    if args.codename is None:
        newest_codename = find_newest_common(cn.names, branch_collection)
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

    branches_current, branches_need_update = at_target_branch(newest_codename, current_branches)

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
                do_update = default_yes(do_update)
            
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
