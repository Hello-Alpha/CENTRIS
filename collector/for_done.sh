#!/bin/bash
#运行方法，在collector目录下./for_done.sh
#每次能够处理20个OSS
let "count=0"
ls ./cache > dir.log
cd cache
for var in `cat ../dir.log`
do
    mv $var ../../../../../f/syssec/cache
    if [ $count -lt 19 ]
    then
        let count+=1
    else
        let count=0
        cd ../../../../../f/syssec
        ./done.sh
        cd ../../e/vscode/CENTRIS/collector/cache
    fi
done
cd ../
rm dir.log

