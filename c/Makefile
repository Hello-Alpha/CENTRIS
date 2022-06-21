all: src/main.cpp src/tlsh.cpp src/tlsh_util.cpp src/tlsh_impl.cpp
	g++ $^ -o codeseg.exe -std=c++17 -g -DMINGW -Iinclude

copy: src/find_copy.cpp
	g++ $^ -o find_copy -std=c++17 -g

.PHONY: clean
clean:
	rm codeseg.exe
