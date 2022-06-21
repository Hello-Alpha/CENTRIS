import os
import multiprocessing

def unzip(f):
  if f[-4:] == '.zip':
    print('unzip repo/' + f + ' -d repo_extracted/' + f[:-4])
    os.system('unzip -q repo/' + f + ' -d repo_extracted/' + f[:-4])
  return

if __name__ == "__main__":
  filelist = [(i,) for i in os.listdir('repo')]
  print(filelist)

  pool = multiprocessing.Pool(32)
  pool.starmap_async(unzip, filelist)
  pool.close()
  pool.join()
