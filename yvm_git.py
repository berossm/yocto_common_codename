import yocto_codename_list as cn
import subprocess
import os


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
    
def at_target_branch(codename, current_branches):
    current = []
    to_update = []
    for key in current_branches:
        if current_branches[key] == codename:
            current.append(key)
        else:
            to_update.append(key)
    return current, to_update