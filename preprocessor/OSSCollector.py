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
                new_lines[start[0]-1] = new_lines[start[0]
                                                  ][:start[1]] + new_lines[start[0]-1][end[1]:]
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


def parse(file_list):
    func_dict = {}
    func_num = 0

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

            # func_dict字典：{“funcHash”: (文件路径, 函数名)}
            if TLSH not in func_dict:
                func_dict[TLSH] = []
            func_dict[TLSH].append((file, func.name))

            # 更新记录
            func_num += 1

    return func_dict, func_num


def Analyze(db, cursor):
    # 读取所有repo
    cursor.execute("""select repo_name, repo_path, version, repo_date 
                    from repo""")
    repo_list = cursor.fetchall()
    total_func_num = 0
    with tqdm(total=len(repo_list)) as pbar:
        for idx, repo in enumerate(repo_list):
            # 分析一个工程
            file_list = get_file(repo[1])  # 获取py文件列表
            func_dict, func_num = parse(file_list)  # 分析该项目中的所有文件

            for hashval, functions in func_dict.items():
                try:
                    for func in functions:
                        # 执行sql语句
                        cursor.execute("""insert into func(
                                func_name, hash_val, repo_name, version, file_path, func_weight)
                                VALUES ('%s', '%s', '%s', '%s', '%s', 0.0)""" % (func[1], hashval, repo[0], repo[2], func[0]))
                        # 提交到数据库执行
                        db.commit()
                except:
                    traceback.print_exc()
                    # 如果发生错误则回滚
                    db.rollback()
            total_func_num += func_num
            pbar.set_postfix(
                {"cur_repo": repo[0], "cur_func_num": func_num, "total_func_num": total_func_num})
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
                        repo_path CHAR(100),
                        version CHAR(20),
                        repo_date DATE);""")

        cursor.execute("""create table func (
                        func_name CHAR(50),
                        hash_val CHAR(100),
                        repo_name CHAR(50),
                        version CHAR(20),
                        file_path CHAR(100),
                        func_weight FLOAT);""")

    return db, cursor


def SaveRepoInfo(db, cursor):
    repo_list = os.listdir(args.src_path)

    for repo_name in repo_list:
        repo_path = os.path.join(args.src_path, repo_name).replace("\\", "/")
        version = "1.0.0"
        repo_date = "2020.1.1"
        try:
            # 执行sql语句
            cursor.execute("""insert into repo(
                repo_name, repo_path, version, repo_date)
                VALUES ('%s', '%s', '%s', '%s')""" % (repo_name, repo_path, version, repo_date))
            # 提交到数据库执行
            db.commit()
        except:
            traceback.print_exc()
            # 如果发生错误则回滚
            db.rollback()
