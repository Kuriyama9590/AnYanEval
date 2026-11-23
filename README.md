# AnYanEval

面向模型与 agent 的十维基准。题集版本 47，每维满分 10，总分 100。

- [题目与随题材料](benchmark/tasks.json)
- [评分标准](benchmark/rubric.json)
- [Qwen 3.8 Flash-Next 逐题结果](results/qwen3.8-flash-next.json)
- [评测执行说明](agent.md)

## Qwen 3.8 Flash-Next

**58/100**，十维均分 **5.8/10**。
这次结果使用单个配对种子校准难度，采用 DeepSeek Harness。由 GPT-6.2 Astra max 对匿名提交独立评分。
题集版本由该模型的试跑逐轮校准，每道题的评分标准在该次试跑前冻结。
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
