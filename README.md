# CENTRIS
系统安全project

## `main.py`主程序入口
首先需要配置一下`run.bat`，将`--config`, `--src_path`, `result_path`改成正确的路径，然后运行`.\run.bat`就好了QwQ

`main.py`负责CENTRIS整个流程：
- 下载一个包(项目的最新版本)
- 解压缩
- 计算哈希
- Code Segmentation
- ...

每个线程负责前三个任务，并在退出前，同时在标准输出和`done.log`中输出已经完成的项目名(已加锁)。运行`undone.py`可以输出没有完成的项目名。

### 下划线`"_"`相关
`config10000.txt`中列出了10001个项目名(不是正式的配置文件)，其中的`"-"`都被替换成了`"_"`，并且`cache`目录中对应的路径也被替换成了下划线，如`cache/charset_normalizer`.

`date.txt`中的源代码压缩包名、压缩包名中的下划线都没有替换。`date.txt`如下：
```
aiobotocore-2.3.2.tar.gz 2022-05-09T06:38:52
```

----

## collector

### 使用方法

编写配置文件，示例如config.

(new) 把文件整合到了`main.py`里，在Windows中直接`python main.py config`就可以了，Linux中使用`python3 main.py config` 

结果放在./cache中.

==与cache同级，先新建一个date文件夹==，date.txt会被重命名成OSS名，然后统一存放到date文件夹中

``Failed to request xxx''表示request失败，会被放进redo.log里。

Invalid package''表示包不存在或请求错误，不会重试。

### 注意事项

不能Ctrl-C中断，只能直接关掉命令行窗口或kill(QAQ).


### 配置信息

repos_5000.txt	包含了top5000的项目

config_full.txt		包含了全部项目



## preprocessor

### 使用方法

#### 多线程版本

`.\run.bat`

#### Old version

修改config.py中的--src_path参数，设置为解压之后的repo的文件夹，然后将main函数中的参数设为mode = "analyze_file"，continue_flag = True，最后运行main函数即可。

如果需要在命令行里可以将--src_path参数传入，具体方法可以百度argparse。

==**注意事项：可以以小批量分批次运行，每次运行的时候，需要清空results文件夹，如果需要断点功能，要将continue_flag设为True，在运行一个批次的时候就不要动results文件夹和repo_info.txt文件了，等一个批次运行完毕之后，要保存这个批次运行得到的results文件夹和repo_info.txt文件，不然会被覆盖掉！！**==



### main

```python
if mode == "analyze":
	分析repo构建数据库，将信息保存在数据库中
elif mode == "analyze_file":
    分析repo构建数据库，将信息保存在文件中
elif mode == "segment":
    OSS去重，保留prime部分
elif mode == "test":
    可以用于查看数据库
```



### 文件

config里保存了全局参数

main文件为主程序



repo_func_summary.txt记录了每个repo的函数数量（仅在analyze模式生成，当需要从断点处继续分析的时候不会生成）

copy_summary.txt里面保存了OSS抄的哪些OSS



### 从断点处继续分析

如果需要从断点重新分析，需要将mode设为mode == "analyze_file"。

如果想重新分析所有的repo，可以将continue_flag设置为False

一般地，如果想继续分析，可以将continue_flag设置True



##### 用于构建数据库的文件

repo_info：保存了所有repo的信息

results：每一个repo一个文件夹，里面保存了repo中函数信息



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
