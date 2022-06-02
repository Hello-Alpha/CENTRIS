# -*- coding: utf-8 -*-

import os
import argparse
import configparser
import os
import errno

import requests

from pkg_resources import Requirement
from threading import Thread
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

_GENERIC_ADDRESS = "https://pypi.org/pypi/{package}/json"

redo_list = []
lock = threading.Lock()

def build_package_cache_latest(settings, package):
    pkg_url, pkg_date = resolve_url_list_latest(settings, package)
    if pkg_url == None:
        return None
    project_name, file_name, url = pkg_url
    target_folder = get_cache_subfolder(settings, project_name)
    target_file = os.path.join(target_folder, file_name)
    date = file_name + ' ' + pkg_date + '\n'
    download_package(url, target_file)
    with open(os.path.join(target_folder, 'date.txt'), 'w') as f:
        f.write(date)
    return

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
        # with click.progressbar(length=total_entries, width=0, label='') as bar:
        
        args = []

        for (project_name, file_name, url) in pkg_urls:
            # bar.label = "{:32s}".format(file_name)
            target_folder = get_cache_subfolder(settings, project_name)
            target_file = os.path.join(target_folder, file_name)
            dates += file_name + ' ' + pkg_dates[index] + '\n'
            index += 1
            # download_package(url, target_file)
            args.append((url, target_file))

            # bar.update(1) # advance status bar
        
        N_DOWNLOAD = 32
        download_pool = ThreadPoolExecutor(max_workers=N_DOWNLOAD)
        cnt = 0
        threads = []
        while cnt < min(N_DOWNLOAD, len(args)):
            # print(args[cnt][1])
            threads.append(download_pool.submit(download_package, args[cnt][0], args[cnt][1]))
            cnt += 1
        while cnt < len(args):
            for c in as_completed(threads):
                err = c.exception()
                if err is not None:
                    print('** Ignored thread exception **')
                threads.remove(c)
            while cnt < len(args) and len(threads) < N_DOWNLOAD:
                print(args[cnt][1])
                threads.append(download_pool.submit(download_package, args[cnt][0], args[cnt][1]))
                cnt += 1
        download_pool.shutdown(True)

        with open(os.path.join(target_folder, 'date.txt'), 'w') as date:
            date.write(dates)
        return None


def resolve_url_list_latest(settings, package):
    """Build a url list for packages matching the specifications."""

    requires = Requirement(package)

    package_addr = _GENERIC_ADDRESS.format(package=requires.name)
    try:
        package_request = requests.get(package_addr)
    except:
        print('Failed request for %s'%package)
        global redo_list
        lock.acquire()
        if package not in redo_list:
            redo_list.append(package)
        lock.release()
        return None, None

    # print(package_request.status_code)
    if package_request.status_code != 200:
        print('Invalid package %s'%package)
        return [], []

    try:
        package_data = package_request.json()
    except:
        print('Decode json failed')
        package_data = {}
        package_data["releases"] = {}
        pass

    # lastest_version = list(package_data["releases"].keys())[-1]

    # p = package_data["releases"].get(lastest_version)[0]

    # # if (package_is_valid(settings, package)):
    # file_name = str(p.get('filename'))  # file name
    # url = str(p.get('url'))             # url
    # project_name = str(requires.name)         # sub-folder in cache
    # url = (project_name, file_name, url)
    # # print(package.get('upload_time'))
    # date = p.get('upload_time')
    # # else:
    # #     return None, None

    version = list(package_data['releases'].keys())[-1]
    packages_for_version = package_data['releases'].get(version)
    for package in packages_for_version:
        if (package_is_valid(settings, package)):
            file_name = str(package.get('filename'))  # file name
            url = str(package.get('url'))             # url
            project_name = str(requires.name)         # sub-folder in cache
            url = (project_name, file_name, url)
            date = package.get('upload_time')
            break
        else:
            continue

    return url, date


def resolve_url_list(settings, package):
    """Build a url list for packages matching the specifications."""

    requires = Requirement(package)

    package_addr = _GENERIC_ADDRESS.format(package=requires.name)
#    while flag == False:
    try:
        package_request = requests.get(package_addr)
    except:
        print('Failed request for %s'%package)
        global redo_list
        lock.acquire()
        if package not in redo_list:
            redo_list.append(package)
        lock.release()
        return None, None

    # print(package_request.status_code)
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
    # accepted_types = settings['packagetypes']
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
        if package_request.status_code != 200:
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


def setup_parser():
    """Setup the parser instance."""

    prog_name = "sync_package_cache"
    description = ("Reads the provided config file and builds the package "
                   "cache according to the defined settings.")
    parser = argparse.ArgumentParser(prog=prog_name, description=description)
    parser.add_argument('configfile', type=str,
                        help="Path to a valid config file.")

    return parser


def parse_config(configfile):
    """Parse the config file."""

    if (not os.path.isfile(configfile)):
        raise OSError("No config file found at location '{}'"
                      .format(configfile))

    # delmiters=(':',':') to allow for = signs in package version specs
    config = configparser.ConfigParser(allow_no_value=True,
                                       delimiters=(':',':'))
    config.read(configfile)

    # get (and possibly create) the defined cache folder
    cache_folder = config['settings'].get('cache_folder', fallback='./')
    packagetypes = config['settings'].get('packagetypes', fallback='wheel')
    platform_tags = config['settings'].get('platform', fallback='')
    python_tags = config['settings'].get('python', fallback='') 
    cache_folder_abspath = os.path.abspath(cache_folder)
    create_directory(cache_folder_abspath)
    if (platform_tags == ''):
        platforms = None
    else:
        platforms = platform_tags.split(",")
    if (python_tags == ''):
        python_versions = None
    else:
        python_versions = python_tags.split(",")
    settings = {
        'cache_folder': os.path.abspath(cache_folder),
        'packagetypes': packagetypes.split(","),
        'pyversions': python_versions,
        'platforms': platforms,
    }

    package_list = []
    for item in config['packages']:
        package_list.append(item)

    return (settings, package_list)

if __name__ == "__main__":
    parser = setup_parser()
    config_path = os.path.abspath(parser.parse_args().configfile)
    settings, packages = parse_config(config_path)

    N_THREADS = 32
    pool = ThreadPoolExecutor(max_workers=N_THREADS)
    threads = []
    cnt_thread = 0

    while cnt_thread < min(N_THREADS, len(packages)):
        threads.append(pool.submit(build_package_cache, settings, packages[cnt_thread]))
        cnt_thread += 1
    length_packages = len(packages)
    while cnt_thread < length_packages:
        for c in as_completed(threads):
            threads.remove(c)
        while cnt_thread < length_packages and len(threads) < N_THREADS:
            threads.append(pool.submit(build_package_cache, settings, packages[cnt_thread]))
            cnt_thread += 1
    pool.shutdown(True)

    cnt = 0
    while cnt < 5:
        redo_list = []
        try:
            if len(redo_list) == 0:
                print('Finished~')
                break
            threads = []
            cnt_sum = 0
            for package in redo_list:
                threads.append(Thread(target=build_package_cache, args=(settings, package)))
                threads[-1].start()
                cnt_sum += 1
            for t in threads:
                t.join()
            cnt += 1
        except:
            break
    if cnt == 5 and len(redo_list) != 0:
        print('Still some packages missing:', redo_list)
        with open('redo.log', 'w') as redo:
            redo.write(str(redo_list))

