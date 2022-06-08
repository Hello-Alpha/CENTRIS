import os

from config import args
from collector_main import build_package_cache, build_package_cache_latest, parse_config
from OSSCollector import analyze_file
from preprocessor import load_database, code_segmentation
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from tar import Decompress_All
import shutil


def check_dir():
    cwd = os.getcwd()

    # if not os.path.exists(os.path.join(cwd, args.src_path)):
    #     print("Error: repo not found!")
    #     exit(-1)

    result_base = os.path.join(cwd, args.result_path)
    if not os.path.exists(result_base):
        os.mkdir(result_base)
    if not os.path.exists(os.path.join(result_base, "repo_func")):
        os.mkdir(os.path.join(result_base, "repo_func"))
    if not os.path.exists(os.path.join(result_base, "repo_date")):
        os.mkdir(os.path.join(result_base, "repo_date"))

    if not os.path.exists(os.path.join(cwd, args.copy_summary_path)):
        os.mkdir(os.path.join(cwd, args.copy_summary_path))

    if not os.path.exists(os.path.join(cwd, args.rm_result_path)):
        os.mkdir(os.path.join(cwd, args.rm_result_path))

def code_segmentation_multithread(DataBase, repos):
    """多线程调用Code Segmentation

    Args:
        DataBase (list): List of repo_func.
        repos (list): Repo names.
    """

    """多线程
  """
    N_THREADS = 8
    pool = ThreadPoolExecutor(max_workers=N_THREADS)
    pool.map(code_segmentation, [DataBase]*len(repos), repos)
    pool.shutdown(True)

    """多进程
  """
    # args = []
    # for i in repos:
    #   args.append((DataBase, i))

    # from multiprocessing import Pool
    # N_THREADS = 8
    # pool = Pool(N_THREADS)
    # pool.starmap_async(code_segmentation, args)
    # pool.close()
    # pool.join()

    return


def main_thread(settings, package):
  # Download
  # build_package_cache_latest(settings, package)
  repo_func_path = os.path.join(args.result_path, 'repo_func')
  if package + '.txt' not in os.listdir(repo_func_path):
    build_package_cache(settings, package)
    # Decompress
    Decompress_All(os.path.join(args.src_path, package))
    # *.py -> LSH
    analyze_file(package)
  else:
    print(f'Already finished: {package}')

  global lock
  lock.acquire()
  print(package) # 输出已经完成的
  with open('done.log', 'a') as f:
    f.write(package+'\n')
  lock.release()

  # Delete repo folder
  # shutil.rmtree(os.path.join(args.src_path, package), ignore_errors=True)
  import subprocess
  # Only in Windows!!!
  if os.path.exists(os.path.join(args.src_path, package)):
    subprocess.run(['rmdir', '/q', '/s', os.path.join(args.src_path, package)], shell=True)

  return

lock = Lock()

if __name__ == "__main__":
    check_dir()  # 初始化result目录

    settings, packages = parse_config(args.config)  # 解析配置文件

    # 为每个package创建一个线程
    N_THREADS = 128
    pool = ThreadPoolExecutor(max_workers=N_THREADS)
    pool.map(main_thread, [settings]*len(packages), packages)
    pool.shutdown(True)

    """后续的Code Segmentation先不做
    """
    # DataBase = load_database()
    # print('Code Segmentation...')
    # code_segmentation_multithread(DataBase, packages)
    # print('Finished')
