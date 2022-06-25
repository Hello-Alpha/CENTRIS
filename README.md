# Notice

在个人电脑上运行时要小心：
- 不能开启太多进程，需要调整代码
- 不要一次性下载10w个PyPI包
- 内存占用可能会达到11.8+ GB

请注意：

- 运行时请修改路径。为方便，代码中多处是绝对路径。

- Python代码可能需要安装依赖包，需要手动下载(推荐使用`pip`)

  py-tlsh, parso, tokenize, retry, tqdm.

# How to run

## Collector

首先需要配置`run.bat`，修改配置文件、临时repo路径和结果保存的路径，示例如下：

```shell
python src/main.py --config config.txt --src_path /home/syssec-py/demo/repositories --result_path /home/syssec-py/demo/results
```

配置文件中保存的是PyPI包名，示例如下。其中`cache_folder`需要与`run.bat`中的`src_path`保持一致。

```toml
[settings]
  cache_folder: repositories
  packagetypes: sdist
  python: py3

[packages]
  plugin_sdk_automation
  stoneredis
  pyspyne
  steadymark
```

在工程根目录下运行`run.bat`，结果会保存在`result_path`中。

```shell
sh run.bat
```

## Preprocessor

### 修改版本ID

在`preprocessor`目录下编译修改版本ID的程序，会生成`mod_date`:

```shell
make date
```

运行前需要先手动创建好与`result_path`同级的`results_new`目录，其中包含`repo_date`和`repo_func`子目录。

将`mod_date`复制到与`result_path`同级的目录下并运行。

### 排序

在`preprocessor`目录下编译排序程序，生成`sort`. 编译前可能需要修改源代码中的路径。

```shell
make sort
```

运行`sort`，得到`sorted_tlsh.txt`.

### Code Segmentation

在`preprocessor`目录下编译，生成`codeseg`.

```shell
make codeseg
```

在运行前需要手动创建好与源代码中对应路径的`results_rm`和`copy_summary`. 运行`codeseg`，结果会保存在这两个路径中。

### 构建OSS数据库

在`preprocessor`路径下运行`build_db_for_detector.py`.

得到`db.txt`，将其保存在某路径下备用。

## Detector

在`detection`路径下，首先准备好待检测工程。或者也可以在`github.txt`中指定github链接，通过`main.py`下载、`unzip.py`解压。

最后运行`detector.py`，结果保存在`detect_results`中。

## Notes on Data

`results`和`results.tar.gz`是下载后的结果，但是版本号有问题。
`results_new`和`results_new.tar.gz`是改正后的数据库。
`sorted_tlsh.txt`是对tlsh排序后的临时OSS数据库。
`db.txt`是最终的OSS数据库。

