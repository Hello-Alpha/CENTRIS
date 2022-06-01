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
        mv "$var" `echo "$var" | sed 's/-/_/g'` 1>/dev/null 2>&1;
    fi
done

ls > dir.log #以package为名的文件夹，写入dir.log文件中
for i in $(cat dir.log)
do 
    if [ -d $i ]; then
    cd $i
    echo $i
    
    #解压缩tar.gz
    ls *.tar.gz 1>ls_gz.log 2>/dev/null
    for k in $(cat ls_gz.log)   
    do
        tar -zxf $k 1>/dev/null 2>&1
        rm $k
    done

    #解压缩tar.bz2
    ls *.tar.bz2 1>ls_bz2.log 2>/dev/null
    for k in $(cat ls_bz2.log)   
    do
        if grep "${k%%.tar.bz2*}.tar.gz" ls_gz.log 1>/dev/null 2>&1
        then 
            rm $k
            echo "repeated!$k"
        else
            tar -jxf $k 1>/dev/null 2>&1   
            rm $k
        fi
    done

    #解压缩zip
    ls *.zip 1>ls_zip.log 2>/dev/null
    for k in $(cat ls_zip.log)   
    do
        if grep "${k%%.zip*}.tar.gz" ls_gz.log 1>/dev/null 2>&1 
        then 
            rm $k
            echo "repeated!$k"
        else
            if grep "${k%%.zip*}.tar.bz2" ls_bz2.log 1>/dev/null 2>&1
            then 
                rm $k
                echo "repeated!$k"
            else
                unzip $k 1>/dev/null 2>&1
                rm $k
            fi
        fi
    done

    #解压缩tgz
    ls *.tgz 1>ls_tgz.log 2>/dev/null
    for k in $(cat ls_tgz.log)
    do
        if grep "${k%%.tgz*}.tar.gz" ls_gz.log 1>/dev/null 2>&1 
        then 
            rm $k
            echo "repeated!$k"
        else 
            if grep "${k%%.tgz*}.tar.bz2" ls_bz2.log 1>/dev/null 2>&1
            then 
                rm $k
                echo "repeated!$k"
            else
                if grep "${k%%.tgz}.zip" ls_zip.log 1>/dev/null 2>&1
                then
                    rm $k
                    echo "repeated!$k"
                else
                    tar -xvf $k 1>/dev/null 2>&1   
                    rm $k
                fi
            fi
        fi
    done
    rm ls_gz.log
    rm ls_bz2.log
    rm ls_zip.log
    rm ls_tgz.log

    #将子文件夹中解压缩后的文件名进行-到_的替换
    for var in `ls`
    do 
        if [ -d $var ]; then
            mv "$var" `echo "$var" | sed 's/-/_/g'` 1>/dev/null 2>&1;
        fi
    done
    cd ../
    fi
done  
rm dir.log
cd ../