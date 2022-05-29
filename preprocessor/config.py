import argparse

parser = argparse.ArgumentParser("centris")


parser.add_argument("--theta", type=float, default=0.1,
                    help="当前OSS与某个OSS函数重合程度的阈值")
parser.add_argument("--score_thresh", type=int,
                    default=30, help="TLSH近似程度的阈值")
parser.add_argument("--src_path", type=str,
                    default="E:\\centris\\repositories_test_400", help="所有repository的存储文件夹,建议使用绝对路径")

args = parser.parse_args()
