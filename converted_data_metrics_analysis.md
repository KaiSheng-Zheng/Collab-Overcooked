# converted_data.csv 指标说明与当前结果解读

本文档基于 `Collab-Overcooked/src/evaluation.py`、`eval_utils.py`、`organize_result.py` 和 `convert_result.py` 对 `eval_result/converted_data.csv` 的生成逻辑做说明，并解读当前 `qwen3-30b-a3b-instruct-2507` 的结果。

## 1. 数据生成链路

`converted_data.csv` 不是直接由环境日志生成，而是经过三层汇总：

1. `evaluation.py`
   读取 `data/<model>/<order>/experiment_*.json`，调用 `Evaluation.evaluate()`，为每个任务输出 `evaluation_result.json`。

2. `organize_result.py`
   从每个任务的 `evaluation_result.json` 中抽取任务级指标，写入 `eval_result/statistics_data.csv`。这一层的粒度是 `model + order`。

3. `convert_result.py`
   将 `statistics_data.csv` 按任务名称映射到 `level_1` 到 `level_6`，然后对同一 `model + level` 下的数值列做简单算术平均，生成 `converted_data.csv`。

因此，`converted_data.csv` 的每一行表示某个模型在某个难度 level 上的任务级均值，而不是按原始 episode 数加权后的均值。

## 2. Level 与任务分组

当前转换脚本使用固定分组：

| level | 任务类型 | 任务数 |
|---|---|---:|
| `level_1` | 单食材基础处理，例如烤甜薯、煮蘑菇 | 5 |
| `level_2` | 单食材切片/加工，例如烤土豆片、煮玉米片 | 5 |
| `level_3` | 汤类，例如烤蘑菇汤、烤南瓜汤 | 5 |
| `level_4` | stew 类复合任务 | 5 |
| `level_5` | mashed patty 类复合任务 | 5 |
| `level_6` | 多食材 patty 类复合任务 | 5 |

## 3. 字段含义

| 字段 | 含义 | 取值解释 |
|---|---|---|
| `model` | 被评测模型名 | 当前为 `qwen3-30b-a3b-instruct-2507` |
| `level` | 任务难度分组 | `level_1` 到 `level_6` |
| `success_rate` | 成功率 | 任务级成功率的 level 内平均值。单个任务成功的判定是日志中的 `total_order_finished` 非空 |
| `time_avg` | 平均完成时间 | 单个任务中，只统计成功 episode 的最后时间戳；若该任务没有成功，则为 0。level 层面是任务级 `time_avg` 的简单平均 |
| `time_var` | 完成时间波动 | 字段名叫 `var`，但代码实际使用 `np.std`，所以这是标准差，不是方差。level 层面同样是任务级标准差的简单平均 |
| `mean_f1_agent_0` / `mean_f1_agent_1` | agent 动作序列与参考流程的综合匹配分 | 越高越好，综合考虑参考动作覆盖程度和执行动作的紧凑程度 |
| `mean_similarity_agent_0` / `mean_similarity_agent_1` | 参考动作覆盖率 | 越高越好，表示执行序列覆盖参考序列前缀的比例 |
| `mean_redundancy_agent_0` / `mean_redundancy_agent_1` | 代码中的 `redundancy` 输出 | 注意：当前实现中它实际是 `max_depth / len(log_actions)`，更接近“执行动作中有多少比例匹配参考流程”。值越高通常表示动作越不冗余；不要按字段名理解成“越高越冗余” |
| `std_f1_agent_0` / `std_f1_agent_1` | F1 的任务内标准差 | 在 `statistics_data.csv` 中是同一任务多个 episode 的标准差；在 `converted_data.csv` 中是这些任务级标准差的平均 |
| `std_similarity_agent_0` / `std_similarity_agent_1` | similarity 的任务内标准差 | 同上 |
| `std_redundancy_agent_0` / `std_redundancy_agent_1` | redundancy 输出的任务内标准差 | 同上 |
| `initiate_collaboration` | 发起协作有效性 | 只统计发生通信的时间步。代码从发起方请求和响应方历史动作的参考流程增益中分类，值越高表示请求更常被判定为有助于协作 |
| `respond_collaboration` | 响应协作有效性 | 只统计发生通信的时间步。值越高表示响应方计划/动作更常被判定为有助于协作 |
| `overall_collaboration` | 总协作分 | `organize_result.py` 中定义为 `(initiate_collaboration + respond_collaboration) / 2` |

## 4. 动作匹配指标的计算口径

对单个 episode、单个 agent，评测会把实际动作序列和一个或多个参考动作序列比较。

设：

- `R` 为参考动作序列；
- `A` 为实际执行动作序列；
- `max_depth` 为从 `R` 的第一个动作开始，在 `A` 中按顺序能匹配到的最长参考前缀长度。实际序列中可以跳过多余动作，但参考序列不能跳过中间步骤；
- 若一个任务有多个参考流程，代码会选使 F1 最高的那个参考流程。

则当前实现的核心指标为：

```text
similarity = max_depth / len(R)
redundancy = max_depth / len(A)
f1 = (1 + beta^2) * max_depth / (len(R) + beta^2 * len(A))
beta = 0.95
```

这里的 `redundancy` 名称容易误导。按公式看，它不是“冗余动作比例”，而是实际动作序列中匹配参考流程的比例。值低通常意味着有较多动作没有贡献到参考流程匹配，或者流程中断较早。

## 5. 协作指标的计算口径

协作指标只看有通信的时间步。代码会：

1. 找到第一个非 `[NOTHING]` 发言的 agent 作为发起方；
2. 从发起方 `plan` 中解析 `request(...)`，得到请求动作 `R`；
3. 从响应方 `plan` 中解析非 `request`、非 `wait` 的动作，得到响应计划 `R_hat`；
4. 取响应方此前动作历史 `H`；
5. 用 `ites(seq_1, seq_2)` 比较两个序列相对参考流程的最佳 F1 差值：
   - `c_1 = ites(H + R, H)`：请求是否让响应方流程更接近参考；
   - `c_3 = ites(H + R_hat, H)`：响应计划是否让响应方流程更接近参考；
   - `c_2 = ites(H + R, H + R_hat)`：请求动作相对响应计划是否更贴近参考。

随后代码将这些 `c` 值映射到一个 confusion matrix，并计算 `initiate_collaboration` 与 `respond_collaboration`。这两个值都是 0 到 1，越高表示通信越常被判定为有效协作。

实现细节注意：当前代码主要依赖 `plan` 字段中的结构化 `request(...)`，纯自然语言 `say` 中的请求不一定会进入统计。

## 6. 当前结果概览

当前 `converted_data.csv` 只有一个模型：`qwen3-30b-a3b-instruct-2507`。

| level | success_rate | time_avg | agent_0 F1 | agent_1 F1 | overall_collaboration |
|---|---:|---:|---:|---:|---:|
| `level_1` | 0.833 | 33.2 | 0.837 | 0.679 | 0.453 |
| `level_2` | 1.000 | 35.4 | 0.968 | 0.826 | 0.445 |
| `level_3` | 0.600 | 50.8 | 0.573 | 0.514 | 0.316 |
| `level_4` | 0.000 | 0.0 | 0.418 | 0.350 | 0.233 |
| `level_5` | 0.000 | 0.0 | 0.426 | 0.403 | 0.271 |
| `level_6` | 0.000 | 0.0 | 0.276 | 0.370 | 0.243 |

## 7. 当前结果解读

### 7.1 成功率随任务复杂度明显下降

`level_2` 表现最好，成功率为 1.0，5 个任务全部成功。`level_1` 成功率为 0.833，主要被 `baked_bell_pepper` 的 0.5 和 `boiled_egg` 的 0.667 拉低。`level_3` 降到 0.6，说明汤类任务已经出现明显失败。

`level_4`、`level_5`、`level_6` 成功率全部为 0，表示当前模型在复合 stew 和 patty 任务上没有完成订单。这里的 `time_avg = 0` 不是“完成很快”，而是因为任务没有成功，代码将完成时间置为 0。

### 7.2 `level_2` 是当前最稳定的能力区间

`level_2` 不仅成功率最高，动作匹配也最高：

- `mean_f1_agent_0 = 0.968`
- `mean_f1_agent_1 = 0.826`
- 两个 agent 的 `mean_similarity` 都是 1.0

这说明在切片/加工类单食材任务中，两个 agent 基本能覆盖参考动作流程。agent_1 的 F1 低于 agent_0，主要来自动作紧凑性指标更低，即实际动作中有更多没有匹配到参考流程的部分。

### 7.3 汤类任务是明显分水岭

`level_3` 成功率为 0.6，且平均完成时间为 50.8。由于失败任务的 `time_avg` 被记为 0，若只看成功的 3 个汤类任务，完成时间实际更长：`baked_bell_pepper_soup` 为 94，`baked_mushroom_soup` 为 97，`baked_pumpkin_soup` 为 63。

动作匹配也同步下降：

- agent_0 F1 从 `level_2` 的 0.968 降到 0.573；
- agent_1 F1 从 `level_2` 的 0.826 降到 0.514。

这说明问题不只是时间变长，而是流程规划和动作分工已经开始偏离参考轨迹。

### 7.4 失败任务中仍有非零动作匹配，说明模型有部分流程知识

`level_4` 到 `level_6` 虽然成功率为 0，但 F1 和 similarity 并不为 0。这表示模型仍能执行部分正确步骤，只是没有完整完成任务。

例如 `level_4` 中 agent_1 的 `mean_similarity_agent_1 = 0.956`，但 `mean_redundancy_agent_1 = 0.207`、`mean_f1_agent_1 = 0.350`。按当前实现，这意味着 agent_1 经常能覆盖参考流程中的一些关键前缀动作，但实际动作序列里有大量没有贡献到匹配的动作，导致综合分低。

### 7.5 协作分整体偏低，且随难度上升下降

协作指标最高的两个 level 是：

- `level_1`: overall collaboration 0.453
- `level_2`: overall collaboration 0.445

从 `level_3` 开始降到 0.316，`level_4` 到 `level_6` 约为 0.23 到 0.27。说明在复杂任务中，通信虽然存在，但被评测代码判定为有效推进参考流程的比例较低。

`level_2` 的 `respond_collaboration = 0.530` 高于 `initiate_collaboration = 0.361`，说明响应方计划更常被判定为有效；而 `level_1` 两者接近。复杂 level 中两项都偏低，说明请求和响应都没有稳定转化为有效动作。

### 7.6 agent_0 与 agent_1 的角色表现不均衡

在 `level_1` 到 `level_3`，agent_0 的 F1 都高于 agent_1，尤其 `level_2` 差距明显。到了 `level_6`，agent_1 的 F1 反而高于 agent_0，但两者都较低。

这通常意味着当前模型对两个角色的动作空间、器具责任或任务分工掌握不均衡。尤其在高难度任务中，某个 agent 即使能执行部分动作，另一方没有同步完成互补步骤，也无法形成成功订单。

## 8. 结论

当前模型的能力边界比较清楚：

- 对 `level_1` 和 `level_2` 的基础/单食材加工任务已有较强完成能力；
- `level_2` 是当前最稳定的成功区间；
- `level_3` 汤类任务开始暴露长流程规划、器具操作和协作衔接问题；
- `level_4` 到 `level_6` 的复合任务全部失败，说明模型尚不能稳定处理多食材、多阶段、多 agent 配合的完整闭环；
- 协作分偏低，提示后续改进应重点关注结构化请求、响应计划是否真正转化为对方的有效动作。

