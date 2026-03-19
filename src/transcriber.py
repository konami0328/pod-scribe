import os
import yaml
from tqdm import tqdm
from faster_whisper import WhisperModel


def load_model(model_size: str) -> WhisperModel:
    """
    Load faster-whisper model of the given size.
    Model is downloaded automatically on first use and cached in ~/.cache/huggingface/hub.
    Uses int8 quantization for faster CPU inference.
    """
    print(f"  [whisper] Loading model: {model_size}")
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def transcribe_audio(
    model: WhisperModel,
    audio_path: str,
    language: str | None = None,
) -> str:
    print(f"  [transcribe] {os.path.basename(audio_path)}")
    segments, info = model.transcribe(audio_path, language=language)
    print(f"  [detected language] {info.language} (probability: {info.language_probability:.2f})")

    duration = get_audio_duration(audio_path)
    transcript_segments = []
    current = 0.0

    with tqdm(total=round(duration), unit="sec", desc="Transcribing") as bar:
        for segment in segments:
            transcript_segments.append(segment.text)
            elapsed = segment.end - current
            bar.update(round(elapsed))
            current = segment.end

    return " ".join(transcript_segments).strip()


def save_transcript(transcript: str, audio_path: str, output_dir: str) -> str:
    """
    Save transcript as a .txt file in output_dir.
    Filename mirrors the audio filename with .txt extension.
    Returns the path to the saved transcript file.
    """
    os.makedirs(output_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(audio_path))[0]
    filepath = os.path.join(output_dir, f"{basename}.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(transcript)

    print(f"  [saved] {filepath}")
    return filepath


if __name__ == "__main__":
    import sys

    config_path = os.path.join(os.path.dirname(__file__), "..", "config.example.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    model_size = config["whisper"]["model"]
    language = config["whisper"]["language"]
    output_dir = config["output"]["transcripts_dir"]

    # Find the most recently downloaded audio file in transcripts dir
    audio_files = [
        f for f in os.listdir(output_dir)
        if f.endswith((".mp3", ".m4a", ".wav"))
    ]
    if not audio_files:
        print("No audio files found in transcripts dir. Run downloader first.")
        sys.exit(1)

    audio_files.sort(reverse=True)
    audio_path = os.path.join(output_dir, audio_files[0])
    print(f"Testing transcription on: {audio_path}")

    model = load_model(model_size)
    transcript = transcribe_audio(model, audio_path, language=language)
    save_transcript(transcript, audio_path, output_dir)

    print(f"\nTranscript preview (first 500 chars):\n{transcript[:500]}")