# Task 1（网络拓展 / POINT 拓展）缺项与限制表

对照 Task2-1031 第 2 页「怎么算完成」与第 9 页「统一要求」。本表只覆盖任务 1；日期 2026-11-07。

## 1. 实际完成（阶段成果，已通过独立验证）

| 项 | 落点 | 验证 |
|---|---|---|
| ① 不等概率固定名额 | `randomized_arm_family/task1_assignment.py` `UnequalProbabilityFixedQuotaDesign`(+wire `…V1`) | `tests/test_task1_assignment_extensions.py`、`test_task1_backend_integration.py` |
| ② 按平衡规则重随机化 | 同上 `RerandomizedBalancedDesign`(+wire) | 同上 |
| ③ 固定权重暴露 | `task1_exposure.py` `WeightedExposureSpec` | `test_task1_supportengine_integration.py` |
| ④ 分组暴露 | 同上 `GroupedExposureSpec` | 同上 |
| 四类目标 | `task1_targets.py` `local_direct_mean`/`peer_spillover_mean`/`policy_mean`/`policy_contrast` | `test_task1_targets.py`（手算 oracle） |
| 关键查找（概率和=1、不可能=0、条件概率、正支持） | 组合表「关键查找验证」一节 | `test_task1_combination_lookup.py` |
| 独立 oracle（自写枚举，不调 SupportEngine） | `task1_verifier.py` | `test_task1_supportengine_integration.py` |
| 组合查找表 | `docs/task1_combination_lookup.md`（`examples/generate_task1_combination_lookup.py` 生成） | `test_task1_combination_lookup.py` |
| 证明与文档（三篇文献） | `docs/TASK1_POINT_EXTENSION_MATH_ZH.md` | — |
| 完整业务案例 | `examples/task1_business_case_reference.py` | `test_task1_business_case.py` |
| 新设计进 arm-mean 证书后端 | 单臂 `randomized_network_arm.py`、批量 `identification_batch.py`、组合 `identification_composition.py` | `test_task1_backend_integration.py` |
| 业务接入（adapter 路由 + 读取层） | `cfm_id/network_design_adapter.py`、`cfm_id_llm/network_design_reading.py`、`network_policy_reading.py` | 派单回归 |

## 2. 明确缺项（硬缺项）

| # | 缺项 | 当前边界 | 后续应怎样处理 |
|---|---|---|---|
| L1 | 加权/分组暴露（W/G）未进证书后端 | 只在内部精确层 `randomized_arm_family` 支持（`SupportEngine.joint_support` + `task1_targets`）；业务派单的 arm-mean 证书后端未接 W/G | 如需证书后端覆盖 W/G，需为 `ExposureSpec` 引入新暴露类型并接入单臂/批量/组合与 verifier；否则维持内部层边界 |
| L2 | 生产政策值后端（R1B/R2）未接入新设计 | 政策值/两政策差值的 POINT 识别由内部层 `task1_targets.policy_mean/policy_contrast` 覆盖（D1–D8 全支持）；生产 `identification_policy_r1b/r2.py` 走解析计数律，对新设计（D7/D8）未接入，已回退成干净边界（`COMPLETE_SUPPORTED_DESIGN_REQUIRED`） | 若需政策值/两政策差值在派单链对新设计出证书，须扩展 R1B/R2 的精确枚举路径；否则视为明确缺项 |
| L3 | 新设计精确支持依赖 N≤8 全排列枚举 | 无解析计数律；`N>8` 报不可处理，不猜测支持 | 推导新设计的条件计数律或引入抽样近似（须独立验证），当前不展开 |
| L4 | 数值 PFN Estimation 不在范围 | 任务只要求识别（POINT functional），估计（有限样本数值）不纳入 | 属 Estimation，非本任务；如需须独立契约 |
| L5 | 代码入口/扩展规则未更新 | `docs/DEVELOPMENT_ENTRY_ZH.md`、`docs/EXTENSION_MAINTENANCE_ZH.md` 尚未补任务 1 条目 | 按第 9 页要求补「实际完成/明确缺项/可复现方法/未解决项」 |
| L6 | literature_support 依据条目未补 | 三篇文献已在 `TASK1_POINT_EXTENSION_MATH_ZH.md` §8 引用全文；`literature_support/` 目录未建对应依据条目 | 可选（第 2 页「新设计不一定是新定理，优先复用已有定理」）；如需再补 `literature_support/routes/` |

## 3. 可复现方法

- 组合查找表：`python -m examples.generate_task1_combination_lookup` → 重写 `docs/task1_combination_lookup.md`（逐格运行真实 `SupportEngine` 与四类目标）。
- 业务案例：`python -m examples.task1_business_case_reference --output <dir> --allow-synthetic-reviews`。
- 已有示例回放：`python -m examples.student_handoff --output <dir> --allow-synthetic-reviews`、`python -m examples.network_design_exposure_reference --output <dir> --allow-synthetic-reviews`（120 例全 PASS）。
- 测试：`tests/test_task1_*.py`（6 个文件）覆盖穷举对拍、零支持、四类目标手算 oracle、证书篡改拒绝。

## 4. 未解决项（研究级，超出本机必做）

- `N>8` 的新设计解析计数律（或精确支持的一般化）。
- 任意 stochastic policy kernel（政策值只支持固定分配与有限认证混合）。
- 动态/未知图、多值或连续处理、时序干预。
- 观测网络（R3）对新设计/新暴露的条件分解。

## 5. 边界状态总结（回退后确认）

- **新设计 D7/D8**：已进 arm-mean 证书后端（effect/spillover → POINT，`independent_replay=true`），精确枚举 N≤8。
- **加权/分组暴露 W/G**：只在内部精确层，未进证书后端（见 L1）。
- **生产政策值后端 R1B/R2**：未接入新设计（见 L2）；政策值/两政策差值识别由内部层覆盖。

本表与 `docs/TASK1_POINT_EXTENSION_MATH_ZH.md`（数学合同）配套，是受限识别结果的边界声明，不构成对真实业务假设成立或实证效应大小的声明。
