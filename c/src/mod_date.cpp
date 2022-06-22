#include "global.h"
#include <iomanip>
#include <iostream>
#include <fstream>
#include <ostream>
#include <string>
#include <tuple>
#include <vector>
#include <filesystem>
#include <algorithm>

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

bool date_ascend(pair<string, string> &p1, pair<string, string> &p2) {
  return p1.second < p2.second;
}

void split_version_id(vector<int> &ids, string &s) {
  string t = s;
  while (!t.empty()) {
    int i = t.find(' ');
    if (i != -1)
      ids.push_back(stoi(t.substr(0, i)));
    else {
      ids.push_back(stoi(t));
      break;
    }
    t = t.substr(i+1, t.length());
  }
}

int main() {
  string repo_in_path = "./results/";
  string repo_out_path = "./results_new/";
  string repo_func_in_path = repo_in_path + "repo_func/";
  string repo_date_in_path = repo_in_path + "repo_date/";
  string repo_func_out_path = repo_out_path + "repo_func/";
  string repo_date_out_path = repo_out_path + "repo_date/";

  filesystem::path dir(repo_func_in_path);
  filesystem::directory_entry entry(dir);
  filesystem::directory_iterator list(dir);

  for(auto &it : list) {
    string s = it.path().string();
    s = s.substr(0, s.find_last_of("."));
    s = s.substr(s.find_last_of("/")+1, s.length());

    cout << s << endl;
    
    ifstream datein, funcin;
    datein.open(repo_date_in_path + s + ".txt", ios::in);
    funcin.open(repo_func_in_path + s + ".txt", ios::in);
    if (!datein.is_open() || !funcin.is_open()) {
      cout << "Failed to open " << s << endl;
      continue;
    }
    ofstream dateout, funcout;
    dateout.open(repo_date_out_path + s + ".txt", ios::out);
    funcout.open(repo_func_out_path + s + ".txt", ios::out);
    vector<pair<string, string>> old_dates;
    vector<DBTuple> funcs;
    string date, func;
    while (getline(datein, date)) {
      int tmp = date.find_first_of(" ");
      old_dates.emplace_back(date.substr(0, tmp), date.substr(tmp+1, date.length()));
    }
    while (getline(funcin, func)) {
      funcs.push_back(getDBTupleFromString(func));
    }
    vector<pair<string, string>> new_dates(old_dates);
    sort(new_dates.begin(), new_dates.end(), date_ascend);

    for (auto &f : funcs) {
      vector<int> ids;
      split_version_id(ids, get<1>(f));
      vector<int> newids;
      for (int id : ids) {
        int i;
        vector<pair<string, string>>::iterator it = find(new_dates.begin(), new_dates.end(), old_dates[id-1]);
        newids.push_back(it - new_dates.begin() + 1);
      }
      sort(newids.begin(), newids.end());
      string newid;
      for (int i : newids) {
        newid += to_string(i) + ' ';
      }
      if (!newid.empty())
        newid.pop_back();
      get<1>(f) = newid;
    }

    for (auto &d : new_dates) {
      dateout << d.first << ' ' << d.second << endl;
    }

    for (auto &f : funcs) {
      funcout << get<0>(f) << "*" << get<1>(f) << "*" << get<2>(f) << "*" << get<3>(f) << "*" << get<4>(f) << "*" << get<5>(f) << endl;
    }

    dateout.close();
    funcout.close();

    datein.close();
    funcin.close();
  }

  return 0;
}
