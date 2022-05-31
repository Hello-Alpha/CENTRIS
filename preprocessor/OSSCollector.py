import copy
import math
import os
import shutil

import tlsh
from tqdm import tqdm
import parso
import tokenize
import io
import pymysql
import traceback
from config import args


class func_sign():
    def __init__(self, name="", start=0, end=0):
        self.name = name
        self.start = start  # 起始行
        self.end = end      # 终结行


class TXTProcess():
    def __init__(self):
        self.identifier = []

    def remov_comment(self, func_str, lines):
        new_lines = copy.deepcopy(lines)
        stringio = io.StringIO(func_str)
        for toktype, tok, start, end, line in tokenize.generate_tokens(stringio.readline):
            if toktype == tokenize.COMMENT:
                new_lines[start[0]-1] = new_lines[start[0]-1][:start[1]] + new_lines[start[0]-1][end[1]:]
        return "".join(new_lines)

    def remov_blank(self, func_str):
        return func_str.replace('\t', '').replace('\n', '').replace(' ', '').strip()


class func_info():
    def __init__(self, func_name, version_id, func_date):
        self.func_name = func_name
        self.version_ids = str(version_id)
        self.version_num = 1
        self.func_date = func_date

    def addversion(self, version_id):
        if self.version_ids.split(' ')[-1] != str(version_id):
            self.version_ids += ' ' + str(version_id)
            self.version_num += 1


def get_file(repo_path):
    file_list = []
    for path, dir, files in os.walk(repo_path):
        for file in files:
            if file[-3:] == ".py":
                file_list.append(os.path.join(path, file).replace("\\", "/"))
    return file_list


def get_func(node, funclist):
    if node.type == "funcdef":
        funclist.append(func_sign(node.name.value,
                        node.start_pos[0], node.end_pos[0]))
    if hasattr(node, "children") is True:
        for sub_node in node.children:
            get_func(sub_node, funclist)


def parse(func_dict, version_id, repo_date, file_list):
    for file in file_list:
        f = open(file, "r", encoding="utf-8")

        # 读取每一行
        lines = f.readlines()

        # 将整个文件并成一个字符串
        src_code = ""
        src_code = src_code.join(lines[:])

        # parse
        module = parso.parse(src_code)

        # 获取函数列表
        funclist = []
        get_func(module, funclist)

        for func in funclist:
            func_str = "".join(lines[func.start - 1: func.end])

            # 去除注释
            func_str = TXTProcess().remov_comment(
                func_str, lines[func.start - 1: func.end])
            # 去除空字符
            func_str = TXTProcess().remov_blank(func_str)
            # 计算TLSH
            func_bstr = str.encode(func_str, encoding="utf-8")
            TLSH = tlsh.forcehash(func_bstr)

            # funcHash以T1开头，去除这个标识符
            if len(TLSH) == 72 and TLSH.startswith("T1"):
                TLSH = TLSH[2:]
            elif TLSH == "TNULL" or TLSH == "" or TLSH == "NULL":
                continue

            # func_dict字典：{“funcHash”: func_info}, 可能存在哈希碰撞
            if TLSH not in func_dict:
                func_dict[TLSH] = func_info(func_name=func.name, version_id=version_id, func_date=repo_date)
            else:
                if func_dict[TLSH].func_name == func.name:
                    func_dict[TLSH].addversion(version_id)
                else:
                    print("哈希碰撞")

    return func_dict


def Analyze(db, cursor):
    f = open("repo_func_summary.txt", "w")
    repo_func_summary = ["format: repo_name(version_number) - function number\n",
                         "---------------------------------------------------\n","",
                         "---------------------------------------------------\n"]
    # 读取所有repo
    cursor.execute("""select repo_name, version, version_id, repo_date 
                    from repo
                    order by repo_name, version_id""")
    repo_list = cursor.fetchall()
    total_func_num = 0
    version_num = 0
    func_dict = {}
    with tqdm(total=len(repo_list), smoothing=0.0) as pbar:
        for idx, repo in enumerate(repo_list):
            cur_repo_name = repo[0]
            version_num += 1
            repo_path = "%s\\%s\\%s_%s" % (args.src_path, repo[0], repo[0], repo[1])
            # 分析一个工程
            file_list = get_file(repo_path)  # 获取py文件列表
            if len(file_list) == 0:
                print("Invalid reponame: %s" % cur_repo_name)
            try:
                func_dict = parse(func_dict, repo[2], repo[3], file_list)  # 分析该项目中的所有文件
            except:
                traceback.print_exc()

            if idx == len(repo_list) -1 or cur_repo_name != repo_list[idx + 1][0]:
                # 将函数插入数据库
                try:
                    for hashval, func in func_dict.items():
                        func_weight = math.log(float(version_num)/float(func.version_num))  # 以e为底数
                        # 执行sql语句
                        cursor.execute("""insert into func (repo_name, version_ids, func_name, hash_val, func_date, func_weight)
                                VALUES ('%s', '%s', '%s', '%s', '%s', %f)""" % (cur_repo_name, func.version_ids, func.func_name, hashval, func.func_date, func_weight))
                        # 提交到数据库执行
                        db.commit()
                except:
                    traceback.print_exc()
                    print("cur_repo_name = %s" % cur_repo_name)
                    # 如果发生错误则回滚
                    db.rollback()

                repo_func_summary.append("%s(%d) - %d\n" % (cur_repo_name, version_num, len(func_dict)))
                version_num = 0
                total_func_num += len(func_dict)
                func_dict.clear()

            pbar.set_postfix(
                {"repo_name": repo[0], "version": repo[1], "cur_func_num": len(func_dict), "total_func_num": total_func_num})
            pbar.update()


        repo_func_summary[2] = "total function number = %d\n" % total_func_num
        f.writelines(repo_func_summary)

        print("-----------------------\nsummary:")
        print("total function number = %d" % (total_func_num))
        print("-----------------------")


def AnalyzeFile(continue_flag):
    f_repo = open("repo_info.txt", "r")

    if continue_flag == False:
        # 从头开始分析
        if os.path.exists("./results"):
            shutil.rmtree("./results")
        os.mkdir("./results")
        total_func_num = 0
        finished_repos = []
    else:
        # 从未分析的包开始
        total_func_num = 0
        finished_repos = [repo_name[:-4] for repo_name in os.listdir("./results")]


    # 读取所有repo
    f_repo_lines = f_repo.readlines()
    repo_list = [tuple(line.strip().split('*')) for line in f_repo_lines]

    version_num = 0
    func_dict = {}
    with tqdm(total=len(repo_list), smoothing=0.0) as pbar:
        for idx, repo in enumerate(repo_list):
            cur_repo_name = repo[0]

            if continue_flag is True and cur_repo_name in finished_repos:
                with open("./results/%s.txt" % cur_repo_name, "r") as fp:
                    total_func_num += len(fp.readlines())
                pbar.set_postfix(
                    {"repo_name": repo[0], "version": repo[1], "cur_func_num": len(func_dict),
                     "total_func_num": total_func_num})
                pbar.update()
                continue

            version_num += 1
            repo_path = "%s\\%s\\%s_%s" % (args.src_path, repo[0], repo[0], repo[1])
            # 分析一个工程
            file_list = get_file(repo_path)  # 获取py文件列表
            if len(file_list) == 0:
                print("Invalid reponame: %s" % cur_repo_name)
            try:
                func_dict = parse(func_dict, repo[2], repo[3], file_list)  # 分析该项目中的所有文件
            except:
                traceback.print_exc()

            if idx == len(repo_list) -1 or cur_repo_name != repo_list[idx + 1][0]:
                with open("./results/%s.txt" % cur_repo_name, "w") as f_func:
                    # 将函数插入数据库
                    for hashval, func in func_dict.items():
                        func_weight = math.log(float(version_num)/float(func.version_num))  # 以e为底数
                        f_func.write("%s*%s*%s*%s*%s*%f\n" % (cur_repo_name, func.version_ids, func.func_name, hashval, func.func_date, func_weight))

                version_num = 0
                total_func_num += len(func_dict)
                func_dict.clear()

            pbar.set_postfix(
                {"repo_name": repo[0], "version": repo[1], "cur_func_num": len(func_dict), "total_func_num": total_func_num})
            pbar.update()


        print("-----------------------\nsummary:")
        print("total function number = %d" % (total_func_num))
        print("-----------------------")


def initDatabase(initTable=False):
    # 打开数据库连接
    db = pymysql.connect(host='localhost',
                         user='root',
                         password='123456',
                         database='repo')

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    if initTable:
        # 删除所有表
        cursor.execute("""select table_name, table_type 
                        from information_schema.tables 
                        where table_schema = 'repo';""")
        results = cursor.fetchall()

        # 使用 execute() 方法执行 SQL，如果表存在则删除
        for table in results:
            cursor.execute("DROP TABLE IF EXISTS %s;" % table[0])

        # 建立表
        cursor.execute("""create table repo (
                        repo_name CHAR(50),
                        version VARCHAR(40),
                        version_id INT,
                        repo_date DATETIME);""")
        # version_id从1开始
        # repo_path = "%s\\%s\\%s-%s" % (args.src_path, repo_name, repo_name, version)

        cursor.execute("""create table func (
                        repo_name CHAR(50),
                        version_ids VARCHAR(200),
                        func_name VARCHAR(100),
                        hash_val CHAR(100),
                        func_date DATETIME,
                        func_weight FLOAT);""")
        # version_ids是version_id的列表

    return db, cursor


def SaveRepoInfo(db, cursor):
    repo_list = os.listdir(args.src_path)

    for repo_name in repo_list:
        repo_path_base = os.path.join(args.src_path, repo_name)
        version_dict = {}   # 版本和日期的对应字典
        try:
            f = open(os.path.join(repo_path_base, "date.txt"), "r")
        except:
            print("Invalid repository: %s" % repo_name)
            continue
        f_lines = f.readlines()
        for line in f_lines:
            version_dict["".join(line.split(' ')[:-1])] = line.split(' ')[-1]
        for idx, (repo_version, repo_date) in enumerate(version_dict.items()):
            version = repo_version[len(repo_name)+1:-7]
            repo_date = repo_date.replace('T', ' ').strip()
            try:
                # 执行sql语句
                cursor.execute("""insert into repo (repo_name, version, version_id, repo_date)
                    VALUES ('%s', '%s', %s, '%s')""" % (repo_name, version, idx+1, repo_date))
                # 提交到数据库执行
                db.commit()
            except:
                traceback.print_exc()
                print("repo_name = %s" % repo_name)
                # 如果发生错误则回滚
                db.rollback()


def SaveRepoInfoFile():
    repo_list = os.listdir(args.src_path)
    f_repo = open("repo_info.txt", "w")
    for repo_name in repo_list:
        repo_path_base = os.path.join(args.src_path, repo_name)
        version_dict = {}   # 版本和日期的对应字典
        try:
            f = open(os.path.join(repo_path_base, "date.txt"), "r")
        except:
            print("Invalid repository: %s" % repo_name)
            continue
        f_lines = f.readlines()
        for line in f_lines:
            version_dict["".join(line.split(' ')[:-1])] = line.split(' ')[-1]
        for idx ,(repo_version, repo_date) in enumerate(version_dict.items()):
            version = repo_version[len(repo_name)+1:-7]
            repo_date = repo_date.replace('T', ' ').strip()
            f_repo.write("%s*%s*%s*%s\n" % (repo_name, version, idx+1, repo_date))
