### 文件

config里保存了全局参数

main文件为主程序



repo_func_summary.txt记录了每个repo的函数数量

copy_summary.txt里面保存了OSS抄的哪些OSS



### 数据库

##### repo表

repo_name CHAR(50),	项目名
version VARCHAR(40),	版本号
version_id INT,		版本id，从1开始计算
repo_date DATETIME	该版本的日期



##### func表

repo_name CHAR(50),		项目名
version_ids VARCHAR(200),	函数出现在的版本id集合
func_name VARCHAR(100),	函数名
hash_val CHAR(100),		函数哈希值
func_date DATETIME,		函数最初出现的时间
func_weight FLOAT		函数权重