#!/bin/bash
#运行方法，在syssec目录下./done.sh
./tar.sh
cd preprocessor
python main.py
cd ../cache
ls > cache.log
for var in `cat cache.log`
do 
    if [ -d $var ]; then
        cd $var
        mv date.txt $var.txt
        mv $var.txt ../../date
        cd ../
    fi
done
rm cache.log
rm -rf ./*
cd ../preprocessor/results
for var in `ls`
do
    mv $var ../../final
done
cd ../../
