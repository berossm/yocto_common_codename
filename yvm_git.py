import yocto_codename_list as cn
import subprocess
import os
import math


def default_yes(input_answer):
    return (input_answer == "" or input_answer == "y" or input_answer == "Y")

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

def find_newest_common(branch_collection):
    remaining = cn.names
    got_result = False
    for key in branch_collection:
        remaining = list(set(remaining) & set(branch_collection[key]))
    best_index = 0
    for distro in remaining:
        if distro in cn.names[best_index:]:
            result_index = cn.names.index(distro, best_index)
            best_index = result_index
            got_result = True
    if got_result:
        return cn.names[best_index]
    else:
        return None

def find_newest_within_major(branch_collection):
    version_collection = {}
    max_major = {}
    best_max = cn.last_major
    target_branches ={}
    for key in branch_collection:
        max_vers = [0] * (cn.last_major + 1)
        max_branch = [""] * (cn.last_major + 1)
        for branch in branch_collection[key]:
            branch_ver = cn.versions[branch]
            branch_index = math.floor(branch_ver)
            if branch_ver > max_vers[branch_index]:
                max_vers[branch_index] = branch_ver
                max_branch[branch_index] = branch
        version_collection[key] = max_branch
        for major in range(cn.last_major, -1, -1):
            if max_branch[major] != '':
                max_major[key] = major
                if major < best_max:
                    best_max = major
                break
    for key in branch_collection:
        target_branches[key] = version_collection[key][best_max]
        
    return target_branches
    
def at_target_branch(codename, current_branches):
    current = {}
    to_update = {}
    for key in current_branches:
        if current_branches[key] == codename:
            current[key] = codename
        else:
            to_update[key] = codename
    return current, to_update

def display_branch(branches_current, branches_need_update, current_branches):
    if len(branches_current) > 0:
        print(f"Current Branches:")
        for key in branches_current:
            branch_name = branches_current[key]
            branch_version = cn.versions[branches_current[key]]
            print(f"    {key} on branch '{branch_name}'({branch_version})")
    print("--------------------------------------------------------------------------------")
    if len(branches_need_update) > 0:
        print(f"Branches to Change:")
        for key in branches_need_update:
            current_branch = current_branches[key]
            current_version = cn.versions[current_branch]
            target_branch = branches_need_update[key]
            target_version = cn.versions[target_branch]
            print(f"    {key} on branch '{current_branch}'({current_version}) update to '{target_branch}'({target_version})")
    

if __name__ == '__main__':
    short_name = os.path.basename(__file__)
    print(f"This python file ({short_name}) is not intended to be executed directly.")
    exit(1)