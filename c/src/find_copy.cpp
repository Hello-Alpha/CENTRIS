#include "global.h"
#include <iomanip>
#include <iostream>
#include <exception>
#include <fstream>
#include <ostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

using namespace std;

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

// no trailing '\n'
void outputTuple(ostream& o, DBTuple &tuple) {
  o << get<0>(tuple) << "*" << get<1>(tuple) << "*" << get<2>(tuple) << "*" << get<3>(tuple) << "*" << get<4>(tuple) << "*" << get<5>(tuple);
}

int main(void) {
  ifstream in;
  in.open("D:\\c\\sorted_tlsh.txt", ios::in);
  string item;

  vector<DBTuple> DB;
  // int cnt = 1;
  while(getline(in, item)) {
    // cout << '\r' << cnt;
    try {
      DB.push_back(getDBTupleFromString(item));
    } catch (exception &e) {
      cout << e.what() << endl;
    }
    // cnt ++;
  }
  cout << endl;
  in.close();
  cout << "Reading finished" << endl;

  int cur = 0;

  // 找到两两抄的repo
  unordered_map<string, unordered_set<string>> copied;
  while (cur < DB.size()) {
    cout << "\r" << setprecision(2) << (float)cur / DB.size() * 100 << "%";
    int next = cur + 1;
    while (next < DB.size() && get<3>(DB[cur]) == get<3>(DB[next])) {
      // A与B有重合，则双向都写
      if (copied.find(get<0>(DB[cur])) == copied.end()) {
        copied.insert_or_assign(get<0>(DB[cur]), unordered_set<string>());
      }
      if (copied.find(get<0>(DB[next])) == copied.end()) {
        copied.insert_or_assign(get<0>(DB[next]), unordered_set<string>());
      }
      copied.at(get<0>(DB[cur])).emplace(get<0>(DB[next]));
      copied.at(get<0>(DB[next])).emplace(get<0>(DB[cur]));
      next ++;
    }

    cur = next;
  }

  // 遍历map，以被抄的为索引
  for (auto &i : copied) {
    ofstream o;
    o.open("D:\\c\\copied\\" + i.first + ".txt", ios::out);
    for (auto &j : i.second) {
      o << j << endl;
    }
    o.close();
  }

  return 0;  
}
