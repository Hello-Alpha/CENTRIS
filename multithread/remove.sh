for dir in `ls`
do
	if [ -d $dir]
	then
		echo $dir
		cd $dir
		for i in `ls`
		do
			if [ -d $i ]
			then
				rm -r $i
			fi
		done
		cd ..
	fi
done

