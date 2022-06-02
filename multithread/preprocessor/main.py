import os

from OSSCollector import analyze_file
from preprocessor import load_database, code_segmentation
from config import args
from concurrent.futures import ThreadPoolExecutor, as_completed
from tar import tar_main

cwd = os.getcwd()

if not os.path.exists(os.path.join(cwd, args.src_path)):
    print("Error: repo not found!")
    exit(-1)

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

if __name__ == "__main__":
    repos = [
      'binaryornot', 'docker-compose', 'flask-session',
      'ifaddr', 'jinja2-time', 'pydub', 'pyhocon', 'pyrogram'
    ]

    repos = [i.replace('-', '_') for i in repos]

    print('解压缩ing...o((>ω< ))o', end='')
    tar_main(args.src_path)
    print('finished')
    
    print('Analysing file...', end='')
    analyze_file_multithread(repos)
    print('Finished')

    print('Code Segmentation...', end='')
    DataBase = load_database()
    code_segmentation_multithread(DataBase, repos)
    print('Finished')
