import copy
import os
import tlsh
import parso
import tokenize
import io



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
                new_lines[start[0]-1] = new_lines[start[0] -
                                                  1][:start[1]] + new_lines[start[0]-1][end[1]:]
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


def parse(file_list):
    func_dict = {}
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
            try:
                func_str = TXTProcess().remov_comment(
                    func_str, lines[func.start - 1: func.end])
            except:
                pass
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
                func_dict[TLSH] = func.name

    return func_dict


def load_database():
    DataBase = []
    with open(os.path.join("/home/syssec-py", "sorted_tlsh.txt"), "r", encoding="utf-8") as f:
        for line in f:
            DataBase.append(tuple(line.strip().split('*')))
    return DataBase


def check_prime(DataBase, S):
    # S_name: S的名字
    # DataBase: 全局变量，保存所有函数

    isPrime = True

    G = {}  # 当前OSS中有哪些函数是抄的， {"repo_name": ["hash", ...], ...}
    copied_OSS = {}  # S抄了哪些OSS以及对应的函数名

    for hashval in S:
        # DBtuple/S_func - 0: repo_name  1: func_name  2: version_ids  3: hash_val  4: func_date  5: func_weight
        left = 0
        right = len(DataBase)-1
        mid = 0
        TLSH = None
        while left <= right:
            mid = int(left + (right-left)/2)
            if DataBase[mid][3] == hashval:
                TLSH = hashval
                break
            elif DataBase[mid][3] < hashval:
                left = mid + 1
            elif DataBase[mid][3] > hashval:
                right = mid - 1
        if TLSH is not None:
            # 找到了
            for offset in range(mid+1):
                if DataBase[mid-offset][3] == hashval:
                    if DataBase[mid-offset][0] not in G:
                        G[DataBase[mid-offset][0]] = []
                    G[DataBase[mid-offset][0]].append(DataBase[mid-offset])
                else:
                    break

            for offset in range(1, len(DataBase) - mid):
                if DataBase[mid+offset][3] == hashval:
                    if DataBase[mid+offset][0] not in G:
                        G[DataBase[mid+offset][0]] = []
                    G[DataBase[mid+offset][0]].append(DataBase[mid+offset])
                else:
                    break

    # members包含了抄的OSS名字
    for repo_name in G.keys():
        G[repo_name] = list(set(G[repo_name]))
        phi = float(len(G[repo_name])) / float(len(S))
        if phi >= 0.3:
            isPrime = False
            # 这里是返回copied_OSS(部分)还是G(全部)?
            copied_OSS[repo_name] = G[repo_name]

    if len(S) == 0:
        print("Error")
    else:
        print("isPrime =", isPrime)

    return isPrime, copied_OSS


def detector(DataBase):
    repo_base = "/home/syssec-py/github/repo_extracted"
    target_list = os.listdir(repo_base)
    for target in target_list:
        print("Analyzing %s..."%target, end = '')
        file_list = get_file(os.path.join(repo_base, target))  # 获取py文件列表
        repo_funcs = parse(file_list)   # TLSH: func_name
        isPrime, copied_OSS = check_prime(DataBase, repo_funcs)  # 检查S是否是抄的
    
        if isPrime is not True:
            with open("detector/detect_results/%s.txt" % target, "w") as f:
                for key, values in copied_OSS.items():
                    version_weight_dict = {}
                    f.write("-------------------------------------------------\n")
                    f.write("copy repository name: %s (%f), " % (key, float(len(copied_OSS[key]))/float(len(repo_funcs))))
                    for func in values:
                        versions = func[1].split(' ')
                        for version in versions:
                            if version not in version_weight_dict:
                                version_weight_dict[version] = float(func[5])
                            else:
                                version_weight_dict[version] += float(func[5])

                    version_weight_dict = sorted(
                        version_weight_dict.items(), key=lambda x: x[1], reverse=True)
                    f.write("version id: %s\n" %
                            version_weight_dict[0][0])
                    f.write("copied function number: %d\n" % len(values))
                    f.write("-------------------------------------------------\ncopied functions:\n")
                    for func in values:
                        f.write("\t%s\n" % func[2])
                    f.write("\n")
        print("finish %s" % target)
        

if __name__ == '__main__':
    print("Loading Database...", end='')
    DataBase = load_database()
    print("Finished!")

    detector(DataBase)
