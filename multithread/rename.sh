cd $1
echo $1
for dir in `ls`
do
	if [ -d $dir ]
	then
		mv $dir `echo $dir | sed 's/-/_/g'`
	fi
done
cd ..

