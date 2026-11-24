# AnYanEval 评测说明

用同一题集版本、种子和 harness 比较候选模型。题集覆盖十个维度，每维满分 10 分。先按题内分项评分，再把同维的一题或两题相加，十维总分满分 100。

## 快速核对

在仓库根目录用 Python 3.9 或更新版本运行。`eval.py` 使用标准库。

```sh
python -X utf8 eval.py verify
```

命令检查当前题集和评分表的版本、题号及分值，再用结果所属版本的清单核对 SHA-256、维度和分数。默认核对第 47 版的 `results/qwen3.8-flash-next.json`，其中保留逐题得分、完成状态、耗时、模型调用数和交付文件数。可用 `verify --result FILE` 核对其他结果。

## 准备与运行

给每道题和每个种子的尝试创建独立工作区。以下命令写入随题材料，把模型输入存到工作区外。

```sh
python -X utf8 eval.py prepare SCI-03 --seed 7291 --workspace ../runs/SCI-03 --prompt-out ../runs/prompts/SCI-03-turn-1.txt
```

基线采用 Linux x86_64、Node.js 24.14.0 和 DeepSeek Harness 0.2.1-rc.3 的 `headless` 配置。用配置好模型接入的同版 harness 在隔离工作区读取准备好的提示。开启会话自动压缩，提供方使用原生上下文和回答预算。把模型、运行环境与种子写入运行记录。

单题的 20 分钟从第一轮开始计时。多轮题在对应轮开始前使用 `prepare --turn N` 写入该轮增量材料和提示，同一尝试续用原会话 ID 和工作区。达到截止时保存已交付产物和可核验步骤，交独立评审评过程分。服务故障的配对组用同题、同种子和同设置补跑。

仓库修复题需要单独准备冻结的第三方工作树。按 `benchmark/tasks.json` 的 `fixture` 找到数据集提交与实例，取该行的 `problem_statement`，并将仓库检出到 `base_commit`。用 `prepare --official-issue FILE` 加入原始问题。补丁与实际验证结果是交付物。判分使用同一固定实例的修复检查和回归检查。[SWE-bench Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified)

## 盲评与汇总

把候选提交及独立验收结果整理成匿名包交给 GPT-6.2 Astra max。保留题号、种子、每个分项的证据位置和给分理由。按 `benchmark/rubric.json` 打分，以 0.5 分为单位。评分确定后将匿名 ID 映射回对应尝试。

把一个模型的独立分项评分合并成 JSON 数组，结构见评分表的 `score_output`。默认汇总种子 7291。多种子复测时，为每个共同种子传一个 `--seed`。

```sh
python -X utf8 eval.py score ../runs/model-grades.json --seed 7291
```

缺失的评分在汇总中保留 `null`。实际达到截止且有可评分过程的尝试使用独立评审给出的分数，包括评审核实的零分。每个已评分试跑对应题集中的原题面与冻结评分标准。

## 更新评测包

有题面或评分变更时，将旧版 `tasks.json` 和 `rubric.json` 原样存入 `benchmark/archive/v版本号/`，再更新题集版本。用冻结后的评分标准重新测受影响的题，再更新配套结果与摘要。运行 `eval.py verify --result FILE` 后一起提交题集、评分表和相同版本的结果。当前公开的基线是一组固定种子的难度校准快照，目标是总分接近 35/100、十维均分 3–4/10。
