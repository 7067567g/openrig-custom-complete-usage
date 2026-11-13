[English](LLM-MISREAD-QUICKREF.md) | **简体中文**

# LLM 速查 — 常见用户误读

读者：读到简短人类指令的 LLM/agent。

目的：把模糊说法映射到正确层级和命令路径，并判断什么时候应该**先问，不要猜**。

## 0. 执行规则

1. 先把话分到某一层：
   - SCTG 协议/kit；
   - workflow-group 控制面；
   - OpenRig 执行面。
2. 检查当前上下文：仓库、已开 rig、workflow 实例、queue、最近命令。
3. 如果一句话可能落到**多个层**，或会改变成本/状态/不可逆动作，先问。
4. 问的时候给**具体选项**，不要只说“请澄清”。
5. 如果按假设继续，先用一句话说明假设。
6. 不要静默换层，也不要偷偷替换命令路径。

### 偏差阈值与提问预算

误差不大时允许模糊。优先做合理理解，并用一句话说明假设。提问是有限资源。

| 偏差 | 动作 |
|---|---|
| 只是措辞不同，同一层 | 继续；说明假设；**不要问** |
| 同一层，不同产物，可逆 | 继续；说明假设；**不要问** |
| 有歧义但低风险 | 选最可能含义；说明假设 |
| 跨层（SCTG ↔ workflow-group ↔ OpenRig） | 问**一个**合并问题 |
| 发布 / 删除 / teardown / 成本 / 凭证 | 问**一个**合并问题 |
| 用户说“10+ 轮”，但上下文是 step | 只有计数影响范围/关闭时才问**一个**问题 |

**提问预算**

- 每轮最多问 **1 个问题**。
- 低风险歧义不要连续追问。
- 有多个歧义时，只问最高风险的那个；其余选安全默认并说明假设。
- 仓库上下文、已开 rig、workflow 状态或最近命令已经能消除歧义时，不要问。
- 动作可逆且成本低时，先做；只有结果会误导或造成破坏时才问。


## 1. 总速查表

| 用户说法 | 可能含义 | 默认理解 | 何时必须问 |
|---|---|---|---|
| “使用 OpenRig” | 建 rig；开 seat；跑 workflow；SCTG 的昵称 | 有 spec/rig 才理解为跑 workflow | 没有 rig/workflow 上下文 |
| “跑个工作流” | workflow-group 轮次；OpenRig steps；只跑本地文档 | 有 spec 时理解为 `rig workflow run` | 没有 spec 或提到“轮” |
| “10 步 / 10 轮” | OpenRig steps；workflow-group rounds | 按用户明确说的单位 | 计数影响范围/关闭 |
| “自动化” | `rig workflow run`；手动 `rig send`；burner 队列 | `rig workflow run` | 没有 rig/spec 或说“无人值守” |
| “跑完了” | workflow completed；packet done；round closed；报告已验收 | 先查实际状态 | 状态不一致 |
| “上传 / 发布” | git push；GitHub release；公开内容；artifact 上传 | 有明确仓库/发布上下文才继续 | 任何公开发布动作 |
| “检查 / 审计” | spec validate；live run；内容审计；安全扫描 | 问是哪一层 | 没点名产物 |
| “脱敏” | 删密钥；删路径；重写历史；脱敏 transcript | 问目标 | 公开发布前 |
| “内存 / 资源” | cgroup 限制；主机压力；模型上下文 | 问是哪种资源 | 提到 OOM/限制 |
| “多轮” | workflow-group rounds；OpenRig rework loop | 有 `wf.py` 上下文时理解为 rounds | OpenRig workflow 上下文 |

## 2. “OpenRig”不是一个东西

| 用户可能指 | 正确映射 | LLM 动作 |
|---|---|---|
| “OpenRig 起个 team” | `rig up` / `rig create` | 建/启动 rig；不要声称 workflow 跑了 |
| “OpenRig 跑工作流” | `rig workflow run` | render/validate/run workflow |
| “OpenRig 发消息” | `rig send` | 人工/调试路径 |
| “OpenRig 调试” | `rig ps`、`queue`、`workflow show/trace` | 只读检查，不要盲改 |
| “OpenRig 就是我的 SCTG 工作流” | 用户昵称，不是 CLI | 先确认是控制面还是执行面 |

**询问模板**

> 你说的 OpenRig 是指：
> A. 起 rig / seat；B. 用 `rig workflow run` 跑工作流；C. 手动 `rig send` 调试；
> D. 你的 SCTG 工作流（不启动 OpenRig）？

## 3. “工作流”不是一个东西

| 说法 | 可能层级 | 检查 |
|---|---|---|
| “跑 workflow-group” | 控制面 | `wf.py`、PROJECT/STATUS |
| “跑 OpenRig workflow” | 执行面 | `workflow.yaml`、`rig workflow run` |
| “跑 SCTG 工作流” | 协议 + workflow-group | `sctg-kit`、`wf.py` |
| “跑多轮” | workflow-group rounds | `new-round`、STATUS-Round-n |
| “跑 12 步” | OpenRig steps | workflow spec `steps:` |

**询问模板**

> 你说的“工作流”是：
> A. workflow-group 的 12 轮；B. OpenRig 的 12 个 step；C. 两者组合？

## 4. “完成”不是一个东西

| 用户说“完成” | 要验证 |
|---|---|
| “workflow 完成” | `rig workflow show <id>` status completed |
| “packet 完成” | `rig queue show <qitem>` state done |
| “round 完成” | `wf.py doctor` / STATUS state |
| “报告完成” | 文件存在且有内容 |
| “验收通过” | 独立 review/decision，不是 packet closure |

**规则：** packet closure ≠ acceptance。不要只凭聊天说“完成”。

**询问模板**

> 你说的“完成”是指 workflow completed、packet done、round closed，还是报告已验收？

## 5. “自动化”不是一个东西

| 用户意图 | 命令路径 |
|---|---|
| 一个声明式 workflow 跟到终态 | `rig workflow run <spec>` |
| 手动和 seat 对话 | `rig send <seat>` |
| 批量长会话队列 | queue/burner 自动化 |
| 只跑本地文档轮次 | `wf.py` |

**没有 rig/spec 时先问**：是先建 rig，还是只跑 local-only。

## 6. “检查/审计”不是一个东西

| 检查类型 | 命令 |
|---|---|
| spec 语法 | `rig workflow validate <spec>` |
| 启动计划 | `rig up <spec> --plan` |
| live workflow 状态 | `rig workflow show/trace` |
| queue 状态 | `rig queue list/show` |
| 仓库内容 | `scripts/check_content.py` |
| 脱敏 | `scripts/check_sanitization.py` |
| 测试 | `make test` |

不要只跑其中一项就说“审计通过”。

## 7. “内存/资源”不是一个东西

| 说法 | 含义 |
|---|---|
| “内存限制” | cgroup `MemoryHigh/MemoryMax/MemorySwapMax` |
| “主机 OOM” | 系统级压力 / page cache |
| “上下文窗口” | 模型上下文，不是主机 RAM |
| “seat 太多” | 并发 + global slice |

**规则：** `MemoryHigh` 是 `MemoryMax` 内的软阈值；swap 单独计算，不可相加。

## 8. “上传/发布”不是一个东西

| 说法 | 动作 |
|---|---|
| “push” | git commit + push |
| “发布” | tag + GitHub release |
| “上传内容” | 发布文件/文档/示例 |
| “公开仓库” | 哪个仓：SCTG-public 还是 openrig-custom-complete-usage？ |
| “脱敏后上传” | 先跑脱敏 + history 扫描 |

**force-push、重写历史、删 tag、公开发布之前必须问。**

## 9. 澄清模板

用具体选项：

```text
你说的 X 是指：
A. ...
B. ...
C. ...
如果是 A，我会 ...；如果是 B，我会 ...
```

```text
这里有一个跨层歧义：你说的是 workflow-group 的 round，还是 OpenRig 的 step？
两者的计数和关闭方式不同。
```

```text
这个操作会改公开历史 / 删除 tag / 触发发布；请确认是否继续。
```

## 10. 快速分诊

```text
用户说法
  -> 提到 wf.py / PROJECT / round?       -> workflow-group 控制面
  -> 提到 rig / seat / queue / step?      -> OpenRig 执行面
  -> 提到 card / gate / submission?       -> SCTG kit
  -> 提到 publish / push / release?       -> 先问再动
  -> 跨层歧义?                            -> 用 A/B/C 选项问
  -> 同层且可逆?                          -> 继续 + 说明假设
```
