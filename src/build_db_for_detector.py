"""在得到prime OSS和non-prime OSS后，需要再次对所有的组件的prime函数进行排序，方便检测
"""

import os

if __name__ == "__main__":
  results_rm_path = '/home/syssec-py/results_rm'
  results_path = '/home/syssec-py/results_new_utf8/repo_func'
  # results_rm_path = 'results_rm'
  # results_path = 'results/repo_func'

  # 非prime OSS的prime部分
  results_rm_list = os.listdir(results_rm_path)
  # 所有的OSS
  results_list = os.listdir(results_path)
  
  repo_funcs = []
  cnt = 0
  for repo in results_list:
    print(f'\r{(cnt/len(results_list)*100):.2f}%', end='')
    if repo in results_rm_list:
      with open(os.path.join(results_rm_path, repo), 'rb') as rf:
        for line in rf.readlines():
          repo_funcs.append(line)
    else:
      with open(os.path.join(results_path, repo), 'rb') as rf:
        for line in rf.readlines():
          repo_funcs.append(line)
    cnt += 1

  print('Sorting...', end='')
  s = set(repo_funcs)
  repo_funcs = list(s)
  repo_funcs.sort(key=lambda x: x.split(b'*')[3])
  print('Finished')
  cnt = 0
  print('')
  with open('db.txt', 'wb') as out:
    buf = b''
    for f in repo_funcs:
      print(f'\r{(cnt/len(repo_funcs)*100):.2f}%', end='')
      buf += f
      cnt += 1
    out.write(buf)
  print('Ciao~')
