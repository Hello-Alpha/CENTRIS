from config import args
from OSSCollector import *
from preporcessor import *


db, cursor = initDatabase(initTable=True)
SaveRepoInfo(db, cursor)    # 保存repo信息

Analyze(db, cursor) # 分析每一个repo，冗余消除

cursor.execute("""select *
                from func;""")
repo_list = cursor.fetchall()
print("num_repo_list1 = %d"%len(repo_list))

# redundancyElimination(db, cursor)
#
# cursor.execute("""select *
#                 from func;""")
# repo_list = cursor.fetchall()
# print("num_repo_list2 = %d"%len(repo_list))

# 关闭数据库连接
db.close()
