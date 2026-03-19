import os
import whisper


def load_model(model_size: str) -> whisper.Whisper:
    """
    Load Whisper model of the given size.
    Model is downloaded automatically on first use and cached in ~/.cache/whisper.
    """
    print(f"  [whisper] Loading model: {model_size}")
    return whisper.load_model(model_size)


def transcribe_audio(
    model: whisper.Whisper,
    audio_path: str,
    language: str | None = None,
) -> str:
    """
    Transcribe a single audio file using Whisper.
    Returns the full transcript as a plain string.
    language=None triggers automatic language detection.
    """
    print(f"  [transcribe] {os.path.basename(audio_path)}")
    result = model.transcribe(audio_path, language=language, verbose=False)
    return result["text"].strip()


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
    import yaml

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