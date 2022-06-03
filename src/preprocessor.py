
import math
import os
import traceback
import tlsh
from tqdm import tqdm

from config import args


def check_prime(DataBase, S_name, S):
    # S_name: S的名字
    # DataBase: 全局变量，保存所有函数

    isPrime = True

    G = {}  # 当前OSS中有哪些函数是抄的， {"repo_name": ["hash", ...], ...}
    copied_OSS = {}  # S抄了哪些OSS以及对应的函数名

    # DBtuple/S_func - 0: repo_name  1: func_name  2: version_ids  3: hash_val  4: func_date  5: func_weight
    for DBtuple in DataBase:
        if DBtuple[0] == S_name:
            continue
        for S_func in S:
            score = tlsh.diffxlen(S_func[3], DBtuple[3])
            if int(score) <= args.score_thresh:
                # 遍历database中所有与当前哈希值一样的函数所在的repo
                if DBtuple[4] <= S_func[4]:
                    if DBtuple[0] not in G:
                        G[DBtuple[0]] = []
                    # hashval代表的函数在抄了repo_name
                    G[DBtuple[0]].append(S_func)

    # members包含了抄的OSS名字
    for repo_name in G.keys():
        G[repo_name] = list(set(G[repo_name]))
        phi = float(len(G[repo_name])) / float(len(S))
        if phi >= args.theta:
            isPrime = False
            # 这里是返回copied_OSS(部分)还是G(全部)?
            copied_OSS[repo_name] = G[repo_name]

    return isPrime, copied_OSS


def code_segmentation(DataBase, repo_name):
    repo_func_path = os.path.join(args.result_path, "repo_func")
    with open(os.path.join(repo_func_path, repo_name + ".txt"), "r") as f:
        func_list = f.readlines()

    repo_funcs = [tuple(func.strip().split('*')) for func in func_list]

    isPrime, copied_OSS = check_prime(DataBase, repo_name, repo_funcs)  # 检查S是否是抄的

    print(repo_name,end='')
    if isPrime is False:
        print('!')
        with open(os.path.join(args.copy_summary_path, "%s.txt" % repo_name), "w") as f:
            # 将S中抄的部分删除
            for copied_OSS_name, funcs in copied_OSS.items():
                f.write("%s: %d\n" % (copied_OSS_name, len(funcs)))
                for func in funcs:
                    repo_funcs.remove(func)
        with open(os.path.join(args.rm_result_path, "%s.txt" % repo_name), "w") as f:
            for func in repo_funcs:
                f.write("%s*%s*%s*%s*%s*%s\n" % (func[0], func[1], func[2], func[3], func[4], func[5]))
    else:
        print('~')


def load_database():
    DataBase = []
    repo_func_path = os.path.join(args.result_path, "repo_func")
    repo_list = os.listdir(repo_func_path)
    for repo in repo_list:
        with open(os.path.join(repo_func_path, repo), "r") as f:
            lines = f.readlines()
            for line in lines:
                DataBase.append(tuple(line.strip().split('*')))
    return DataBase
