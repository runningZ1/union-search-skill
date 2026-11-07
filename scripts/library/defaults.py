# 抓取任务默认参数；CLI 帮助与执行器共用。
# timeout 分别限制单项的网络请求和提取运算，等待空闲提取进程的时间不计入。
# 并发 32：提取进程数为 CPU 核数一半时吞吐最高，32 项同时请求足以让提取进程保持满负荷；更高并发只增加排队
DEFAULT_FETCH_OPTIONS = {"concurrency": 32, "per_host": 2, "timeout": 30}
