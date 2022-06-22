#include <ios>
#include <iostream>
#include <ctype.h>
#include <sstream>
#include <stdio.h>
#include <vector>
#include <fstream>
#include <filesystem>
#include <set>
#include <algorithm>
#include <cstring>
#include "tlsh.h"
#include "tlsh_impl.h"
#include "global.h"

map<string, vector<DBTuple>> copied_OSS;
string repo_func_path;
string sorted_tlsh_path;
// std::mutex mtx;

struct Args {
  float theta;
  int score_thresh;
  string src_path;
  string result_path;
  string copy_summary_path;
  string rm_result_path;
  string config;
} args;

size_t tlsh_diffxlen(string &h1, string &h2) {
  Tlsh t1, t2;
  t1.fromTlshStr(h1.c_str());
  t2.fromTlshStr(h2.c_str());
  return t1.totalDiff(&t2, false);
}

DBTuple getDBTupleFromString(string &s) {
  int i1, i2, i3, i4, i5;
  string s1, s2, s3, s4, s5;
  i1 = s.find("*");
  s1 = s.substr(0, i1);
  s = s.substr(i1+1, s.length());
  i2 = s.find("*");
  s2 = s.substr(0, i2);
  s = s.substr(i2+1, s.length());
  i3 = s.find("*");
  s3 = s.substr(0, i3);
  s = s.substr(i3+1, s.length());
  i4 = s.find("*");
  s4 = s.substr(0, i4);
  s = s.substr(i4+1, s.length());
  i5 = s.find("*");
  s5 = s.substr(0, i5);
  s = s.substr(i5+1, s.length());
  return make_tuple(s1, s2, s3, s4, s5, stof(s));
}

void load_database(vector<DBTuple> &DB) {
  ifstream in;
  in.open(sorted_tlsh_path, ios::in);
  string item;
  size_t cnt = 0;
  while (getline(in, item)) {
    printf("\r%ld", cnt);
    DB.push_back(getDBTupleFromString(item));
    cnt ++;
  }
  in.close();
  putchar('\n');
}

void load_database(vector<DBTuple> &DB, vector<string> &repo_list) {
  int cnt = 1;
  int errcnt = 0;
  for (string& repo : repo_list) {
    printf("\r%.2f%%", (float)cnt / repo_list.size() * 100);
    ifstream in;
    in.open(repo_func_path + repo + ".txt", ios::in);
    if (!in.is_open()) {
      // puts("Error");
      errcnt ++;
      cnt ++;
      continue;
    }
    stringstream buffer;
    buffer << in.rdbuf();
    string item;
    while (getline(buffer, item)) {
      DB.push_back(getDBTupleFromString(item));
    }
    in.close();
    cnt ++;
  }
  printf("\n%d repos not found\n", errcnt);
}

int binary_search(vector<DBTuple> &DB, DBTuple &func) {
  // 可能有多个函数都有相同的tlsh值,返回最小的下标
  int left, right, mid;
  left = 0, right = DB.size()-1;
  while (left <= right) {
    mid = (left + right) >> 1;
    if (get<3>(DB[mid]) > get<3>(func)) {
      right = mid - 1;
    } else if (get<3>(DB[mid]) < get<3>(func)) {
      left = mid + 1;
    } else {
      while (mid >= 0) {
        if (get<3>(DB[mid]) != get<3>(func))
          break;
        mid--;
      }
      if (mid <= -1)
        return 0;
      return mid + 1;
    }
  }
  return -1;
}

bool check_prime(vector<DBTuple> &DB, string &S_name, vector<DBTuple> &S) {
  static size_t cnt = 0;
  bool isPrime = true;
  
  map<string, vector<DBTuple>> G;
  set<string> G_keys;

  for (auto &S_func : S) {
    // mtx.lock();
    printf("\r%.2f%%    %64s", (float)cnt / DB.size() * 100, S_name.c_str());
    // mtx.unlock();
    int index = binary_search(DB, S_func);
    if (index == -1) {
      printf("Binary search error: %s\n", get<2>(S_func).c_str());
      continue;
    }
    while (get<3>(DB[index]) == get<3>(S_func)) {
      if (get<0>(DB[index]) != get<0>(S_func) && get<4>(DB[index]) <= get<4>(S_func)) {
        if (G_keys.find(get<0>(DB[index])) == G_keys.end()) {
          G.insert(G.begin(), pair<string, vector<DBTuple>>(get<0>(DB[index]), vector<DBTuple>()));
          G_keys.insert(get<0>(DB[index]));
        }
        G.at(get<0>(DB[index])).push_back(S_func);
      }
      index ++;
    }
    // mtx.lock();
    cnt ++;
    // mtx.unlock();
  }

  for (auto repo_name : G_keys) {
    set<DBTuple> tmpset(G.at(repo_name).begin(), G.at(repo_name).end());
    G.at(repo_name).assign(tmpset.begin(), tmpset.end());
    float phi = float(G.at(repo_name).size()) / float(S.size());
    if (phi >= args.theta) {
      isPrime = false;
      copied_OSS.insert_or_assign(repo_name, G.at(repo_name));
    }
  }

  return isPrime;
}

bool tuple_ascend(DBTuple& t1, DBTuple &t2) {
  return get<3>(t1) < get<3>(t2);
}

void sort_tlsh(vector<DBTuple> &DB) {
  sort(DB.begin(), DB.end(), tuple_ascend);
  ofstream o;
  o.open("sorted_tlsh.txt", ios::out);
  constexpr int bufsize = 0x800000;
  char *buf = new char[bufsize];
  for (auto &i : DB) {
    snprintf(buf, bufsize, "%s*%s*%s*%s*%s*%.2f\n", get<0>(i).c_str(), get<1>(i).c_str(), get<2>(i).c_str(), get<3>(i).c_str(), get<4>(i).c_str(), get<5>(i));
    o.write(buf, strlen(buf));
  }
  o.close();
  delete[] buf;
}

void code_segmentation(vector<DBTuple> &DB, string &repo_name) {
  ifstream f;
  f.open(repo_func_path + repo_name + ".txt", ios::in);
  if (!f.is_open()) {
    return;
  }
  string item;
  vector<DBTuple> repo_funcs;
  while (getline(f, item)) {
    repo_funcs.push_back(getDBTupleFromString(item));
  }
  f.close();

  bool isPrime = check_prime(DB, repo_name, repo_funcs);

  if (!isPrime) {
    putchar('!');
    ofstream fsummary;
    fsummary.open(args.copy_summary_path + repo_name + ".txt", ios::out);
    for (auto &i : copied_OSS) {
      fsummary << i.first << ": " << i.second.size() << "\n";
      for (auto &func : i.second) {
        vector<DBTuple>::iterator it = repo_funcs.begin();
        for ( ; it != repo_funcs.end();) {
          if (*it == func) {
            it = repo_funcs.erase(it);
          } else {
            ++it;
          }
        }
      }
    }
    copied_OSS.clear();
    fsummary.close();

    ofstream fresult;
    fresult.open(args.rm_result_path + repo_name + ".txt", ios::out);
    for (auto &func : repo_funcs) {
      fresult << get<0>(func) << "*" << get<1>(func) << "*" << get<2>(func) << "*" << get<3>(func) << "*" << get<4>(func) << "*" << get<5>(func) << '\n';
    }
    fresult.close();
  } else {
    putchar('~');
  }
}


int main(int argc, char* argv[]) {
    args.copy_summary_path = "/home/syssec-py/CENTRIS_byt/c/copy_summary/";
    args.result_path = "/home/syssec-py/results_new/";
    args.score_thresh = 30;
    args.rm_result_path = "/home/syssec-py/CENTRIS_byt/c/results_rm/";
    args.config = "./config_1w-2w.txt";
    args.src_path = "repositories/";

  sorted_tlsh_path = "/home/syssec-py/sorted_tlsh.txt";

  std::ios_base::sync_with_stdio(false);

  repo_func_path = args.result_path + "repo_func/";

  #ifdef SORT
  filesystem::path dir(repo_func_path);
  filesystem::directory_entry entry(dir);
  filesystem::directory_iterator list(dir);
  vector<string> repo_list;
  for(auto &it : list) {
    string s = it.path().string();
    s = s.substr(0, s.find_last_of("."));
    s = s.substr(s.find_last_of("/")+1, s.length());
    repo_list.push_back(s);
  }
  #endif

  vector<DBTuple> DB;
  #ifdef SORT
  load_database(DB, repo_list);
  #endif

  #ifdef CODESEG
  load_database(DB);
  #endif

  printf("Database size: %ld\n", DB.size());

  #ifdef CODESEG
  for (auto &repo : repo_list) {
    code_segmentation(DB, repo);
  }
  #endif

  #ifdef SORT
  sort_tlsh(DB);
  #endif

  puts("Voilaaaaaaaa!");

  return 0;
}
