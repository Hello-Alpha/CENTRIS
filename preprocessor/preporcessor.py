
import math
import traceback
import tlsh
from tqdm import tqdm

from config import args


def CompareBirth(birthday1, birthday2):
    # 如果birthday1<birthday2返回True
    return True


def CheckPrime(db, cursor, S_name, S, DataBase):
    # S_name: S的名字
    # S_birth: S的发行日期

    isPrime = True

    G = {}  # 当前OSS中有哪些函数是抄的， {"repo_name": ["hash", ...], ...}
    copied_OSS = {}  # S抄了哪些OSS以及对应的函数名
    # DBtuple - 0: repo_name  1: func_name  2: version_ids  3: hash_val  4: func_date
    # S_func - 0: func_name  1: version_ids  2: hash_val  3: func_date
    for DBtuple in DataBase:
        if DBtuple[0] == S_name:
            continue
        for S_func in S:
            score = tlsh.diffxlen(S_func[2], DBtuple[3])
            if int(score) <= args.score_thresh:
                # 遍历database中所有与当前哈希值一样的函数所在的repo
                # for DBtuple in [x[0] for x in DBtuples]:

                if DBtuple[4] <= S_func[3]:
                    if DBtuple[0] not in G:
                        G[DBtuple[0]] = []
                    # hashval代表的函数在抄了repo_name
                    G[DBtuple[0]].append(S_func[2])

    # members包含了抄的OSS名字
    for repo_name in G.keys():
        G[repo_name] = list(set(G[repo_name]))
        phi = float(len(G[repo_name])) / float(len(S))
        if phi >= args.theta:
            isPrime = False
            # 这里是返回copied_OSS(部分)还是G(全部)?
            copied_OSS[repo_name] = G[repo_name]

    return isPrime, copied_OSS


def codeSegmentation(db, cursor):
    f = open("copy_summary.txt", "w")
    # 读取所有repo
    cursor.execute("""select distinct repo_name 
                    from repo;""")
    repos = cursor.fetchall()
    # 读取所有函数
    cursor.execute("""select repo_name, version_ids, func_name, hash_val, func_date 
                        from func;""")
    funcs = cursor.fetchall()
    with tqdm(total=len(repos)) as pbar:
        for repo_name in repos:
            repo_name = repo_name[0]
            # 读取该OSS的函数
            cursor.execute("""select func_name, version_ids, hash_val, func_date 
                                from func
                                where repo_name = '%s';""" % repo_name)
            repo_funcs = cursor.fetchall()
            isPrime, copied_OSS = CheckPrime(db, cursor, repo_name, repo_funcs, funcs)  # 检查S是否是抄的

            if isPrime is False:
                f.write("%s:\n"%repo_name)
                # 将S中抄的部分删除
                for copied_OSS_name, hash_list in copied_OSS.items():
                    f.write("\t%s - %d\n" % (copied_OSS_name, len(hash_list)))
                    for hashval in hash_list:
                        try:
                            # 执行SQL语句
                            cursor.execute("""delete from func 
                                            where repo_name = '%s' and hash_val = '%s';""" % (repo_name, hashval))
                            # 提交修改
                            db.commit()
                        except:
                            traceback.print_exc()
                            # 发生错误时回滚
                            db.rollback()
            pbar.set_postfix({"repo_name": repo_name})
            pbar.update()


def getWeight(repo_name):
    # 根据repo_name获取信息
    repo_dict = {}  # 该repo中函数哈希值和版本的字典{"repo_name": [hash, ...], ...}
    weight_dict = {}    # 该repo中函数哈希值和权重的字典{"repo_name": weight, ...}
    n = 1   # 该oss的总版本数

    for hashval, verlist in repo_dict.items():
        weight_dict[hashval] = math.log(float(n)/float(len(verlist)))

    return weight_dict
