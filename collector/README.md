## 使用方法
编写配置文件，示例如config.

(new) 把文件整合到了`main.py`里，直接`python main.py config`就可以了\~

结果放在./cache中.
在cache文件夹下`sh tar.sh`解压缩.

``Failed to request xxx''表示request失败，会被放进redo.log里。

Invalid package''表示包不存在或请求错误，不会重试。

## 注意事项
不能Ctrl-C中断，只能直接关掉命令行窗口或kill(QAQ).

Windows:
推荐使用python virtual environment(不用问题也不大)
```bash
pip install virtualenv
python -m venv env
env\Scripts\activate.ps1
```
之后就建立好虚拟环境了~
删除venv只要删掉env文件夹就好了~

