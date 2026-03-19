


# pod-scribe

Download and transcribe podcast episodes locally. No cloud ASR costs — just your CPU and time.

Built for generating transcripts that can be fed into your own LLM workflows (summarization, Q&A, notes, etc).

---

## Features

- Download podcast episodes from RSS feeds
- Local transcription using Whisper
- Plain text output, ready for LLM input
- Fully local, no external APIs

---

## How it works

```

RSS feed → download audio → local Whisper → transcript (.txt)

````

Transcripts are saved as plain text files and can be used in any downstream workflow.

---

## Requirements

- Python 3.11+
- [Whisper](https://github.com/openai/whisper) (model downloads on first run)
- Proxy (only if required by your network)

---

## Setup

```bash
conda create -n pod-scribe python=3.11
conda activate pod-scribe
pip install -r requirements.txt
cp config.example.yaml config.yaml
````

Edit `config.yaml` to configure RSS feeds and Whisper model settings.

---

## Usage

### Download episodes

```bash
# Download the 3 most recent episodes
python run.py --download --last 3

# Download episodes since a specific date
# (recommended: add a one-day buffer for timezone differences)
python run.py --download --since 2026-03-01
```

### Transcribe

```bash
# Transcribe all downloaded episodes without transcripts
python run.py --transcribe

# Transcribe a specific episode by keyword
python run.py --transcribe "Howard Marks"
```

### Download and transcribe

```bash
python run.py --download --transcribe --last 3
```

---

## Whisper model sizes

| Model  | Size   | Speed (CPU)     | Quality |
| ------ | ------ | --------------- | ------- |
| small  | ~500MB | ~1–2× realtime  | good    |
| medium | ~1.5GB | ~5–10× realtime | better  |

`small` is recommended for CPU-only environments.

Models are cached at:

```
~/.cache/whisper/
```

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
  http: "http://127.0.0.1:7897"
  https: "http://127.0.0.1:7897"

output:
  transcripts_dir: "./transcripts"
```

---

## Notes

* Transcripts and audio files are saved to `transcripts/` (gitignored)
* RSS publish dates may differ from podcast apps; use `--since` with a one-day buffer
* This tool only handles downloading and transcription

Downstream processing (summarization, QA, etc.) is intentionally left to the user.

