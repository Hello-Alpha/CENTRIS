# -*- coding: utf-8 -*-


from fileinput import filename
import os
import errno
import requests
import click

from pkg_resources import Requirement


_GENERIC_ADDRESS = "https://pypi.org/pypi/{package}/json"

def build_package_cache(settings, package):
    """Download all package versions from PyPI for specified package."""

    pkg_urls, pkg_dates = resolve_url_list(settings, package)
    if pkg_urls == None:
        return None
    total_entries = len(pkg_urls)

    if (total_entries == 0):
        return None
    else:
        dates = ''
        index = 0
        with click.progressbar(length=total_entries, width=0, label='') as bar:
            for (project_name, file_name, url) in pkg_urls:
                bar.label = "{:32s}".format(file_name)
                target_folder = get_cache_subfolder(settings, project_name)
                target_file = os.path.join(target_folder, file_name)
                dates += file_name + ' ' + pkg_dates[index] + '\n'
                index += 1
                download_package(url, target_file)

                bar.update(1) # advance status bar
        with open(os.path.join(target_folder, 'date.txt'), 'w') as date:
            date.write(dates)
        return None


def resolve_url_list(settings, package):
    """Build a url list for packages matching the specifications."""

    requires = Requirement(package)

    package_addr = _GENERIC_ADDRESS.format(package=requires.name)
#    while flag == False:
    try:
        package_request = requests.get(package_addr)
    except:
        print('Failed request for %s'%package)
        with open('redo.log', 'a') as redo:
            redo.write(package + '\n')
        return None, None

    if package_request.status_code >= 400 or package_request.status_code == 104:
        print('Invalid package %s'%package)
        return [], []
    # package_request.raise_for_status()  # raise if response is 4xx/5xx
    try:
        package_data = package_request.json()
    except:
        print('Decode json failed')
        package_data = {}
        package_data["releases"] = {}
        pass

    all_versions = package_data["releases"].keys()
    wanted_versions = [v for v in all_versions if (requires.__contains__(v))]

    url_list = []
    accepted_types = settings['packagetypes']
    date_list = []
    for version in wanted_versions:
        packages_for_version = package_data['releases'].get(version)
        for package in packages_for_version:
            if (package_is_valid(settings, package)):
                file_name = str(package.get('filename'))  # file name
                url = str(package.get('url'))             # url
                project_name = str(requires.name)         # sub-folder in cache
                url_list.append((project_name, file_name, url))
                # print(package.get('upload_time'))
                date_list.append(package.get('upload_time'))
            else:
                continue

    return url_list, date_list


def package_is_valid(settings, package):
    """Check if package matches the defined specifications."""

    valid_types = settings['packagetypes']
    valid_py_vers = settings['pyversions']
    valid_platforms = settings['platforms']

    ptype = str(package.get('packagetype'))
    fname = str(package.get('filename'))
    if (ptype in valid_types):
        if (ptype == 'sdist'):  # nothing to match for sources
            return True
        elif (ptype in ['bdist_wheel']):
            (pyvers, platform) = parse_filename(fname)
            # check if package matches specified versions match
            if (valid_py_vers is None):
                version_matches = True
            else:
                version_matches = any([(_ in pyvers) for _ in valid_py_vers])
            # check if package matches specified platforms
            if (valid_platforms is None):
                platform_matches = True
            else:
                platform_matches = any([(_ in platform) for _ in valid_platforms])
            # return True only if all specifiers match
            return (version_matches and platform_matches) 
        else:
            raise NotImplementedError
    else:
        return False


def parse_filename(filename):
    """Parse python and platform according to PEP 427 for wheels."""

    stripped_filename = filename.strip(".whl")
    try:
        proj, vers, build, pyvers, abi, platform = stripped_filename.split("-")
    except ValueError:  # probably no build version available
        proj, vers, pyvers, abi, platform = stripped_filename.split("-")
    
    return (pyvers, platform) 
    

def download_package(url, target_file):
    """Download contents at url-address to file."""

    if (not os.path.exists(target_file)):
        flag = False
        while flag == False:
            try:
                package_request = requests.get(url, allow_redirects=True)
                flag = True
            except:
                pass
        if package_request.status_code >= 400:
            print('Skipped invalid package: %s'%url)
            pass
        # package_request.raise_for_status()  # raise if response is 4xx/5xx
        with open(target_file, 'wb') as target:
            target.write(package_request.content)
    else: # skip if file is already present in cache
        pass

    return None


def get_cache_subfolder(settings, project_name):
    """Checks and returns the subfolder for the defined project_name."""

    cache_folder = settings.get('cache_folder')
    target_folder = os.path.abspath(os.path.join(cache_folder, project_name))
    if (not os.path.exists(target_folder)):
        create_directory(target_folder)

    return target_folder


def create_directory(dir_name):
    """Check if a directory exists and create it if it doesn't."""

    try:
        os.makedirs(dir_name)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    return None

