# CENTRIS
系统安全project



## collector

### 使用方法

编写配置文件，示例如config.

(new) 把文件整合到了`main.py`里，直接`python3 main.py config`就可以了\~

结果放在./cache中.
在collector文件夹下`./tar.sh`解压缩.

``Failed to request xxx''表示request失败，会被放进redo.log里。

Invalid package''表示包不存在或请求错误，不会重试。

### 注意事项

不能Ctrl-C中断，只能直接关掉命令行窗口或kill(QAQ).



在src目录下使用`tar.sh`对收集的pypi库文件进行重命名&解压

（linux下需要先`sudo apt in`）

### 配置信息

repos_5000.txt	包含了top5000的项目

config_full.txt		包含了全部项目



## preprocessor

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
