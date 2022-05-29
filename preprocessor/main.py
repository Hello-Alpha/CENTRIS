from config import args
from OSSCollector import *
from preporcessor import *


db, cursor = initDatabase(initTable=True)
SaveRepoInfo(db, cursor)

Analyze(db, cursor)

cursor.execute("""select *
                from func;""")
repo_list = cursor.fetchall()
print("num_repo_list1 = %d"%len(repo_list))

redundancyElimination(db, cursor)

cursor.execute("""select *
                from func;""")
repo_list = cursor.fetchall()
print("num_repo_list2 = %d"%len(repo_list))

# 关闭数据库连接
db.close()
