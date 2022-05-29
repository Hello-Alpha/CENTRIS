from config import args
from OSSCollector import *
from preporcessor import *

db, cursor = initDatabase(initTable=False)

cursor.execute("""select *
                from func;""")
repo_list = cursor.fetchall()

print("num_repo_list2 = %d"%len(repo_list))