#!/bin/bash
#!/bin/bash
#目录格式为
# cache
#     lxml
#      lxml1.0.tar.gz
#      lxml1.1.tar.gz
#     request
#      request1.0.tar.gz
#      request1.1.tar.gz
#      request1.2.tar.gz
#     scrapy


ls > dir.log #以package为名的文件夹，写入dir.log文件中
for i in $(cat dir.log)
do 
    if [ -d $i ]; then
    cd $i
    echo $i
    ls | grep tar.gz > ls_gz.log
    ls | grep tar.bz2 > ls_bz2.log
    ls | grep .zip > ls_zip.log
    for k in $(cat ls_gz.log)   
    do
        tar -zxf $k & > /dev/null   
    done
    for k in $(cat ls_bz2.log)
    do
        tar -zxf $k & > /dev/null
    done
    for k in $(cat ls_zip.log)
    do
        unzip -zxf $k & > /dev/null
    done
    rm ls_gz.log
    rm ls_bz2.log
    rm ls_zip.log
    cd ..
    fi
done  
rm dir.log

