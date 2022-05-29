#!/bin/bash
#目录格式为
# src
#     lxml
#      lxml1.0.tar.gz
#      lxml1.1.tar.gz
#     request
#      request1.0.tar.gz
#      request1.1.tar.gz
#      request1.2.tar.gz
#     scrapy
#在src目录中./tar.sh即可

ls > dir.log #以package为名的文件夹，写入dir.log文件中
for i in $(cat dir.log)
do 
    if [ -d $i ]; then
    cd $i
    echo $i
    ls *.tar.gz 1>ls_gz.log 2>tar_error.log
    for k in $(cat ls_gz.log)   
    do
        tar -zxf $k & > /dev/null   
        rm $k
    done
    # rm ls_gz.log
    cd ..
    fi
done  
# rm dir.log

