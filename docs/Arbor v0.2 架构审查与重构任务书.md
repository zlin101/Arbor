# Arbor v0.2 架构审查与重构任务书

仓库：

`https://github.com/zlin101/Arbor`

## 1. 任务目标

请对 Arbor 当前第一版进行一次完整的架构审查和重构。

重点不是讨论：

- 第一版哪些功能应该做；
- 哪些功能暂时不应该做；
- 是否需要继续堆更多能力。

重点是：

> 在 Arbor 当前产品目标和功能方向基本成立的前提下，检查现有实现、协议、Skill、Reviewer、Contract、跨平台适配和验收体系有没有结构性问题，并把它优化成一个更稳定、更一致、更容易长期演进的 Agent-native review protocol。

不要为了“架构漂亮”进行大规模重写。

优先采用：

> surgical refactor：保留正确的骨架，只重构真正存在语义、协议、边界或可维护性问题的部分。

---

# 2. 首先重新审查，不要直接相信下面的结论

开始修改前，请完整阅读：

- root README；
- `.agents/`；
- `.claude-plugin/`；
- `plugins/dual-review-loop/`；
- 所有 `SKILL.md`；
- reviewer agent definitions；
- references；
- plugin manifests；
- acceptance / spec / architecture docs；
- 当前测试、CI、脚本，如果存在。

然后自行判断下面列出的所有问题是否真实存在。

要求：

> 不允许因为这份任务书说某处有问题，就直接修改。

必须先通过当前代码和 contract 验证。

如果你认为某个判断不成立，请明确说明原因，并保留原设计。

---

# 3. 当前设计中应尽量保留的核心原则

Arbor 当前最有价值的部分不是目录结构，而是 review protocol。

除非经过充分论证，否则不要破坏以下原则：

1. Frozen scope / stable baseline
2. 两个不同 review lens
3. Reviewer fresh context
4. Reviewer read-only
5. Reviewer 不看到 prior reviewer findings
6. Same scope materialization
7. Root-cause-level finding deduplication
8. Single writer
9. Validation after fixes
10. Fresh full-scope re-review
11. Bounded convergence
12. No-progress / oscillation protection
13. Project instructions 优先于 Skill 默认规则
14. Review 和 Fix 职责分离

目标不是把 Arbor 改成：

- 通用 workflow engine；
- server；
- database-backed state machine；
- MCP orchestration framework；
- 重型 runtime。

至少当前阶段不要这么做。

Arbor 更适合作为：

> 一个严格定义的 Agent Review Protocol + 多 runtime packaging。

---

# 4. 第一优先级：重新检查 convergence algorithm

重点验证一个潜在流程漏洞。

当前可能存在如下状态：

```text
Round N

Correctness reviewer:
PASS

Structure reviewer:
P2 residual improvement
blocking = false

当前不存在 P0/P1/structural blocker。

但是本轮 validation 尚未执行。
```

如果当前算法类似：

```text
review
↓
normalize

if convergence gate met AND validation green:
    PASS

select actionable blockers

if no actionable blockers:
    STOP
```

那么可能出现：

```text
没有 blocker
+
validation 尚未执行
=
convergence=false

然后

没有 actionable blocker
=
STOP
```

但正确行为应该是：

```text
gate blockers == 0
↓
run required validation
↓
validation PASS
↓
PASS with residual P2
```

请完整检查当前实现和 contract 是否存在这个问题。

如果存在，修复 execution order。

建议目标状态：

```text
REVIEW
  ↓
NORMALIZE / DEDUPE
  ↓
RESOLVE REVIEWER CONFLICT
  ↓
COMPUTE GATE BLOCKERS
  ↓

gate_blockers == 0 ?
        │
        ├── YES
        │      ↓
        │   VALIDATE
        │      ↓
        │   PASS ?
        │      ├── YES → CONVERGED
        │      └── NO  → classify validation failure
        │
        └── NO
               ↓
           stop guards
               ↓
       actionable findings
               ↓
        root-cause fix batch
               ↓
            validate
               ↓
        fresh review round
```

核心原则：

> Validation 是尝试完成 convergence 的动作，而不是要求 validation 已经为 green 才允许进入 convergence path。

同时检查术语：

如果集合中可能包含 non-blocking P2，则不要把整个集合叫：

`actionable blockers`

更准确可以是：

`actionable findings`

避免 blocker / finding 语义污染。

---

# 5. 第二优先级：重新设计 Scope Contract

当前重点检查：

是否存在类似规则：

> findings 只能针对 changed code / changed lines。

这种设计虽然可以阻止 repo-wide cleanup，但可能把：

```text
问题是否由本 change 引起
```

错误等同于：

```text
问题是否发生在 changed line
```

这两个概念必须分开。

例如：

```text
changed:
service.GetUser() 修改了返回语义

untouched:
handler 调用 GetUser()

结果：
untouched handler 因新语义出现 crash
```

问题 manifestation 在 untouched code。

但 root cause 明确由当前 change 引入。

这种 finding 应该属于 review scope。

建议将 scope ownership 从：

```text
location-based
```

调整为：

```text
causality-based
```

推荐原则：

> A finding is in scope iff it is causally attributable to the target change.

Untouched code 可以作为：

- manifestation；
- interaction point；
- compatibility evidence；
- caller/callee evidence；
- configuration interaction；
- schema interaction；

但 unrelated pre-existing issue 仍然只能作为 context。

可以考虑 contract：

```text
Findings must be causally attributable to the target change.

Untouched code may be cited as the manifestation or evidence of a
change-induced regression.

Unrelated pre-existing defects remain out of scope.
```

不要简单扩大成 repo-wide review。

这里必须维持 scope boundary。

---

# 6. Finding Schema：收回 reviewer 的 policy 权力

请检查当前 finding 是否同时包含类似：

```yaml
severity: P0 | P1 | P2 | P3
blocking: true | false
```

Structure reviewer 是否还有：

```yaml
discipline:
  blocking regression
  material improvement
  taste
```

如果是，则检查是否存在 duplicated policy state。

例如：

```yaml
severity: P1
blocking: false
```

或者：

```yaml
severity: P2
blocking: true
discipline: material improvement
```

这些状态是否语义一致？

如果必须依赖额外自然语言规则解释是否合法，那么 schema 本身过于宽松。

建议原则：

> Reviewer 负责产生 evidence 和 classification；
> Orchestrator 负责决定 gate policy。

也就是：

```text
Reviewer = Evidence Producer

Orchestrator = Policy Owner
```

建议 reviewer finding 更接近：

```yaml
local_id: C1
severity: P1
category: correctness

problem: ...
evidence: ...
impact: ...
recommended_direction: ...
```

Structure finding 可以是：

```yaml
severity: P2
structural_class: regression | improvement
```

然后由 orchestrator 根据 policy/profile 派生 blocking：

```text
correctness:

P0 → BLOCK
P1 → BLOCK
P2 → optional strict-mode block
P3 → NON-BLOCK


structure:

regression → BLOCK
improvement → normally NON-BLOCK
strict policy may override
```

如果当前 contract 已经规定：

`taste` 不应该成为 finding，

那么不要继续在 finding schema 中保留合法的：

```yaml
discipline: taste
```

避免产生：

> schema 合法但 protocol 非法

的状态。

---

# 7. 重新检查 No-Progress 定义

当前如果 no-progress 是通过：

```text
blocker count does not shrink
```

来判断，请重新评估。

例如：

```text
Round 1:
F001
F002

Round 2:
F003
F004
```

如果：

```text
F001 resolved
F002 resolved
```

fresh reviewer 又发现两个新的 independent blocker，

那么：

```text
blocker count:
2 → 2
```

不能简单称为：

`NO PROGRESS`

实际上是：

```text
有 resolution progress
但仍存在 high churn / non-convergence
```

建议利用 stable finding identity，显式区分：

```text
previous blockers
    ↓
persistent
resolved
new
```

建议：

```text
resolution_progress =
    resolved(previous blockers) > 0

validation_progress =
    failing → passing

stagnation =
    inherited persistent blockers unchanged
    AND
    no validation improvement
```

新的 blocker 可以视为：

```text
churn
```

不要一开始就设计复杂 churn state machine。

`max_rounds` 本身已经可以限制无限发现新问题。

No-progress guard 应更关注：

> 相同根因持续存在且没有验证改善。

---

# 8. 引入一个明确但轻量的 ReviewPacket 抽象

目前两个 reviewer 理论上都接收：

- same baseline；
- same changed scope；
- same project instructions；
- same target change；
- fresh context；
- no prior findings。

建议正式把这个概念命名为：

`ReviewPacket`

不是必须实现成复杂 runtime object。

首先可以只是 protocol-level abstraction。

例如：

```yaml
review_packet:

  scope:
    type: working-tree
    baseline: abc123
    paths:
      - internal/foo.go
      - internal/bar.go

  project_constraints:
    sources:
      - AGENTS.md

  validation:
    required:
      - make test

  target_change:
    materialization: ...

  previous_findings:
    NEVER_INCLUDE
```

概念模型：

```text
CorrectnessReview
=
ReviewPacket × CorrectnessLens


StructureReview
=
ReviewPacket × StructureLens
```

Fresh round：

```text
ReviewPacket(current repository state)
+
fresh reviewer
```

这个抽象的价值是：

> 明确 reviewer 的输入协议，而不是仅靠多份 prompt 约定“你们看到相同东西”。

保持轻量，不要把 ReviewPacket 做成复杂 framework。

---

# 9. 重新整理 Core / Lens / Runtime / Distribution 四层边界

建议将 Arbor 的概念架构收敛为：

```text
                Arbor

          Distribution Layer
      marketplace / packaging
                │
      ┌─────────┴─────────┐
      │                   │
   Codex Adapter      Claude Adapter
      │                   │
      └─────────┬─────────┘
                │
          Review Protocol
                │
       canonical invariants
                │
      ┌─────────┴─────────┐
      │                   │
Correctness Lens     Structure Lens
      │                   │
      └──── ReviewPacket ─┘
                │
            Reconcile
                │
               Fix
                │
            Validate
                │
            Converge
```

职责定义：

### Arbor Distribution

负责：

- marketplace；
- plugin discovery；
- installation；
- release metadata；
- packaging。

### Runtime Adapter

负责：

- Codex 如何 spawn reviewer；
- Claude 如何 spawn reviewer；
- runtime-specific tools；
- runtime-specific agent definitions。

### Core Review Protocol

负责：

- scope；
- ReviewPacket；
- finding model；
- reconciliation；
- fix policy；
- validation；
- convergence；
- stop guards。

### Review Lens

负责：

- correctness；
- structure；

未来如果有第三个 reviewer，也只是新增 lens。

不要让 runtime-specific 行为逐渐渗透 Core Protocol。

---

# 10. Skill 本体应保持薄而清晰

检查：

`dual-review-loop/SKILL.md`

是否同时承担：

- inputs；
- reviewer role；
- algorithm；
- convergence；
- guards；
- Codex adaptation；
- Claude adaptation；
- output rules；
- reference index。

问题不是 Skill 太长。

问题是：

> 不同变化频率的内容混合。

Core protocol 很稳定。

Runtime API 和 agent spawning 方式变化更频繁。

建议 Core Skill 最终只表达：

```text
resolve input
freeze scope
construct ReviewPacket
dispatch review lenses
normalize findings
resolve conflict
evaluate gate
fix
validate
repeat
report
```

平台差异分别放到：

```text
references/runtimes/codex.md
references/runtimes/claude.md
```

或者当前 repo layout 下最合适的 runtime-specific 文件。

不要机械重构目录。

首先遵守 Codex / Claude 对 Plugin、Skill、Agent discovery path 的真实要求。

逻辑边界比目录美观更重要。

---

# 11. 解决 Semantic Duplication，而不是机械追求 DRY

当前可能存在同一 invariant 在多个地方重复描述，例如：

```text
reviewer read-only

fresh reviewer

no previous findings

same scope

no nested agent

single writer
```

这些规则可能分别存在：

- reviewer agent；
- reviewer Skill；
- orchestrator Skill；
- prompt contract；
- reference docs。

不要简单删除重复。

Agent Prompt 世界不能机械套传统代码 DRY。

因为 subagent 必须在自己的 context 中重新收到关键边界。

正确目标应是：

```text
one semantic source of truth
+
multiple runtime projections
```

建议定义 canonical invariants，例如：

```text
INV-01 READ_ONLY

INV-02 FRESH_CONTEXT

INV-03 SAME_SCOPE

INV-04 NO_PRIOR_FINDINGS

INV-05 NO_NESTED_AGENT

INV-06 SINGLE_WRITER

INV-07 FULL_SCOPE_REREVIEW
```

然后检查：

```text
Reviewer projection
Orchestrator projection
Codex projection
Claude projection
```

是否都正确包含自己所需要的 invariants。

目标不是：

```text
no duplicated text
```

而是：

```text
no semantic drift
```

这可能是 Arbor 长期维护中比普通 code duplication 更重要的问题。

---

# 12. 加入 Contract Consistency Check

不要一开始构建复杂生成系统。

先做简单 deterministic checks。

例如：

```text
plugin version parity

marketplace version parity

plugin name parity

repo metadata parity

license parity

relative file path exists

Skill frontmatter valid

manifest parseable

required invariant present

reviewer projection contains required rules

orchestrator projection contains required rules
```

如果 Arbor 现在只有一个 plugin，

暂时不要为了两个 marketplace manifest 建：

```text
canonical yaml
→ generator
→ all manifests
```

优先做：

```text
parity checker
```

等未来有多个 plugin，真实出现 metadata drift 后，再考虑 code generation。

---

# 13. 把 Acceptance Tests 升级为 Regression Evals

当前 acceptance 如果主要停留在设计文档或人工验证，请把它正式固化到 repo。

至少覆盖：

```text
E01 Clean change
→ PASS

E02 Correctness blocker
→ fix → validate → fresh review

E03 Structural blocker
→ fix → validate → fresh review

E04 Duplicate root cause
→ two reviewer findings → one stable root-cause finding

E05 Residual-only
→ no blockers + P2 residual
→ validation
→ PASS

E06 Cross-boundary regression
→ root cause changed code
→ manifestation untouched code
→ finding remains in scope

E07 Persistent blocker
→ no-progress guard

E08 Oscillation
→ A → B → A style repair behavior
→ stop guard

E09 Reviewer disagreement
→ explicit conflict resolution

E10 Validation failure
→ correct classification / repair / BLOCKED
```

建议分两层：

## Layer 1 — Static / deterministic CI

执行：

- JSON parse；
- path existence；
- manifest parity；
- invariant consistency；
- schema validation；
- frontmatter validation。

每次 PR 都跑。

## Layer 2 — Behavioral eval

真正调用 agent protocol。

可以：

- release 前运行；
- 手动运行；
- 定期运行。

不要求每个 commit 都消耗 Agent token。

目标：

> 从“我们曾经验证过 Arbor”
>
> 变成
>
> “Arbor 有自己的 regression suite”。

---

# 14. 调整 Final Output Contract

如果当前 output contract 是：

```text
exactly PASS template
or
exactly STOPPED template

nothing else
```

请检查它是否可能和用户的显式要求冲突。

例如用户说：

> review 完以后详细告诉我修改了什么。

此时 Skill 不应该强行禁止解释。

更合理的模型：

```text
The final response MUST contain exactly one canonical
PASS or STOPPED outcome block.

Additional explanation may be included only when:

1. explicitly requested by the user; or

2. necessary to explain a STOP decision.
```

目标：

```text
machine-stable core
+
human-flexible shell
```

不要让 Skill contract 和用户 instruction 制造不必要的 instruction conflict。

---

# 15. 暂时不要抽象 Generic Convergence Engine

请专门做一次 architecture ablation。

至少比较：

## 方案 A

当前：

```text
Skill + references + agents
```

优点：

- 简单；
- portable；
- native。

问题：

- semantic contract 容易散。

## 方案 B

抽象：

```text
Arbor Generic Convergence Engine
```

然后 dual-review-loop 只是其上的 workflow。

优点：

- 理论上可复用。

问题：

- 目前没有第二个明确真实 use case；
- 很可能形成错误抽象；
- runtime 会变重；
- Agent-native 特征可能被 workflow engine 稀释。

## 方案 C

```text
Protocol Core
+
ReviewPacket
+
Review Lenses
+
Runtime Adapters
+
Evals
```

预期这是更优方案。

但请你自己重新评估。

不要因为任务书推荐 C 就直接选 C。

必须说明：

- A 的限制；
- B 为什么现在可能过度设计；
- C 是否真正解决当前实际问题；
- 是否存在更好的 D。

---

# 16. 推荐目标目录，仅作为参考

不要为了达到目录结构而违反平台规范。

逻辑上可以接近：

```text
Arbor/

├── README.md
│
├── .agents/
│   └── plugins/
│       └── marketplace.json
│
├── .claude-plugin/
│   └── marketplace.json
│
├── plugins/
│   └── dual-review-loop/
│
│       ├── plugin.json
│       ├── .claude-plugin/
│       │   └── plugin.json
│       │
│       ├── agents/
│       │   ├── correctness-reviewer.md
│       │   └── structure-reviewer.md
│       │
│       ├── skills/
│       │
│       │   ├── dual-review-loop/
│       │   │   ├── SKILL.md
│       │   │   └── references/
│       │   │       ├── protocol.md
│       │   │       ├── scope.md
│       │   │       ├── review-packet.md
│       │   │       ├── finding-model.md
│       │   │       ├── convergence.md
│       │   │       ├── output.md
│       │   │       └── runtimes/
│       │   │           ├── codex.md
│       │   │           └── claude.md
│       │   │
│       │   ├── dual-review-correctness/
│       │   └── dual-review-structure/
│       │
│       ├── evals/
│       │   ├── clean/
│       │   ├── residual-only/
│       │   ├── cross-boundary-regression/
│       │   ├── duplicate-root-cause/
│       │   ├── no-progress/
│       │   └── oscillation/
│       │
│       └── scripts/
│           └── check-contract-consistency.*
│
└── docs/
    ├── architecture.md
    └── acceptance.md
```

再次强调：

> directory layout 是 implementation detail。

更重要的是明确四层职责：

```text
Distribution
Runtime Adapter
Core Protocol
Review Lens
```

---

# 17. 推荐执行顺序

不要一次性推翻重写。

建议按以下顺序执行：

## Phase A — Correctness

修复：

```text
residual-only convergence branch
```

并补对应 regression case。

---

## Phase B — Scope

将：

```text
changed-location ownership
```

调整成：

```text
change-causality ownership
```

同时保持 unrelated repo issue 不进入 scope。

---

## Phase C — Finding Policy

整理：

```text
severity
blocking
discipline
```

减少重复状态。

把 gate decision 尽量收口到 orchestrator。

---

## Phase D — Progress Semantics

区分：

```text
persistent
resolved
new
```

重新定义 no-progress。

---

## Phase E — ReviewPacket

将 currently implicit reviewer input contract 正式化。

---

## Phase F — Canonical Invariants

整理：

```text
READ_ONLY
FRESH_CONTEXT
SAME_SCOPE
NO_PRIOR_FINDINGS
NO_NESTED_AGENT
SINGLE_WRITER
FULL_SCOPE_REREVIEW
```

解决 semantic drift。

---

## Phase G — Runtime Boundary

把 Codex / Claude-specific orchestration 进一步从 core protocol 中隔离。

---

## Phase H — Regression Evals

把现有 acceptance cases 正式变成 repository eval cases。

---

## Phase I — Static CI

增加：

```text
manifest validation
path validation
version parity
contract consistency
```

---

## Phase J — Full Acceptance

重新运行：

```text
Codex
+
Claude
```

完整 acceptance。

---

# 18. 代码修改原则

整个重构过程中遵守：

### 1.

优先修改 contract，而不是用更多 prompt 文字 patch 行为。

### 2.

能删除一个非法状态，就不要增加三条文字说明解释它为什么非法。

### 3.

Reviewer 尽量只负责：

```text
observe
classify
explain
```

Orchestrator 负责：

```text
policy
gate
fix
convergence
```

### 4.

Platform-specific behavior 不应成为 Core Protocol 的一部分。

### 5.

不要为了 DRY 牺牲 reviewer isolation。

### 6.

不要为了 abstraction 引入尚未存在的未来需求。

### 7.

任何新增 abstraction 必须回答：

> 它今天解决了哪两个以上真实存在的问题？

否则不要加。

### 8.

如果能通过 protocol-level abstraction 解决，不引入 runtime framework。

### 9.

保持 Arbor Agent-native、portable、small-core。

---

# 19. 修改完成后必须重新进行 Self Review

完成第一轮修改以后，不要直接结束。

重新站在以下三个角色审查自己的实现：

## Reviewer A — Protocol correctness

检查：

- convergence 有没有 impossible state；
- validation order 是否一致；
- blocking 语义是否唯一；
- finding identity 是否稳定；
- scope 是否既不过窄也不过宽；
- stop guards 是否存在误判。

## Reviewer B — Architecture

检查：

- core / lens / adapter / distribution 是否混层；
- 是否过度抽象；
- 是否加入没有第二 use case 的 framework；
- contract 是否又产生新的 duplication；
- 是否为未来平台做了 premature abstraction。

## Reviewer C — Agent behavior

检查：

- prompt 是否可能互相冲突；
- fresh reviewer 是否真的 fresh；
- reviewer 是否可能看到 previous findings；
- reviewer 是否可能修改 workspace；
- reviewer 是否有足够 context；
- user instruction 是否可能被 Skill output contract 错误覆盖。

修复这些 review 中真正成立的问题。

然后再次运行 tests/evals。

---

# 20. 最终做一次 Ablation / Reflection

完成之后，请专门回答：

### A.

如果完全保留 Arbor v0.1，不进行这次重构，长期最大的三个风险是什么？

### B.

这次新增的 abstraction 中：

```text
ReviewPacket
Canonical Invariants
Runtime Adapter
Regression Evals
```

逐个说明：

> 如果删除它，会失去什么？

如果删除后几乎没有损失，则说明它可能是过度设计，应删除。

### C.

检查是否把一个：

```text
简单 Agent Skill
```

错误演变成了：

```text
mini workflow framework
```

如果有这种趋势，主动退回。

### D.

检查是否存在：

```text
为了未来第三 reviewer
为了未来第三 runtime
为了未来十个 plugin
```

而引入的当前无价值复杂度。

如果有，删除。

---

# 21. 最终交付内容

完成后请输出：

## 1. 当前 Arbor 架构判断

说明：

```text
什么是 Arbor 当前真正的核心抽象。
```

---

## 2. 实际发现的问题

按照：

```text
P0
P1
P2
```

排序。

只列真实验证过的问题。

---

## 3. 修改内容

逐项说明：

```text
Before
After
Why
```

---

## 4. 最终架构

给出：

```text
Distribution
Runtime Adapter
Core Protocol
Review Lens
ReviewPacket
Finding Model
Convergence
Evals
```

之间的关系。

---

## 5. Ablation 结果

说明：

```text
哪些建议被保留
哪些建议被删除
哪些建议被简化
为什么
```

---

## 6. Remaining Risks

明确当前仍未解决的问题。

不要为了让结果显得完整而假装没有风险。

---

# 22. 最终目标

这次工作的成功标准不是：

```text
文件更多
架构图更漂亮
抽象更多
代码更“工程化”
```

成功标准是：

```text
更少的语义歧义

更少的非法协议状态

更清楚的职责边界

更可靠的 convergence

更准确的 scope

更稳定的 reviewer isolation

更低的跨平台耦合

更容易验证的行为

更低的未来修改成本
```

最终希望 Arbor 收敛为：

```text
              Arbor
                │
          Distribution
                │
      ┌─────────┴─────────┐
    Codex               Claude
   Adapter              Adapter
      └─────────┬─────────┘
                │
         Review Protocol
                │
       Canonical Invariants
                │
      ┌─────────┴─────────┐
Correctness Lens     Structure Lens
      │                   │
      └──── ReviewPacket ─┘
                │
            Reconcile
                │
              Fix
                │
            Validate
                │
            Converge
```

最重要的一句话：

> 不要把 Arbor 重做成一个更复杂的系统；把它重做成一个语义更严格、协议更一致、行为更可验证的系统。

请先审查，再修改，再 self-review，再 ablation，最终收敛后再提交结果。
