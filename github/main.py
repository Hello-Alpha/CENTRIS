import requests
import os
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from retry import retry
import logging

lock = RLock()
failed = []

@retry(tries=5, logger=logging.Logger)
def download(url):
  print(url)
  # try:
  repo_request = requests.get(url, allow_redirects=True)
  # except:
  #   print(f'Failed request for {url}')
  #   lock.acquire()
  #   failed.append(url)
  #   lock.release()
  #   return False
  if repo_request.status_code != 200:
    print(f'Failed request for {url}')
    lock.acquire()
    failed.append(url)
    lock.release()
    return False
  else:
    url = url.replace('//', '').split('/')
    author = url[2]
    repo_name = url[3]
    filename = author + '@@' + repo_name + ".zip"
    with open(os.path.join('repo', filename), 'wb') as o:
      o.write(repo_request.content)
    return True

if __name__ == '__main__':
  urls = []
  with open('github.txt', 'r') as f:
    for line in f.readlines():
      if '.git' in line:
        url = line[:-5]
      else:
        url = line
      # https://gh.api.99988866.xyz/https://github.com/localstack/localstack/archive/master.zip
      url = 'https://gh.api.99988866.xyz/' + url + '/archive/master.zip'
      urls.append(url)

  pool = ThreadPoolExecutor(max_workers=32)
  pool.map(download, urls)

  cnt = 0
  timeout = 5
  while cnt < timeout:
    urls = failed.copy()
    failed = []
    pool.map(download, urls)
    cnt += 1
  pool.shutdown(True)

  print(f'{len(failed)} failed after {timeout} timeouts:\n{failed}')

