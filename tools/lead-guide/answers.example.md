# OpenRig Lead onboarding answers

## 层级与单位 (`layers`)
- Q: SCTG、workflow-group、OpenRig 各是什么？它们之间是什么关系？
  A: SCTG 是协议/kit；workflow-group 是控制面，管目标、决策、轮次；OpenRig 是执行面，管 rig、seat、queue、workflow step。三者分层，不混用。
- Q: round 和 step 的区别是什么？packet done 和验收通过有什么区别？
  A: round 是 PMO→TDO→QA→MAIN 的一轮；step 是 OpenRig workflow 里的一个 packet。packet done 只表示队列项关闭，不等于验收通过；验收要有证据和独立 QA/决策。

## 治理层与别名 (`governance`)
- Q: 总指挥部、总参谋部、单独轮、医护中心各负责什么？
  A: 总指挥部管长运行轮/主支登记与冲突；总参谋部管思考类轮索引、评估和咨询；单独轮是一次性受控轮；医护中心做伤员分诊、隔离、标戳、只提案补丁和 RCA。
- Q: 如果用户说“组织部”，你怎么映射？遇到不认识的治理名词时你的动作是什么？
  A: 组织部映射到总指挥部。陌生名字先按职责维度匹配；能落到四层之一就按该层处理；像两层就看它读写 ROUND-REGISTRY 还是 THINKING-ROUNDS；匹配不到就先给 A/B/C/D 选项问一次，不新建第五层。

## 澄清门与阻断 (`flow`)
- Q: 自动多轮流程开始前和开始后，提问规则分别是什么？
  A: 开始前一次性合并澄清层级、单位、验收、不可逆动作、预算；开始后零提问，低风险歧义用默认值并记录假设。
- Q: 被阻塞时写什么状态？如果下一步是未授权的不可逆动作，你怎么办？
  A: 写 BLOCKED 或 NEED_MAIN 并继续能做的工作；未授权的不可逆动作先停下来写 blocker，不擅自执行。

## 安全、证据与补丁 (`safety`)
- Q: 哪些动作必须得到授权？哪些内容不能进入公开仓库？
  A: push/发布、删除、重写历史、teardown、花钱和不可逆动作必须授权。不能公开原始聊天正文、截图、token、密钥、设备标识、个人路径和私有日志。
- Q: 证据、独立 QA、补丁提案三者的边界是什么？
  A: 证据是可复核的命令/文件/哈希；独立 QA 只审查，不由实现者自审；补丁只提案，不自动应用，应用要另开修复轮并由 QA/MAIN 批准。

## 版本漂移与收口 (`version`)
- Q: 发现 OpenRig 主文档版本或哈希漂移时，你先做什么？
  A: 先停下引导，更新引导文件的 version.json、content-index 和 persona，重新固定版本/哈希，再继续；引导文件版本优先。
- Q: 你能复述 OpenRig 启动、检查和收口的最低动作吗？
  A: 启动后查 rig ps / queue / workflow show；确认 seat 和 packet 状态；收口按 archive → workflow abort/close → rig down → rig daemon stop，不把 packet done 当验收。
