import os

from config import args
from collector_main import build_package_cache_latest, parse_config
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



def analyze_file_multithread(repos):
  """
    提取OSS函数
    repo_name = "0html"
    analyze_file(repo_name)

  Args:
      repos (list): List of repo names
  """

  N_THREADS = 64
  pool = ThreadPoolExecutor(max_workers=N_THREADS)
  cnt = 0
  threads = []
  while cnt < min(N_THREADS, len(repos)):
    threads.append(pool.submit(analyze_file, repos[cnt]))
    cnt += 1
  while cnt < len(repos):
    for c in as_completed(threads):
      err = c.exception()
      if err is not None:
          print(f'** Ignored thread exception**\n{err}')
      threads.remove(c)
      print(c.result())
    while cnt < len(repos) and len(threads) < N_THREADS:
      threads.append(pool.submit(analyze_file, repos[cnt]))
      cnt += 1
  pool.shutdown(True)

def code_segmentation_multithread(DataBase, repos):
  """多线程调用Code Segmentation

  Args:
      DataBase (list): List of repo_func.
      repos (list): Repo names.
  """
  if len(DataBase) != len(repos):
    print(f'Database num {len(DataBase)} does not match Repo num {len(repos)}')
    return
  N_THREADS = 64
  pool = ThreadPoolExecutor(max_workers=N_THREADS)
  cnt = 0
  threads = []
  while cnt < min(N_THREADS, len(repos)):
    threads.append(pool.submit(code_segmentation, DataBase[cnt], repos[cnt]))
    cnt += 1
  while cnt < len(repos):
    for c in as_completed(threads):
      err = c.exception()
      if err is not None:
          print(f'** Ignored thread exception**\n{err}')
      threads.remove(c)
      print(c.result())
    while cnt < len(repos) and len(threads) < N_THREADS:
      threads.append(pool.submit(code_segmentation, DataBase[cnt], repos[cnt]))
      cnt += 1
  pool.shutdown(True)


def main_thread(settings, package):
  # print(package)
  # Download
  build_package_cache_latest(settings, package)
  # Decompress
  Decompress_All(os.path.join(args.src_path, package))
  # *.py -> LSH
  analyze_file(package)

  global lock
  lock.acquire()
  print(package) # 输出已经完成的
  with open('done.log', 'a') as f:
    f.write(package+'\n')
  lock.release()

  # Delete source code
  shutil.rmtree(os.path.join(args.src_path, package))

  return

lock = Lock()

# pbar = None

if __name__ == "__main__":
    check_dir() # 初始化result目录

    settings, packages = parse_config(args.config) # 解析配置文件

    # 为每个package创建一个线程
    N_THREADS = 128
    pool = ThreadPoolExecutor(max_workers=N_THREADS)
    threads = set()
    cnt_thread = 0

    # # 初始化pool
    # length_packages = len(packages)
    # while cnt_thread < min(N_THREADS, length_packages):
    #     threads.add(pool.submit(main_thread, settings, packages[cnt_thread]))
    #     cnt_thread += 1
    
    # # pool update
    # while cnt_thread < length_packages:
    #     for c in as_completed(threads):
    #         threads.remove(c)
    #     while cnt_thread < length_packages and len(threads) < N_THREADS:
    #         threads.add(pool.submit(main_thread, settings, packages[cnt_thread]))
    #         cnt_thread += 1
    # pool.shutdown(True)
    pool.map(main_thread, [settings]*len(packages), packages)
    pool.shutdown(True)

    # if os.path.exists('abandoned.txt'):
    #   with open('abandoned.txt', 'r') as f:
    #     result_path = args.result_path
    #     for repo in f:
    #       try:
    #         os.remove(os.path.join(result_path, 'repo_date', repo+'.txt'))
    #         os.remove(os.path.join(result_path, 'repo_func', repo+'.txt'))
    #       except:
    #         pass

    """后续的Code Segmentation先不做
    """
    # print('Code Segmentation...', end='')
    # DataBase = load_database()
    # code_segmentation_multithread(DataBase, packages)
    # print('Finished')
