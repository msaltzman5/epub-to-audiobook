"""Text-to-speech output.

Kept separate from the extraction/cleanup pipeline so that generating
`book.txt` never depends on a TTS engine being installed or a voice model
being present. The CLI calls :func:`synthesize_book` after the text is written.
"""
from __future__ import annotations

import asyncio
import wave
from pathlib import Path

# Piper voice model shipped in the project root.
DEFAULT_PIPER_MODEL = "en_US-kusal-medium.onnx"
# A reasonable default edge-tts voice.
DEFAULT_EDGE_VOICE = "en-US-AndrewNeural"

# Rough throughput used only to print a "this will take about..." line.
# These are ballpark figures for a typical machine, not measurements:
#   - Piper on CPU renders on the order of ~180 characters/second.
#   - edge-tts streams from a server and is much faster.
PIPER_CHARS_PER_SEC = 180
EDGE_CHARS_PER_SEC = 1500

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# One (file_stem, text) pair per output audio file.
Job = tuple[str, str]


def synthesize_book(
    jobs: list[Job],
    output_dir: str | Path,
    *,
    engine: str = "piper",
    model: str | Path | None = None,
    voice: str | None = None,
    use_cuda: bool = False,
) -> list[Path]:
    """Render each ``(stem, text)`` job to an audio file inside ``output_dir``.

    Returns the list of written audio paths (empty when ``engine == "none"``).
    """
    engine = (engine or "none").lower()
    output_dir = Path(output_dir)
    jobs = [(stem, text) for stem, text in jobs if text.strip()]

    if engine == "none" or not jobs:
        return []

    rate = PIPER_CHARS_PER_SEC if engine == "piper" else EDGE_CHARS_PER_SEC
    total_chars = sum(len(text) for _, text in jobs)
    print(
        f"Estimated synthesis time: ~{format_duration(total_chars / rate)} "
        f"for {total_chars:,} characters across {len(jobs)} file(s) (rough estimate)"
    )

    if engine == "piper":
        return _piper(jobs, output_dir, model, use_cuda)
    if engine == "edge":
        return _edge(jobs, output_dir, voice or DEFAULT_EDGE_VOICE)

    raise ValueError(f"Unknown TTS engine: {engine!r}. Use 'piper', 'edge', or 'none'.")


def format_duration(seconds: float) -> str:
    """Turn a number of seconds into e.g. '1h 4m 09s' or '4m 09s' or '9s'."""
    total = int(round(max(0.0, seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def _resolve_model(model: str | Path | None) -> Path:
    path = Path(model) if model else _PROJECT_ROOT / DEFAULT_PIPER_MODEL
    if not path.exists():
        raise FileNotFoundError(
            f"Piper voice model not found: {path}\n"
            "Download one with:\n"
            "    python -m piper.download_voices en_US-kusal-medium\n"
            "or pass a path with --model /path/to/voice.onnx"
        )
    return path


def _piper(jobs: list[Job], output_dir: Path, model: str | Path | None, use_cuda: bool) -> list[Path]:
    try:
        from piper import PiperVoice
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise RuntimeError(
            "piper-tts is not installed. Install it with: pip install piper-tts"
        ) from exc

    model_path = _resolve_model(model)
    voice = PiperVoice.load(str(model_path), use_cuda=use_cuda)

    paths: list[Path] = []
    for i, (stem, text) in enumerate(jobs, 1):
        out_path = output_dir / f"{stem}.wav"
        print(f"  [{i}/{len(jobs)}] {out_path.name}  ({len(text):,} chars)")
        with wave.open(str(out_path), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        paths.append(out_path)
    return paths


def _edge(jobs: list[Job], output_dir: Path, voice: str) -> list[Path]:
    return asyncio.run(_edge_async(jobs, output_dir, voice))


async def _edge_async(jobs: list[Job], output_dir: Path, voice: str) -> list[Path]:
    try:
        import edge_tts
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise RuntimeError(
            "edge-tts is not installed. Install it with: pip install edge-tts"
        ) from exc

    paths: list[Path] = []
    for i, (stem, text) in enumerate(jobs, 1):
        out_path = output_dir / f"{stem}.mp3"
        print(f"  [{i}/{len(jobs)}] {out_path.name}  ({len(text):,} chars)")
        await edge_tts.Communicate(text, voice).save(str(out_path))
        paths.append(out_path)
    return paths
