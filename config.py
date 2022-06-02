import argparse

parser = argparse.ArgumentParser("centris")


parser.add_argument("--theta", type=float, default=0.1,
                    help="当前OSS与某个OSS函数重合程度的阈值")
parser.add_argument("--score_thresh", type=int,
                    default=30, help="TLSH近似程度的阈值")
parser.add_argument("--src_path", type=str,
                    default="repositories", help="所有repository的存储文件夹,建议使用绝对路径")
parser.add_argument("--result_path", type=str,
                    default="results", help="repo分析之后文件的存储文件夹,建议使用绝对路径")
parser.add_argument("--copy_summary_path", type=str,
                    default="copy_summary", help="OSS去重时生成，记录了OSS的copy信息")
parser.add_argument("--rm_result_path", type=str,
                    default="results_rm", help="去重后的OSS函数")
parser.add_argument("--config", type=str,
                    default="config.txt", help="配置文件")
args = parser.parse_args()

