#!/bin/bash
#目录格式为
#collector
    # cache
    #     lxml
    #      lxml1.0.tar.gz
    #      lxml1.1.tar.gz
    #     request
    #      request1.0.tar.gz
    #      request1.1.tar.gz
    #      request1.2.tar.gz
    #     scrapy

#运行方法，在collector目录下./tar.sh
cd cache
#将cache文件夹中的文件名进行-到_的替换
for var in `ls`
do 
    if [ -d $var ]; then
        mv "$var" `echo "$var" | sed 's/-/_/g'` 1>cache_shift.log 2>cache_shift_error.log;
    fi
done
rm cache_shift.log
rm cache_shift_error.log
ls > dir.log #以package为名的文件夹，写入dir.log文件中
for i in $(cat dir.log)
do 
    if [ -d $i ]; then
    cd $i
    echo $i

    #解压缩tar.gz
    ls *.tar.gz 1>ls_gz.log 2>gz_error.log
    for k in $(cat ls_gz.log)   
    do
        tar -zxf $k 1>/dev/null 2>&1
        rm $k
    done

    #解压缩tar.bz2
    ls *.tar.bz2 1>ls_bz2.log 2>bz2_error.log
    for k in $(cat ls_bz2.log)   
    do
        tar -jxf $k 1>/dev/null 2>&1   
        rm $k
    done

    #解压缩zip
    ls *.zip 1>ls_zip.log 2>zip_error.log
    for k in $(cat ls_zip.log)   
    do
        unzip $k 1>/dev/null 2>&1
        rm $k
    done
    rm ls_gz.log
    rm gz_error.log
    rm ls_bz2.log
    rm bz2_error.log
    rm ls_zip.log
    rm zip_error.log
    
    #将子文件夹中解压缩后的文件名进行-到_的替换
    for var in `ls`
    do 
        if [ -d $var ]; then
            mv "$var" `echo "$var" | sed 's/-/_/g'` 1>/dev/null 2>&1;
        fi
    done
    cd ..
    fi
done  
rm dir.log

