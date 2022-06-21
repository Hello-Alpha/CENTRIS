#ifndef _GLOBAL_H_
#define _GLOBAL_H_

#include <string>
#include <tuple>
#include <map>
#include <vector>

using namespace std;

// 0: repo ; 1: version id ; 2: function name ; 3: hash ; 4: date ; 5: weight
// aadict*1*test_base*D6B012320C934CA2F13B172D48AE0C0FC82E8D12040D341D8639130FB56740C64CACB1*2016-11-12 17:07:33*0
typedef tuple<string, string, string, string, string, float> DBTuple;

#endif

