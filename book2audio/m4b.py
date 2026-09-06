"""Combine per-chapter audio files into a single chaptered .m4b audiobook.

Shells out to ffmpeg (concat + chapter metadata muxing) rather than pulling in
a dependency, so this only needs ffmpeg/ffprobe on PATH.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(
            f"{name} was not found on PATH, but is required to build a .m4b file.\n"
            "Install ffmpeg (it provides both ffmpeg and ffprobe):\n"
            "  Windows:       winget install Gyan.FFmpeg\n"
            "  macOS:         brew install ffmpeg\n"
            "  Debian/Ubuntu: sudo apt install ffmpeg"
        )
    return path


def _duration_ms(ffprobe: str, path: Path) -> int:
    result = subprocess.run(
        [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return round(float(result.stdout.strip()) * 1000)


def _escape_concat_path(path: Path) -> str:
    # ffmpeg's concat demuxer wraps each entry in single quotes.
    return str(path.resolve()).replace("\\", "/").replace("'", "'\\''")


def _escape_metadata_value(value: str) -> str:
    # ffmetadata1 requires '=', ';', '#', '\' and newlines to be backslash-escaped.
    return re.sub(r"([=;#\\\n])", r"\\\1", value)


def combine_to_m4b(
    audio_paths: list[Path],
    titles: list[str],
    output_path: str | Path,
    *,
    bitrate: str = "64k",
) -> Path:
    """Concatenate ``audio_paths`` into one .m4b at ``output_path``.

    Each ``(path, title)`` pair becomes one chapter, in order. Inputs may be
    any format ffmpeg can decode (the Piper .wav / edge-tts .mp3 outputs of
    :func:`book2audio.tts.synthesize_book` both work) since they are decoded
    and re-encoded to AAC rather than stream-copied.
    """
    if len(audio_paths) != len(titles):
        raise ValueError("audio_paths and titles must be the same length")
    if not audio_paths:
        raise ValueError("No audio files to combine into a .m4b")

    ffmpeg = _require_tool("ffmpeg")
    ffprobe = _require_tool("ffprobe")
    output_path = Path(output_path)

    with tempfile.TemporaryDirectory(prefix="book2audio-m4b-") as tmp:
        tmp_dir = Path(tmp)
        concat_list = tmp_dir / "files.txt"
        chapters_meta = tmp_dir / "chapters.txt"

        concat_list.write_text(
            "\n".join(f"file '{_escape_concat_path(p)}'" for p in audio_paths),
            encoding="utf-8",
        )

        lines = [";FFMETADATA1"]
        cursor_ms = 0
        for path, title in zip(audio_paths, titles):
            duration_ms = _duration_ms(ffprobe, path)
            lines += [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={cursor_ms}",
                f"END={cursor_ms + duration_ms}",
                f"title={_escape_metadata_value(title)}",
                "",
            ]
            cursor_ms += duration_ms
        chapters_meta.write_text("\n".join(lines), encoding="utf-8")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            ffmpeg, "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-i", str(chapters_meta),
            "-map", "0:a", "-map_metadata", "1", "-map_chapters", "1",
            "-c:a", "aac", "-b:a", bitrate,
            "-movflags", "+faststart",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed while building {output_path.name}:\n{result.stderr[-4000:]}"
            )

    return output_path
