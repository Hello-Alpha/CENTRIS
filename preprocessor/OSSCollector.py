import copy
import os
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


def parse(func_dict, version_id, file_list):
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

            # func_dict字典：{“funcHash”: {函数名, 版本id}}}, 可能存在哈希碰撞
            if TLSH not in func_dict:
                func_dict[TLSH] = {func.name: str(version_id)}
            else:
                if func.name in func_dict[TLSH]:
                    if str(version_id) not in func_dict[TLSH][func.name].split(' '):    # 防止出现重复
                        func_dict[TLSH][func.name] += ' ' + str(version_id)
                else:
                    # 哈希碰撞
                    func_dict[TLSH][func.name] = str(version_id)

    return func_dict


def Analyze(db, cursor):
    # 读取所有repo
    cursor.execute("""select repo_name, version, version_id, repo_date 
                    from repo
                    order by repo_name, version_id""")
    repo_list = cursor.fetchall()
    total_func_num = 0
    cur_repo_name = ''
    func_dict = {}
    with tqdm(total=len(repo_list), smoothing=0.0) as pbar:
        for idx, repo in enumerate(repo_list):
            if cur_repo_name != repo[0]:
                cur_repo_name = repo[0]
                total_func_num += len(func_dict)

                # 将函数插入数据库
                try:
                    for hashval, functions in func_dict.items():
                        for func_name, version_ids in functions.items():
                            # 执行sql语句
                            cursor.execute("""insert into func (repo_name, version_ids, func_name, hash_val, func_weight)
                                    VALUES ('%s', '%s', '%s', '%s', 0.0)""" % (repo[0], version_ids, func_name, hashval))
                            # 提交到数据库执行
                            db.commit()
                except:
                    traceback.print_exc()
                    print("version_ids = %s" % version_ids)
                    print("func_name = %s" % func_name)
                    # 如果发生错误则回滚
                    db.rollback()

                func_dict.clear()

            repo_path = "%s\\%s\\%s-%s" % (args.src_path, repo[0], repo[0], repo[1])
            # 分析一个工程
            file_list = get_file(repo_path)  # 获取py文件列表

            try:
                func_dict = parse(func_dict, repo[2], file_list)  # 分析该项目中的所有文件
            except:
                traceback.print_exc()

            pbar.set_postfix(
                {"repo_name": repo[0], "version": repo[1], "cur_func_num": len(func_dict), "total_func_num": total_func_num})
            pbar.update()




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
                        func_weight FLOAT);""")
        # version_ids是version_id的列表

    return db, cursor


def SaveRepoInfo(db, cursor):
    repo_list = os.listdir(args.src_path)

    for repo_name in repo_list:
        repo_path_base = os.path.join(args.src_path, repo_name)
        version_dict = {}   # 版本和日期的对应字典
        f = open(os.path.join(repo_path_base, "date.txt"), "r")
        f_lines = f.readlines()
        for line in f_lines:
            version_dict["".join(line.split(' ')[:-1])] = line.split(' ')[-1]
        for idx ,(repo_version, repo_date) in enumerate(version_dict.items()):
            version = repo_version[:-7].split('-')[-1]
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
