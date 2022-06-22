codeseg: src/main.cpp src/tlsh.cpp src/tlsh_util.cpp src/tlsh_impl.cpp
	g++ $^ -o codeseg -std=c++17 -g -DMINGW -Iinclude -DCODESEG

sort: src/main.cpp src/tlsh.cpp src/tlsh_util.cpp src/tlsh_impl.cpp
	g++ $^ -o sort -std=c++17 -g -DMINGW -Iinclude -DSORT

copy: src/find_copy.cpp
	g++ $^ -o find_copy -std=c++17 -g

date: src/mod_date.cpp
	g++ $^ -o mod_date -std=c++17 -g -Iinclude

.IGNORE: clean
.PHONY: clean
clean:
	rm codeseg.exe codeseg
