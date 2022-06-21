# CENTRIS

系统安全project

## 0. GitHub仓库的下载解压检测

所需代码放置于github目录下

运行collect.py生成一个记录着使用python语言的star数top 5000的GitHub仓库的下载链接的文本文件

运行main.py根据tmp.txt下载GitHub仓库源代码的压缩包

运行unzip.py将下载的GitHub仓库源代码解压



运行detector.py对每个GitHub仓库计算tlsh，排序后输出代码重用检测结果

## 1. Collector

`collector_main.py`和`OSSCollector.py`实现了collector的核心功能，分别是：根据给定的PyPI库名称下载其所有版本的源代码包，主要代码参考了GitHub上的开源项目[pypi-downloader](https://github.com/astamminger/pypi_downloader)；分析目标库的代码，并对其中定义的所有版本的所有函数计算TLSH哈希值。

为了指定想要下载的PyPI库，需要编写一个配置文件。由于我们需要的是源代码，配置文件格式如下：

```toml
[settings]
  cache_folder: repositories
  packagetypes: sdist
  python: py3

[packages]
  cn2an
  jedi_language_server
  google_cloud_talent
  ...
```

其中指定了下载的目标目录(`cache_folder`)、包类型(`sdist`)和Python版本。

为了运行collector，可以直接运行`main.py`，其中的`main_thread`函数会调用`collector_main`中定义的`build_package_cache`函数。

在主函数中会开启多线程，调用`main_thread`. `main_thread`所做的工作有：

1.   检查当前包是否已下载，如果已经下载则跳过。
2.   调用`build_package_cache`，将源代码压缩包下载到配置文件中缩写的路径，并在`results/repo_date/<repo_name>.txt`中记录每个版本与日期之间的对应关系。
3.   调用`tar.py`中定义的`Decompress_All`，解压下载路径下所有的压缩包。
4.   调用`OSSCollector.py`中定义的`analyze_file`，分析库代码函数并计算TLSH，保存在`results/repo_func/<repo_name>.txt`.
5.   删除刚刚下载的压缩包和加压后的文件。

## 2. Preprocessor

Preprocessor做两部分工作：找到Prime OSS和构建Detector需要的数据库。

### 2.1 计算Prime OSS

首先对Collector部分得到的所有函数根据TLSH值进行排序，保存在`sorted_tlsh.txt`中，再对每一个OSS的每一个函数在排好序的TLSH序列中进行二分查找。如果一个OSS的每一个函数仅有自己拥有，这说明这个OSS就是Prime OSS. 否则需要将其非独有的部分删除，把剩余部分保存在`results_rm/<repo_name>.txt`中，将复用的OSS个数保存在`copy_summary/<repo_name>.txt`中。

#### 运行方法

本部分代码使用C++实现，在`//c/`目录下。

1.   初次排序.

     ```shell
     make sort
     ./sort
     ```

     结果写在`sorted_tlsh.txt`中。

2.   计算Prime OSS.

     ```shell
     make codeseg
     ./codeseg
     ```

     结果会保存在`copy_summary/`和`results_rm/`中。

### 2.2 构建数据库

需要同时参考`results_rm`和`results`，对函数重新排序，将结果保存在`db.txt`中，此时数据库中保存的函数都是对应的OSS所独有的。

运行`python src/build_db_for_detector.py`，参数可以修改。

## 3. Detector
