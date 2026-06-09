from pathlib import Path
import shutil
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from config.settings import settings


def main() -> None:
    if shutil.which(settings.ffmpeg_executable) is None:
        raise RuntimeError(f"FFmpeg executable not found: {settings.ffmpeg_executable}")

    settings.audio_temp_dir.mkdir(parents=True, exist_ok=True)
    probe_file = settings.audio_temp_dir / ".write-test"
    probe_file.write_text("ok", encoding="utf-8")
    probe_file.unlink(missing_ok=True)

    print(f"Sanity check OK. Temp dir: {settings.audio_temp_dir}")


if __name__ == "__main__":
    main()
