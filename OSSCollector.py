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


def load_date(repo_name):
    repo_path = os.path.join(args.src_path, repo_name)
    repo_date_path = os.path.join(args.result_path, "repo_date")
    repo_list = []
    version_dict = {}  # 版本和日期的对应字典

    if not os.path.exists(os.path.join(repo_path, "date.txt")):
        print("Invalid repository: %s" % repo_name)
    else:
        shutil.copy(os.path.join(repo_path, "date.txt"), os.path.join(repo_date_path, "%s.txt" % repo_name))
        f = open(os.path.join(repo_path, "date.txt"), "r")
        f_lines = f.readlines()
        for line in f_lines:
            version_dict["".join(line.split(' ')[:-1])] = line.split(' ')[-1]

        version_list = []
        version_num = 0
        for repo_version, repo_date in version_dict.items():
            if repo_version[-4:] == '.zip':
                version = repo_version[len(repo_name) + 1:-4].replace('-', '_')
            elif repo_version[-4:] == '.tgz':
                version = repo_version[len(repo_name) + 1:-4].replace('-', '_')
            elif repo_version[-7:] == '.tar.gz':
                version = repo_version[len(repo_name) + 1:-7].replace('-', '_')
            elif repo_version[-8:] == '.tar.bz2':
                version = repo_version[len(repo_name) + 1:-8].replace('-', '_')
            else:
                version = None
                print("Invalid repo name: %s" % repo_version)

            if version is not None and version not in version_list:
                version_num += 1
                version_list.append(version)
                repo_date = repo_date.replace('T', ' ').strip()
                repo_list.append((repo_name, version, version_num, repo_date))

    return repo_list


def analyze_file(repo_name):
    repo_func_path = os.path.join(args.result_path, "repo_func")
    # 读取所有repo
    repo_list = load_date(repo_name)

    version_num = 0
    func_dict = {}

    # with tqdm(total=len(repo_list)) as pbar: # 显示进度条会很乱
    for repo in repo_list:
        cur_repo_name = repo[0]

        version_num += 1
        repo_path = os.path.join(args.src_path, repo[0], f'{repo[0]}_{repo[1]}')
        # print(repo_path)
        # repo_path = "%s\\%s\\%s_%s" % (args.src_path, repo[0], repo[0], repo[1])
        # 分析一个工程
        file_list = get_file(repo_path)  # 获取py文件列表
        if len(file_list) == 0:
            print("Invalid reponame: %s" % cur_repo_name)
        try:
            func_dict = parse(func_dict, repo[2], repo[3], file_list)  # 分析该项目中的所有文件
        except:
            # traceback.print_exc()
            pass

        # pbar.set_postfix(
        #     {"repo_name": repo[0], "version": repo[1], "func_num": len(func_dict)})
        # pbar.update()

    with open(os.path.join(repo_func_path, "%s.txt" % cur_repo_name), "w") as f_func:
        # 将函数插入数据库
        for hashval, func in func_dict.items():
            func_weight = math.log(float(version_num) / float(func.version_num))  # 以e为底数
            f_func.write("%s*%s*%s*%s*%s*%f\n" % (
            cur_repo_name, func.version_ids, func.func_name, hashval, func.func_date, func_weight))

    # print("-----------------------\nsummary:")
    # print("total function number = %d" % len(func_dict))
    # print("-----------------------")
