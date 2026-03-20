
# pod-scribe

Download and transcribe podcast episodes locally. No cloud ASR costs — just your CPU and time.

Built for generating transcripts that can be fed into your own LLM workflows (summarization, Q&A, notes, etc).

---

## How it works

```
RSS feed → download audio → local Whisper → transcript (.txt)
```

Transcripts are saved as plain text files, ready to paste into any LLM chat interface.

---

## Requirements

- Python 3.11+
- faster-whisper (model downloads on first run)
- Proxy (only if required by your network)

---

## Setup

```bash
conda create -n pod-scribe python=3.11
conda activate pod-scribe
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

Edit `config.yaml` to configure RSS feeds and Whisper model settings.

---

## Usage

> **Tip:** use `--pod` to target a specific podcast by name (fuzzy match). Defaults to all feeds.

### Download episodes

```bash
# Download the 3 most recent episodes (all feeds)
python run.py --download --last 3

# Download episodes since a specific date
# Tip: add a one-day buffer to account for timezone differences
python run.py --download --since 2026-03-01

# Target a specific podcast
python run.py --pod "Invest" --download --last 3

# Download a specific episode by title keyword
python run.py --pod "Invest" --download "stock"
```

### Transcribe

```bash
# Transcribe all downloaded episodes that don't have a transcript yet
python run.py --transcribe

# Transcribe a specific episode by keyword
python run.py --transcribe "stock"
```

### Download and transcribe together

```bash
python run.py --download --transcribe --last 3
python run.py --pod "Invest" --download --transcribe --since 2026-03-01
```

---

## Whisper model sizes

| Model  | Size   | Speed (CPU)    | Quality |
| ------ | ------ | -------------- | ------- |
| small  | ~500MB | ~0.6-0.8× realtime | good   |

`small` is recommended for CPU-only environments — fast enough for most clean English audio.

Models are cached at `~/.cache/huggingface/hub/` after first download.

> **First run note:** the model will be downloaded automatically. If you're in a restricted network region, set proxy environment variables before running. E.g,:
> ```bash
> export https_proxy=http://127.0.0.1:7897
> export http_proxy=http://127.0.0.1:7897
> ```

---

## Configuration

```yaml
rss:
  feeds:
    - name: "Invest Like the Best"
      url: "https://feeds.megaphone.fm/CLS2859450455"

whisper:
  model: small        # small / medium / large-v3
  language: null      # null = auto-detect, or "en" / "zh"

proxy:
  http: null          # leave empty if not needed
  https: null

output:
  transcripts_dir: "./transcripts"
```

---

## Suggested analysis prompt

Once you have a transcript, paste it into any LLM chat interface with a prompt. Below is the one I use now — feel free to adapt it to your own thinking style.

```
# ZH

- 你是一位批判性思维训练有素的分析师，擅长从对话性内容中提炼论证结构。

以下是一期播客的转录文稿。请按照以下4个步骤进行分析：

---

【第一步：论证结构梳理 + Fact Check（如适用）】

严格基于转录文本，不得添加未提及信息。

以表格呈现：

| 论点 | 支撑论据 | 论据类型 | 重要性 | 事实性核查 |
|------|--------|--------|------|------------|
| ... | ... | ... | 高/中/低 | ✅/⚠️/❌/🔍 |

要求：
- 每条尽量简洁（建议30–50字以内）
- 论据类型必须标注：（个人经验）（类比）（数据）（权威背书）（案例）
- 仅当涉及**明确可验证事实**时填写“事实性核查”：
  - ✅ 可确认 / ⚠️ 存疑 / ❌ 有误 / 🔍 建议核实
  - 并在单元格中简要说明依据（如：据领域共识 / 常识判断）
- 若该行无事实性内容，可留空或写“—”

---

【第二步：论证质量评估】

严格基于转录文本，不得添加文本中未提及的任何信息。

对每个论点逐一评估：
- 论据是否为直接证据，还是个人经验/类比/权威背书？
- 论证链条中是否存在跳跃或隐含假设？
- 样本是否有代表性？

---

【第三步：辩证反思】

允许调用训练知识，但须遵守以下规则：
- 反面论点须来自已知的学术争议、主流替代观点、或论证结构上的逻辑漏洞
- 必须注明来源类型，例如"据[领域]主流争议"或"从逻辑结构看"
- 不得凭空构造反例或捏造对立观点
- 推荐属于对立观点的不超过3个的高质量材料

---

【第四步：归纳总结】

在前三步的基础上，给出你对这期播客的整体判断。包含以下三点：
- 核心价值：这期播客最值得保留的洞见是什么？
- 最大局限：论证中的缺陷或盲点是什么？
- 你的建议：听完这期播客，听众最值得延伸阅读/思考的方向是什么？（不超过2个方向，须言之有据，不得泛泛而谈）


注意：
- 无论转录文本语言为何，所有输出均以中文呈现
```

```
# EN

You are an analyst highly trained in critical thinking, specializing in extracting and refining argumentative structures from conversational content.

Below is a transcript of a podcast episode. Please conduct an analysis following these 4 steps:

---

**【Step 1: Argumentative Structure Mapping + Fact Check (if applicable)】**

Strictly based on the transcript; do not add information not mentioned.

Present in a table:

| Argument | Supporting Evidence | Evidence Type | Importance | Fact Check |
| :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | High/Med/Low | ✅/⚠️/❌/🔍 |

Requirements:
- Each entry should be as concise as possible (suggested 30–50 words).
- Evidence types must be labeled: (Personal Experience), (Analogy), (Data), (Authority Endorsement), (Case Study).
- Only fill in the "Fact Check" column when **explicitly verifiable facts** are involved:
    - ✅ Confirmed / ⚠️ Questionable / ❌ Erroneous / 🔍 Verification Recommended.
    - Briefly state the basis in the cell (e.g., Based on field consensus / Common sense).
- If the row has no factual content, leave it blank or write "—".

---

**【Step 2: Argument Quality Assessment】**

Strictly based on the transcript; do not add any information not mentioned in the text.

Evaluate each argument individually:
- Is the evidence direct, or is it personal experience/analogy/authority endorsement?
- Are there leaps or hidden assumptions in the argumentative chain?
- Is the sample representative?

---

**【Step 3: Dialectical Reflection】**

Allowed to use trained knowledge, but must adhere to the following rules:
- Counter-arguments must come from known academic disputes, mainstream alternative views, or logical loopholes in the argumentative structure.
- Must specify the source type, e.g., "According to mainstream controversy in [Field]" or "From a logical structural perspective".
- Do not fabricate counter-examples or invent opposing views.
- Recommend no more than 3 high-quality materials belonging to opposing viewpoints.

---

**【Step 4: Summary & Conclusion】**

Based on the previous three steps, provide your overall judgment of this podcast. Include the following three points:
- Core Value: What is the most valuable insight to retain from this episode?
- Maximum Limitation: What are the flaws or blind spots in the argumentation?
- Your Suggestion: What are the most worthwhile directions for listeners to explore or reflect on after listening to this episode? (No more than 2 directions; must be evidence-based and not vague).

Note:
- Regardless of the language of the transcript, all final outputs must be presented in English.
```

---

## Notes

- Transcripts and audio files are saved to `transcripts/` (gitignored)
- RSS publish dates may differ from podcast apps — use `--since` with a one-day buffer to be safe
- This tool only handles downloading and transcription. Downstream processing is intentionally left to the user
