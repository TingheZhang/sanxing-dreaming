# 三省 · Sanxing

一个面向研究型 Agent 的 dreaming skill。它回看原始证据，从论文与项目记录的交汇处提出可检验的问题，并把能够改变判断的最小检查写成可复现的交接材料。

## 名称

「三省」取自《论语·学而》中的「吾日三省吾身」。这里的「省」读作 *xǐng*，意为反省、检查。三省也对应每一轮研究回看的三个问题。

1. **旧判断有哪一条该改**

   先回看新增的原始记录，核对旧记忆、摘要和状态判断，标出需要修正的证据。

2. **几篇论文放在一起能提出什么新假设**

   在有出处的论文观点之间寻找联系或张力，把联想收敛成带有竞争预测的可证伪假设。

3. **什么结果会让我改主意**

   只有在可信的冻结数据可用，且不同结果会改变明确判断时，才执行最小检查。条件不足时，交付带输入、指标、阈值和反证条件的可执行方案。

## 内容

- [SKILL.md](SKILL.md) 研究 dreaming 流程，版本 0.3.0
- [evidence_delta.py](scripts/evidence_delta.py) 增量证据扫描与检查点工具

## English

Sanxing helps research agents revisit evidence, form falsifiable hypotheses, and test what could change their minds.

