  SEC-bench 评估脚本分析

  1. 脚本层次结构

  run_secb.sh (顶层包装脚本)
      ↓ 调用
  evaluation/benchmarks/sec_bench/scripts/run_infer.sh (Shell脚本)
      ↓ 调用
  evaluation/benchmarks/sec_bench/run_infer.py (Python执行脚本)

  2. run_secb.sh 参数说明

  必需参数：
  - -m, --mode: 模式选择
    - poc: 生成漏洞概念验证（Proof of Concept）
    - patch: 生成修复补丁

  可选参数：
  - -l, --llm: LLM配置文件（默认：llm.sonnet）
  - -n, --num-instances: 评估实例数量（默认：200）
  - -i, --iterations: 最大迭代次数（默认：75）
  - -t, --label: 运行标签（默认：eval）
  - -w, --workers: 工作进程数（默认：1）

  3. 你的命令问题分析

  你的命令：
  ./run_secb.sh -m 20 -l llm.DMXAPI -c recent -i gpac.cve-2023-5586

  存在的问题：

  1. ❌ -m 20 → mode应该是 poc 或 patch，不是数字
  2. ❌ -c recent → 脚本不支持 -c 参数
  3. ❌ -i gpac.cve-2023-5586 → -i 是最大迭代次数，应该是数字，不是实例ID

  4. 正确的使用方式

  如果你想评估特定实例，应该这样做：

  方法1: 使用config.toml指定实例
  # 1. 创建 evaluation/benchmarks/sec_bench/config.toml
  # 内容：
  # selected_ids = ["gpac.cve-2023-5586"]

  # 2. 运行脚本
  ./run_secb.sh -m patch -l llm.DMXAPI -n 1 -i 75

  方法2: 直接修改Python脚本调用
  # 直接调用 run_infer.sh
  ./evaluation/benchmarks/sec_bench/scripts/run_infer.sh \
      llm.DMXAPI \
      HEAD \
      CodeActAgent \
      1 \
      75 \
      1 \
      SEC-bench/SEC-bench \
      eval \
      1.5 \
      patch

  5. 核心功能说明

  PoC模式 (poc):
  - 目标：生成能触发sanitizer错误的测试用例
  - Agent会探索代码库，分析漏洞，创建PoC文件
  - PoC文件保存在 /testcase 目录
  - 使用 secb repro 验证PoC是否触发错误

  Patch模式 (patch):
  - 目标：修复代码中的安全漏洞
  - Agent会分析bug报告，探索代码，实施修复
  - 使用 secb build 构建，secb repro 验证修复
  - 最终生成git patch

  6. 关键环境变量

  USE_HINT_TEXT=false        # 是否使用提示文本
  USE_INSTANCE_IMAGE=true    # 是否使用实例镜像
  RUN_WITH_BROWSING=false    # 是否启用浏览功能

  7. Docker镜像

  脚本使用特定的Docker镜像：
  hwiwonlee/secb.eval.x86_64.<instance_id>:poc
  hwiwonlee/secb.eval.x86_64.<instance_id>:patch


  # 这里是 OpenHands 执行 SEC-bench 基准测试的完整流程和定制说明：

  执行流程架构

  run_secb.sh (入口)
      ↓ 解析参数 (mode, llm, num-instances, iterations等)
      ↓
  evaluation/benchmarks/sec_bench/scripts/run_infer.sh
      ↓ 设置环境变量和运行配置
      ↓ 调用 poetry run python
      ↓
  evaluation/benchmarks/sec_bench/run_infer.py
      ↓ 核心评估逻辑
      ├── get_instruction() - 生成提示词
      ├── initialize_runtime() - 初始化运行环境
      ├── run_controller() - 执行 OpenHands agent
      └── complete_runtime() - 收集结果

  核心定制点

  1. 提示词定制 (run_infer.py:152-242)

  在 get_instruction() 函数中，根据任务类型生成不同的提示词：

  PoC 模式提示词 (run_infer.py:160-201):
  # 5步工作流
  1. EXPLORATION - 探索代码库结构
  2. ANALYSIS - 分析漏洞触发路径
  3. POC DEVELOPMENT - 创建 PoC 文件
  4. VERIFICATION - 运行 secb repro 验证
  5. POC REFINEMENT - 迭代优化

  Patch 模式提示词 (run_infer.py:202-236):
  # 5步工作流
  1. EXPLORATION - 探索代码库
  2. ANALYSIS - 分析漏洞并提出2-3种修复方案
  3. IMPLEMENTATION - 实现最小化修复
  4. VERIFICATION - secb build + secb repro 验证
  5. FINAL REVIEW - 最终审查

  2. 环境变量控制 (run_infer.sh:34-99)

  USE_INSTANCE_IMAGE=true   # 使用实例特定的Docker镜像
  RUN_WITH_BROWSING=false   # 是否启用浏览器
  USE_HINT_TEXT=false       # 是否使用提示文本

  3. 运行时初始化 (run_infer.py:328-481)

  initialize_runtime() 函数执行：
  - 设置环境变量 (SECB_INSTANCE_ID, SECB_WORK_DIR)
  - 注入实例数据到 /secb_util/eval_data/instances/
  - 执行 instance_secb_entry.sh 初始化脚本
  - 运行 secb repro 验证环境

  4. 结果收集 (run_infer.py:483-654)

  complete_runtime() 函数根据任务类型：
  - PoC模式: 收集 /testcase 目录下的 PoC 文件，压缩为 base64
  - Patch模式: 生成 git diff patch

  关键文件说明

  | 文件                     | 作用              | 关键代码行                                    |
  |------------------------|-----------------|------------------------------------------|
  | run_secb.sh            | 用户入口，参数解析       | 110-119 (mode分发)                         |
  | run_infer.sh           | 环境配置，调用Python   | 100-120 (run_eval函数)                     |
  | run_infer.py           | 核心：提示词+工作流+评估逻辑 | 152-242 (提示词)328-481 (初始化)483-654 (结果收集) |
  | instance_secb_entry.sh | 容器内初始化脚本        | 注入实例数据                                   |
  | config.toml            | 任务筛选配置          | selected_ids                             |

  主要定制内容总结

  ✅ 有修改工作流：
  - 在 get_instruction() 中定义了详细的5步工作流
  - 针对 PoC 和 Patch 两种模式有不同的流程

  ✅ 有修改提示词：
  - PoC 模式：强调使用 Python 脚本精确构建 PoC，使用 secb repro 验证
  - Patch 模式：要求提出多个方案，选择最优方案，最小化修改
  - 两种模式都禁止浏览网页（如果 RUN_WITH_BROWSING=false）

  ✅ 特殊机制：
  - 使用专门的 Docker 镜像 (hwiwonlee/secb.eval.x86_64)
  - 集成 secb 命令行工具 (build/repro)
  - 自动提取 sanitizer 报告 (run_infer.py:75-130)

  你可以通过修改 run_infer.py 中的 get_instruction() 函数来调整提示词策略。