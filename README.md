# 三省 · Sanxing

面向研究型 Agent 的 research-dreaming Skill。它回看原始证据，阅读本地论文，从两者交汇处提出可证伪假设，并在结果可能改变判断时执行最小检查。

[English README](README.en.md)

## 名称

「三省」取自《论语·学而》中曾子的「吾日三省吾身」，读作 *sān xǐng*，意为反省和检查。Sanxing 借这个名字提醒研究 Agent 每轮回答三个问题。

1. **旧判断有哪一条该改？**

   从新增的原始记录开始，核对旧记忆、摘要和状态判断，并保存来源、版本和页码或段落位置。

2. **几篇论文放在一起，能提出什么新假设？**

   先读本地论文库，寻找论文之间的联系、张力和边界条件，再把联想收敛成假设、竞争预测和明确的验证输入。

3. **什么结果会让我改主意？**

   只有可信的冻结数据已经可读，而且不同结果会改变一个明确判断或行动时，才执行最小检查。条件不足时，交付包含输入、分割方式、指标、阈值和反证条件的可执行方案。

## 适用范围

Sanxing 适合项目记忆和论文资料已经积累，但旧总结可能过时，或跨论文联系尚未成为可检验问题的研究任务。它可以只做证据回看和方案设计，也可以在已有冻结数据时运行小型、可复现的检查。

每轮调用者需要明确项目标识、研究范围、获准读取的项目记录、本地论文目录、独立输出目录和执行预算。Sanxing 不要求特定模型、记忆产品或编程语言。它不会自动训练生产模型、改写正式项目记忆、访问密封测试集，也不会把历史摘要重新包装成新实验。

## 给 Agent 的调用模板

把仓库放到 Agent 能读取的位置，将下方提示中的 `SKILL.md` 换成文件的实际路径。预算可以填「最多 30 分钟，单次本地 CPU 检查」。首轮把检查点填为 `none`。

```text
先读取 <path_to_repo>/SKILL.md，按 research-dreaming 0.3.0 执行。
项目是 <project>，本轮范围是 <scope>。
只读项目证据是 <approved_project_records>，本地论文目录是 <local_papers>。
结果写入独立目录 <output_dir>，预算是 <budget>。
上一次成功检查点是 <previous_checkpoint_or_none>。

先建立范围内完整的 catalog.json，再运行增量证据扫描。
从原始项目证据和本地论文中自己选择一个可能改变项目判断的问题。
记录页码或段落来源、竞争预测、输入、数据划分或独立重复单位、指标、不确定性、反证条件和阈值。
只有可信冻结输入存在且结果会改变明确判断时才跑最小检查。
否则输出 PLAN_ONLY，并写明缺失输入和下一步需要什么。
所有报告、命令、哈希和交接材料都写入独立目录。
不要训练生产模型，不访问密封测试集，不更新正式记忆。
```

## 工作流程

1. 建立 `catalog.json`，用稳定 ID 完整列出范围内来源。
2. 运行增量扫描，检查新增、修改、删除和未变化来源。
3. 阅读新增或修改的原始证据，再阅读相关论文的具体页码或段落。
4. 选择一个能影响明确判断的可证伪问题，区分观察、推断、方案和未决事项。
5. 定义竞争预测、输入、数据划分或独立重复单位、指标、不确定性、反证条件和阈值。
6. 决定是否执行最小检查。冻结证据不足时，输出 `PLAN_ONLY`。
7. 保存报告、机器可读结果、精确命令、哈希、日志和交接信息。
8. 扫描和证据审阅都成功后，才推进检查点。

## 增量扫描和检查点

可将这一步交给 Agent，也可以手动运行仓库自带的 Python 脚本。下面假定 `catalog.json` 在仓库根目录。把 `sources` 换成约定范围内的完整清单。清单里的相对路径以清单所在目录为基准，命令行路径以当前工作目录为基准。

```json
{
  "project": "example-project",
  "scope": "notes-and-priority-evidence",
  "complete_inventory": true,
  "sources": [
    {"id": "project-index", "path": "inputs/MEMORY.md"},
    {"id": "paper-001", "path": "papers/example.pdf"}
  ]
}
```

从仓库根目录运行首次扫描。以下代码使用 Bash。在 Windows PowerShell 5.1 里，用 `| Set-Content -Encoding utf8 <输出路径>` 写入 JSON。

```bash
mkdir -p runs/first
python scripts/evidence_delta.py scan --catalog catalog.json > runs/first/DELTA.json
```

首轮会把当前清单里的所有来源标为新增。审阅后再写 `RESULT.json`，包含 `project`、`scope`、`status` 和 `delta_sha256`，后者是实际保存的 `DELTA.json` 文件的 SHA-256。可用下面第一条命令计算哈希。在 `reviewed.json` 写入已审阅并记录处理结论的稳定 ID，例如 `["project-index"]`。确认审阅有效后再运行第二条命令。

```bash
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('runs/first/DELTA.json').read_bytes()).hexdigest())"
python scripts/evidence_delta.py checkpoint --scan runs/first/DELTA.json --result runs/first/RESULT.json --reviewed runs/first/reviewed.json > runs/first/CHECKPOINT.json
```

下一轮使用同一项目和范围的上一个成功检查点，输出到新的目录。范围变化时重新建立基线。

```bash
mkdir -p runs/second
python scripts/evidence_delta.py scan --catalog catalog.json --previous runs/first/CHECKPOINT.json > runs/second/DELTA.json
```

方案完成但未执行检查时，使用 `status: COMPLETED` 和 `verification_status: PLAN_ONLY`。实际运行的检查要记录冻结输入和结果。证据或清单无法核实时记录 `UNRESOLVED` 或 `NOT_VERIFIED`，并保留旧检查点。

## 输出目录

成功的一轮通常包括以下文件。

- `DREAM_REPORT.md` 记录问题、证据地图、论文页码、竞争预测和决策规则
- `RESULT.json` 记录机器可读状态、范围、哈希和下一步
- `RUN.md` 记录执行过或计划执行的命令
- `DELTA.json` 记录增量扫描结果
- `CHECKPOINT.json` 记录已审阅来源的检查点
- `reviewed.json` 列出已完成证据处置的稳定 ID

所有结果都放在独立目录。正式项目记忆应在人工审阅后另行更新。

## 示例

假设研究问题是某模型组件是否在两个细胞背景中带来至少 0.5% 的相对误差下降。Agent 先从训练分区计算权重，再在相同目标和冻结留出分割上比较两个容量匹配的模型。若逐目标预测和响应数据不存在，Agent 不能把历史摘要称为新结果，而应输出 `PLAN_ONLY`，列出所需预测、标签、分割和权重文件。

## 内容

- [SKILL.md](SKILL.md) 研究流程，版本 0.3.0
- [scripts/evidence_delta.py](scripts/evidence_delta.py) 增量证据扫描和检查点工具
- [README.en.md](README.en.md) English documentation
