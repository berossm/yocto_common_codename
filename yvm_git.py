import os
import sys
import subprocess
import math
import yocto_codename_list as cn


def get_search_and_ignore(path, script_path, keep_all=False):
    search_result = subprocess.check_output(['find', path, '-name', '.git', '-type', 'd', '-prune'])
    search_result = search_result.decode('utf-8').split()
    dir_result = []
    drop_dirs = []

    for search_dir in search_result:
        repo_dir = search_dir.rstrip('.git')
        dir_result.append(repo_dir)
        if "build" in search_dir and keep_all is True:
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
        repo_url_args = ['git', '-C', repo_dir, 'config', '--get', 'remote.origin.url']
        repo_url = subprocess.check_output(repo_url_args).decode('utf-8').split()[0]
        if include_this_repo is not True:
            include_url = input(f"Include {repo_dir} ({repo_url})? [Y]/N: ")
            include_this_repo = include_url in ('', 'y', 'Y')
        if include_this_repo is True:
            branch_list = subprocess.check_output(['git', '-C', repo_dir, 'branch', '-r'])
            branch_list = branch_list.decode('utf-8').split()
            branch_list.remove("->")
            release_list = []
            for branch in branch_list:
                branch_element = branch.split("/")[1]
                if codename_override is None:
                    if branch_element in cn.versions:
                        release_list.append(branch_element)
                else:
                    if branch_element == codename_override.lower():
                        release_list.append(branch_element)
            branch_collection[repo_dir] = release_list
            branch_list = subprocess.check_output(['git', '-C', repo_dir, 'branch'])
            branch_list = branch_list.decode('utf-8').split()
            current_branch = branch_list[branch_list.index('*')+1]
            current_branches[repo_dir] = current_branch
    return branch_collection, current_branches

def find_newest_common(branch_collection):
    remaining = []
    for key in cn.versions:
        remaining.append(key)
    for key in branch_collection:
        remaining = list(set(remaining) & set(branch_collection[key]))
    newest_distro = None
    newest_version = 0.0
    for distro in remaining:
        if distro in cn.versions:
            if cn.versions[distro] > newest_version:
                newest_distro = distro
                newest_version = cn.versions[distro]
    return newest_distro

def find_newest_within_major(branch_collection):
    version_collection = {}
    max_major = {}
    best_max = cn.LAST_MAJOR
    target_branches ={}
    for key in branch_collection:
        max_vers = [0] * (cn.LAST_MAJOR + 1)
        max_branch = [""] * (cn.LAST_MAJOR + 1)
        for branch in branch_collection[key]:
            branch_ver = cn.versions[branch]
            branch_index = math.floor(branch_ver)
            if branch_ver > max_vers[branch_index]:
                max_vers[branch_index] = branch_ver
                max_branch[branch_index] = branch
        version_collection[key] = max_branch
        for major in range(cn.LAST_MAJOR, -1, -1):
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
    """This takes the branch information and displays it in a clean format.
    
    Parameters
        ----------
        branches_current : dic
            Dictionary using the local path as key and with the distro codename as the value for
            branches that do not need to be modified.
        branches_need_update : dic 
            Dictionary using the local path as key and with the distro codename as the value for
            branches that need to be modified.
        current_branches : dic
            Dictionary using the local path as key and with the distro codename as the value with
            the current codename.
    """

    if len(branches_current) > 0:
        print("Current Branches:")
        for key in branches_current:
            branch_name = branches_current[key]
            branch_version = cn.versions[branches_current[key]]
            print(f"    {key} on branch '{branch_name}'({branch_version})")
    print("--------------------------------------------------------------------------------")
    if len(branches_need_update) > 0:
        print("Branches to Change:")
        for key in branches_need_update:
            current_branch = current_branches[key]
            current_version = cn.versions[current_branch]
            target_branch = branches_need_update[key]
            target_version = cn.versions[target_branch]
            print(f"    {key} on branch '{current_branch}'({current_version}) update to" +
                  f" '{target_branch}'({target_version})")

if __name__ == '__main__':
    short_name = os.path.basename(__file__)
    print(f"This python file ({short_name}) is not intended to be executed directly.")
    sys.exit(1)
