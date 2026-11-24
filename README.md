# AnYanEval

面向模型与 agent 的十维基准。当前题集为第 50 版，每维满分 10，总分 100。

- [题目与随题材料](benchmark/tasks.json)
- [评分标准](benchmark/rubric.json)
- [Qwen 3.8 Flash-Next 逐题结果（第 47 版）](results/qwen3.8-flash-next.json)
- [评测执行说明](agent.md)

## 第 50 版算法校准

算法对抗（ALG-09）增加动态代价替换和条件查询。条件查询固定一个点的标签及全图加权余数，同时考查两个不同的最低总代价和并列方案计数。第 50 版算法题待候选模型复测。

## 第 49 版校准

- 算法对抗（ALG-08）的分量查询占 4 分，其余考查全图带权余数的最小代价、并列解计数和动态维护。
- 物理模拟沿用第 47 版的 PHY-04 原题、随题样例和评分标准。
- 三维建模（CAD-06）考查分体弯流道、可开关旁路和薄隔壁，验收截止时的默认网格和四组参数重建。

第 49 版 A6000 复测结果为算法对抗 9.5/10、三维建模 7.5/10。[复测结果](results/v49-a6000-2026-11-24.json) · [题集](benchmark/archive/v49/tasks.json) · [评分标准](benchmark/archive/v49/rubric.json)

## 第 48 版 A6000 复测

算法对抗 10/10、物理模拟 8/10、三维建模 9.5/10。[复测结果](results/v48-a6000-2026-11-23.json) · [题集](benchmark/archive/v48/tasks.json) · [评分标准](benchmark/archive/v48/rubric.json)

## Qwen 3.8 Flash-Next（第 47 版）

**58/100**，十维均分 **5.8/10**。
这次结果使用单个配对种子校准难度，采用 DeepSeek Harness。由 GPT-6.2 Astra max 对匿名提交独立评分。
每道题的评分标准在该次试跑前冻结。[第 47 版题集](benchmark/archive/v47/tasks.json) · [第 47 版评分标准](benchmark/archive/v47/rubric.json)
单题评测至多 20 分钟，达到截止时间的试卷按已交付的结果和可核验步骤给过程分。

当前发布的是已完成评分的校准快照。目标是总分约 35/100、十维均分 3–4/10。

| 维度 | 分数 / 10 |
| --- | ---: |
| 算法对抗 | 0 |
| 数学推理 | 2.5 |
| 科学研究 | 7 |
| 物理模拟 | 7.5 |
| 三维建模 | 9.5 |
| 长流程agent任务 | 4.5 |
| 文学写作 | 6.5 |
| 全栈开发 | 9 |
| 仓库修复 | 5.5 |
| 事实核验与证据溯源 | 6 |

仓库修复题可按题集中记录的实例 ID 和数据集提交定位官方问题。[SWE-bench Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified)
