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

bool check_prime(vector<DBTuple> &DB, string &S_name, vector<DBTuple> &S) {
  bool isPrime = true;
  
  map<string, vector<DBTuple>> G;
  set<string> G_keys;

  for (auto &DBtuple : DB) {
    if (get<0>(DBtuple) == S_name) {
      continue;
    }
    for (auto &S_func : S) {
      size_t score = tlsh_diffxlen(get<3>(S_func), get<3>(DBtuple));
      // cout << get<0>(S_func) << '\n';
      if (score < args.score_thresh) {
        if (get<4>(DBtuple) <= get<4>(S_func)) {
          if (G_keys.find(get<0>(DBtuple)) == G_keys.end()) {
            // DBtuple[0] not in G_keys
            // vector<DBTuple> DBV;
            G.insert(G.begin(), pair<string, vector<DBTuple>>(get<0>(DBtuple), vector<DBTuple>()));
            G_keys.insert(get<0>(DBtuple));
          }
          G.at(get<0>(DBtuple)).push_back(S_func);
        }
      }
    }
  }

  for (auto repo_name : G_keys) {
    set<DBTuple> tmpset(G.at(repo_name).begin(), G.at(repo_name).end());
    G.at(repo_name).assign(tmpset.begin(), tmpset.end());
    float phi = float(G.at(repo_name).size()) / float(S.size());
    if (phi >= args.theta) {
      isPrime = false;
      // copied_OSS.at(repo_name) = G.at(repo_name);
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
  o.open("out.txt", ios::out);
  char buf[512];
  for (auto &i : DB) {
    // o << get<0>(i) << "*" << get<1>(i) << "*" << get<2>(i) << "*" << get<3>(i) << "*" << get<4>(i) << "*" << get<5>(i) << 
    snprintf(buf, sizeof(buf), "%s*%s*%s*%s*%s*%.2f\n", get<0>(i).c_str(), get<1>(i).c_str(), get<2>(i).c_str(), get<3>(i).c_str(), get<4>(i).c_str(), get<5>(i));
    o.write(buf, strlen(buf));
  }
  o.close();
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
  printf("%s", repo_name.c_str());
  if (!isPrime) {
    puts("!");
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
    puts("~");
  }
}


int main(int argc, char* argv[]) {
  if (argc == 1) {
    args.copy_summary_path = "D:\\c\\copy_summary\\";
    args.result_path = "D:\\results\\";
    args.score_thresh = 30;
    args.rm_result_path = "D:\\c\\result_rm\\";
    args.config = ".\\config_1w-2w.txt";
    args.src_path = "D:\\repositories\\";
  } else {
    args.copy_summary_path = argv[1];
    args.result_path = argv[2];
    args.score_thresh = atof(argv[3]);
    args.rm_result_path = argv[4];
    args.config = argv[5];
    args.src_path = argv[6];
  }

  std::ios_base::sync_with_stdio(false);

  repo_func_path = args.result_path + "repo_func\\";
  filesystem::path dir(repo_func_path);
  filesystem::directory_entry entry(dir);
  filesystem::directory_iterator list(dir);
  vector<string> repo_list;
  for(auto &it : list) {
    string s = it.path().string();
    s = s.substr(0, s.find_last_of("."));
    s = s.substr(s.find_last_of("\\")+1, s.length());
    repo_list.push_back(s);
  }
  // ifstream in;
  // in.open(args.config, ios::in);
  // string item;
  // while(getline(in, item)) {
  //   repo_list.push_back(item);
  // }
  // in.close();

  vector<DBTuple> DB;
  load_database(DB, repo_list);
  printf("Database size: %lld\n", DB.size());
  // for (auto &repo : repo_list) {
  //   code_segmentation(DB, repo);
  // }
  sort_tlsh(DB);

  return 0;
}
