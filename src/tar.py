import gzip
import os
import tarfile
import zipfile
import bz2
from concurrent.futures import ThreadPoolExecutor, as_completed

#path为repo的文件夹地址
def Decompress_All(path):
    if os.path.exists(path):
        # print(path)
        filename = {"":0}
        files = os.listdir(path)

        decompress_list = []

        for file in files:
            if file=='date.txt':
                continue
            flag=0
            pre=""
            path_to_enter = os.path.join(path, file)
            if (file.find('.tar.gz') != -1):
                pre=file[:-7]
                flag=1
            elif (file.find('.tar.bz2') != -1):
                pre=file[:-8]
                flag=2
            elif (file.find('.zip') != -1):
                pre=file[:-4]
                flag=3
            elif (file.find('.tgz') != -1):
                pre = file[:-4]
                flag=4
            # elif not os.path.isdir(file):
                # print(file)
                # print("not support!") # 会对目录报错QAQ (byt)
            if (flag != 0 ):
                if (pre in filename):
                    print("repeat!")
                else:
                    filename[pre]=1
                    # Decompression_file(path_to_enter)
                    decompress_list.append(path_to_enter)
            
            """删除压缩包
            """
            # delete_path = os.path.join(path, file)
            # os.remove(delete_path)
            # if(flag==1):
            #     os.remove(delete_path[:-3])
            # elif(flag==2):
            #     os.remove(delete_path[:-4])
        
        N_THREADS_FILE = 16
        file_pool = ThreadPoolExecutor(max_workers=N_THREADS_FILE)
        
        file_pool.map(Decompression_file, decompress_list)
        file_pool.shutdown(True)

        # 将目录名中的"-"替换成"_"
        for dir in os.listdir(path):
            if os.path.isdir(os.path.join(path, dir)) and '-' in dir:
                dir_ = dir.replace('-', '_')
                if not os.path.exists(os.path.join(path, dir_)):
                    os.rename(os.path.join(path, dir), os.path.join(path, dir_))
                else:
                    os.replace(os.path.join(path, dir_), os.path.join(path, dir))

    else:
        print("this path not exists!: %s"%path)

def Decompression_file(file_name):
    if(file_name.find('.gz') != -1):
        un_gz(file_name)
        name_without_gz = file_name[:-3]
        if(name_without_gz.find('.tar') != -1):
            un_tar(name_without_gz)
    elif(file_name.find('.bz2') != -1):
        un_bz2(file_name)
        name_without_bz2 = file_name[:-4]
        if(name_without_bz2.find('.tar') != -1):
            un_tar(name_without_bz2)
    elif(file_name.find('.zip') != -1):
        un_zip(file_name)
    elif(file_name.find('.tgz') != -1):
        un_tgz(file_name)
    else:
        print("Unsupported File!")


def un_tgz(file_name):
    tar = tarfile.open(file_name)
    f_name = file_name.replace(".tgz", "")
    if os.path.isdir(f_name):
        pass
    else:
        os.mkdir(f_name)
    tar.extractall(os.path.splitext(file_name)[0])
    tar.close()

#传入.bz2后缀的文件，在当前目录新增一个去除了.bz2后缀的文件
def un_bz2(file_name):
    zipfile = bz2.BZ2File(file_name)
    data = zipfile.read()
    newfile = file_name[:-4]
    open(newfile, 'wb').write(data)


#传入.gz后缀的文件，在当前目录新增一个去除了.gz后缀的文件
def un_gz(file_name):
    g_file = gzip.GzipFile(file_name)
    #获取文件的名称，去掉.gz后缀
    f_name = file_name.replace(".gz", "")
    #创建gzip对象
    open(f_name, "wb+").write(g_file.read())
    #gzip对象用read()打开后，写入open()建立的文件里。
    g_file.close()
    #关闭gzip对象


#传入.tar后缀的文件，在当前目录新增一个去除了.tar后缀的文件夹
def un_tar(file_name):
    #tar后缀的文件内有多个文件，将他们的文件名存入names中
    tar = tarfile.open(file_name)
    f_name = file_name.replace(".tar", "")
    names = tar.getnames()
    if os.path.isdir(f_name):
        pass
    else:
        os.mkdir(f_name)
    #因为解压后是很多文件，预先建立同名目录
    for name in names:
        tar.extract(name, f_name + "/")
    tar.close()


#传入.zip后缀的文件，在当前目录新增一个去除了.zip后缀的文件夹
def un_zip(file_name):
    zip_file = zipfile.ZipFile(file_name)
    f_name = file_name.replace(".zip", "")
    if os.path.isdir(f_name):
        pass
    else:
        os.mkdir(f_name)
    #因为解压后是很多文件，预先建立同名目录
    for names in zip_file.namelist():
        zip_file.extract(names,f_name + "/")
    zip_file.close()


def tar_main(filepath):
    if os.path.exists(filepath):
        dirs=os.listdir(filepath)
        dirs = [i for i in dirs if os.path.isdir(os.path.join(filepath, i))]

        N_THREAD_DIR = 16
        dir_pool = ThreadPoolExecutor(max_workers=N_THREAD_DIR)
        cnt = 0
        threads = set()
        while cnt < min(N_THREAD_DIR, len(dirs)):
            dir_path = os.path.join(filepath, dirs[cnt])
            threads.add(dir_pool.submit(Decompress_All, dir_path))
            cnt += 1
        while cnt < len(dirs):
            for c in as_completed(threads):
                err = c.exception()
                if err is not None:
                    print(f'Ignored exception\n{err}')
                threads.remove(err)
            while cnt < len(dirs) and len(threads) < N_THREAD_DIR:
                dir_path = os.path.join(filepath, dirs[cnt])
                threads.add(dir_pool.submit(Decompress_All, dir_path))
                cnt += 1
        dir_pool.shutdown(True)

    else:
        print("filepath not exists!")


if __name__ == "__main__":
    tar_main('cache')
