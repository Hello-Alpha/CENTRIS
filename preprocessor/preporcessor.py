
import math
import traceback
import tlsh
from config import args


def CompareBirth(birthday1, birthday2):
    # 如果birthday1<birthday2返回True
    return True


def CheckPrime(db, cursor, S_name, S_birth):
    # S_name: S的名字
    # S_birth: S的发行日期

    # 读取repo中所有的函数
    cursor.execute("""select hash_val, file_path 
                    from func 
                    where repo_name = '%s';""" % S_name)
    S = cursor.fetchall()
    # S: 当前OSS, 是个含有hashval的array; DataBase: 所有OSS, 两者结构相同

    # 读取database中所有的函数
    cursor.execute("""select func.hash_val, func.repo_name, func.file_path, repo.repo_date
                    from func
                    inner join repo
                    on func.repo_name=repo.repo_name and func.version=repo.version;""")
    # "hash": [("repo_name", version, birth), ...]，version怎么用？
    DataBase = cursor.fetchall()

    isPrime = True

    G = {}  # 当前OSS中有哪些函数是抄的， {"repo_name": ["hash", ...], ...}
    copied_OSS = {}  # S抄了哪些OSS以及对应的函数名
    for S_func in S:
        for DBtuple in DataBase:
            repo_name = DBtuple[1]
            if repo_name == S_name:
                continue
            score = tlsh.diffxlen(S_func[0], DBtuple[0])
            if int(score) <= args.score_thresh:
                # 遍历database中所有与当前哈希值一样的函数所在的repo
                # for DBtuple in [x[0] for x in DBtuples]:
                if DBtuple[3] <= S_birth:
                    if repo_name not in G:
                        G[repo_name] = []
                    # hashval代表的函数在抄了repo_name
                    G[repo_name].append(S_func[0])

    # members包含了抄的OSS名字
    for repo_name in G.keys():
        phi = float(len(G[repo_name])) / float(len(S))
        if phi >= args.theta:
            isPrime = False
            # 这里是返回copied_OSS(部分)还是G(全部)?
            copied_OSS[repo_name] = G[repo_name]

    return isPrime, copied_OSS


def redundancyElimination(db, cursor):
    # 读取所有repo
    cursor.execute("""select repo_name, repo_path, version, repo_date 
                    from repo;""")
    repos = cursor.fetchall()
    for repo_info in repos:
        isPrime, copied_OSS = CheckPrime(db, cursor,
                                         repo_info[0], repo_info[3])  # 检查S是否是抄的

        if isPrime is False:
            # 将S中抄的部分删除
            for _, hash_list in copied_OSS.items():
                for hashval in hash_list:
                    try:
                        # 执行SQL语句
                        cursor.execute("""delete from func 
                                        where repo_name = '%s' and hash_val = '%s';""" % (repo_info[0], hashval))
                        # 提交修改
                        db.commit()
                    except:
                        traceback.print_exc()
                        # 发生错误时回滚
                        db.rollback()


def getWeight(repo_name):
    # 根据repo_name获取信息
    repo_dict = {}  # 该repo中函数哈希值和版本的字典{"repo_name": [hash, ...], ...}
    weight_dict = {}    # 该repo中函数哈希值和权重的字典{"repo_name": weight, ...}
    n = 1   # 该oss的总版本数

    for hashval, verlist in repo_dict.items():
        weight_dict[hashval] = math.log(float(n)/float(len(verlist)))

    return weight_dict
