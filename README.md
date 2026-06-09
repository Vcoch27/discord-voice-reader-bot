# Vietnamese Discord TTS Bot

## Overview

This is a lightweight Discord Vietnamese TTS bot optimized for small containers such as Northflank `nf-compute-10`. It uses Microsoft Edge-TTS to generate Vietnamese speech, FFmpeg to stream audio into Discord voice channels, and bounded per-guild queues to keep memory predictable.

## Features

- `/tts text:<message>` reads Vietnamese text in the user's current voice channel.
- `/voice gender:<female|male>` changes the Vietnamese voice for the current server.
- `/join` joins the user's current voice channel.
- `/leave` disconnects the bot from voice.
- `/stop` stops playback and clears the queue.
- `/ping` runtime health check.
- Per-guild queue with configurable queue limit.
- Configurable TTS text length limit.
- Temporary audio cleanup after playback and on startup.
- Low-resource configuration through environment variables.

## Resource Target

- Minimum test target: `0.1 vCPU / 256 MB RAM`.
- More stable target: `0.2 vCPU / 512 MB RAM`.
- Runtime storage target: `1 GB`.
- No public port is required because this is a Discord worker, not a web server.

The default limits are intentionally conservative: `MAX_TTS_CHARS=200`, `MAX_QUEUE_SIZE=3`, and `TTS_TIMEOUT_SECONDS=30`.

## Environment Variables

Never commit a real `.env` file. Commit only `.env.example`.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `DISCORD_TOKEN` | Yes | none | Discord bot token from the Discord Developer Portal. |
| `COMMAND_PREFIX` | No | `!` | Prefix for classic commands if used. |
| `FFMPEG_EXECUTABLE` | No | `ffmpeg` | FFmpeg executable. Use `ffmpeg` on Docker/Northflank. A local Windows path is only acceptable in a local uncommitted `.env`. |
| `LOG_LEVEL` | No | `INFO` | Python logging level. |
| `TTS_RATE` | No | `+0%` | Edge-TTS speech rate. |
| `TTS_VOLUME` | No | `+0%` | Edge-TTS speech volume. |
| `TTS_PITCH` | No | `+0Hz` | Edge-TTS speech pitch. |
| `MAX_TTS_CHARS` | No | `200` | Maximum characters per TTS request. Lower this if memory or CPU is tight. |
| `MAX_QUEUE_SIZE` | No | `3` | Maximum queued TTS requests per guild, not counting active playback. |
| `TTS_TIMEOUT_SECONDS` | No | `30` | Timeout for Edge-TTS generation. |
| `AUDIO_TEMP_DIR` | No | `/tmp/discord-tts` | Directory for temporary audio files. |
| `CLEANUP_TEMP_ON_START` | No | `true` | Delete stale `tts-*.mp3` files on startup. |
| `DISCORD_INTENTS_MINIMAL` | No | `true` | Use minimal Discord intents for slash commands and voice state. |

Example `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token_here
COMMAND_PREFIX=!
FFMPEG_EXECUTABLE=ffmpeg
LOG_LEVEL=INFO
TTS_RATE=+0%
TTS_VOLUME=+0%
TTS_PITCH=+0Hz
MAX_TTS_CHARS=200
MAX_QUEUE_SIZE=3
TTS_TIMEOUT_SECONDS=30
AUDIO_TEMP_DIR=/tmp/discord-tts
CLEANUP_TEMP_ON_START=true
DISCORD_INTENTS_MINIMAL=true
```

## Local Setup Without Docker

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` and edit `DISCORD_TOKEN`:

```bash
cp .env.example .env
```

On Windows, FFmpeg can be installed with:

```powershell
winget install Gyan.FFmpeg
```

If needed for local Windows only, `FFMPEG_EXECUTABLE` may be an absolute local path in `.env`. Do not use a `C:/Users/...` path on Docker or Northflank.

Run the bot:

```bash
python main.py
```

## Local Test With Docker

Build:

```bash
docker build -t discord-tts-bot .
```

Run with small runtime limits:

```bash
docker run --rm --env-file .env --memory=256m --cpus=0.1 discord-tts-bot
```

For a detached container:

```bash
docker run -d --name discord-tts-bot --env-file .env --memory=256m --cpus=0.1 discord-tts-bot
docker logs -f discord-tts-bot
```

Docker Compose is optional for local testing:

```bash
docker compose up --build
```

## Northflank Deployment

1. Push the cleaned repository to GitHub.
2. Create a new Northflank project.
3. Create a new Combined Service or Deployment Service from the GitHub repository.
4. Select the `main` branch.
5. Select Dockerfile build.
6. Set Dockerfile path to `./Dockerfile`.
7. Choose compute plan:
   - Start with `nf-compute-10` for testing.
   - If OOM or restarts occur, upgrade to `nf-compute-20`.
8. Do not expose a public port.
9. Add runtime variables or a secret group:
   - `DISCORD_TOKEN`
   - `COMMAND_PREFIX=!`
   - `FFMPEG_EXECUTABLE=ffmpeg`
   - `LOG_LEVEL=INFO`
   - `TTS_RATE=+0%`
   - `TTS_VOLUME=+0%`
   - `TTS_PITCH=+0Hz`
   - `MAX_TTS_CHARS=200`
   - `MAX_QUEUE_SIZE=3`
   - `TTS_TIMEOUT_SECONDS=30`
   - `AUDIO_TEMP_DIR=/tmp/discord-tts`
   - `CLEANUP_TEMP_ON_START=true`
   - `DISCORD_INTENTS_MINIMAL=true`
10. Deploy.
11. Open Northflank logs and verify successful Discord login.
12. Test `/ping` and `/tts` in Discord.

## Discord Developer Portal Setup

1. Open `https://discord.com/developers/applications`.
2. Create an application and bot.
3. Copy the bot token into local `.env` or Northflank `DISCORD_TOKEN`.
4. Go to OAuth2 URL Generator.
5. Select scopes:
   - `bot`
   - `applications.commands`
6. Select bot permissions:
   - `Connect`
   - `Speak`
   - `Use Voice Activity`
   - `Send Messages`
7. Open the generated invite URL and add the bot to your server.

No privileged gateway intents are required for the current code.

## Troubleshooting

### Bot restarts or OOM

Reduce `MAX_TTS_CHARS`, reduce `MAX_QUEUE_SIZE`, and keep `TTS_TIMEOUT_SECONDS` low. If restarts continue on `nf-compute-10`, upgrade to `nf-compute-20`.

### FFmpeg not found

Ensure the Dockerfile installs FFmpeg and set this on Northflank:

```env
FFMPEG_EXECUTABLE=ffmpeg
```

Do not use a `C:/Users/...` FFmpeg path in Docker or Linux deployment.

### Discord token missing

The bot exits with:

```text
DISCORD_TOKEN is required. Set it locally in .env or in Northflank runtime variables.
```

Set `DISCORD_TOKEN` in local `.env` or Northflank runtime variables.

### Bot cannot join voice

Check the user is already in a voice channel. Check bot permissions: `Connect`, `Speak`, and `Use Voice Activity`. Also confirm `PyNaCl` is installed from `requirements.txt`.

### Audio files are not deleted

Check `AUDIO_TEMP_DIR` permissions. Docker creates `/tmp/discord-tts` and assigns it to the non-root `appuser`.

### Token leaked

If `.env` or a real `DISCORD_TOKEN` was ever committed, reset the token immediately in the Discord Developer Portal. Removing `.env` from the latest commit does not remove it from Git history.

## Useful Commands

```bash
python -m compileall .
python scripts/sanity_check.py
docker build -t discord-tts-bot .
docker run --rm --env-file .env --memory=256m --cpus=0.1 discord-tts-bot
docker ps
docker logs -f discord-tts-bot
docker stop discord-tts-bot
git status
git add .
git commit -m "chore: optimize Discord TTS bot for low-resource deployment"
git push origin main
```

## Project Structure

```text
discord-voice-reader-bot/
|-- main.py
|-- bot.py
|-- commands/
|-- services/
|-- config/
|-- scripts/
|-- Dockerfile
|-- docker-compose.yml
|-- .dockerignore
|-- .env.example
|-- requirements.txt
|-- README.md
`-- VOICE_ISSUES_AND_FIXES.md
```
