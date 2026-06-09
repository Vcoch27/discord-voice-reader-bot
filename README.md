# Vietnamese Discord TTS Bot

## Overview

Discord Vietnamese TTS Bot is a Python 3.12 background worker for Discord voice channels. It uses Microsoft Edge-TTS for Vietnamese speech, FFmpeg for audio playback, supports per-guild queues, and lets users choose female or male Vietnamese voices.

## Features

- `/tts2 text:<message>` reads Vietnamese text in the user's current voice channel.
- `/voice gender:<female|male>` changes the Vietnamese voice for the current server.
- `/join` joins the user's current voice channel.
- `/leave` disconnects the bot from voice.
- `/stop` stops playback and clears the queue.
- `/ping` health check.
- Per-guild TTS queue to avoid overlapping playback.
- Temporary audio files are deleted after playback.

## Requirements

- Python 3.12
- FFmpeg
- Discord bot token
- Docker for container deployment

## Local Setup

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set a real Discord bot token:

```env
DISCORD_TOKEN=your_real_token_here
```

Run the bot:

```powershell
python main.py
```

## Environment Variables

Do not commit a real `.env` file to GitHub. Commit only `.env.example`.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `DISCORD_TOKEN` | Yes | none | Discord bot token from the Discord Developer Portal. |
| `COMMAND_PREFIX` | No | `!` | Prefix for classic commands if used. |
| `FFMPEG_EXECUTABLE` | No | `ffmpeg` | FFmpeg executable name or path. Use `ffmpeg` for Docker and Northflank. A local Windows path is only for local development. |
| `LOG_LEVEL` | No | `INFO` | Python logging level. |
| `TTS_RATE` | No | `+0%` | Edge-TTS speech rate. |
| `TTS_VOLUME` | No | `+0%` | Edge-TTS speech volume. |
| `TTS_PITCH` | No | `+0Hz` | Edge-TTS speech pitch. |

Example:

```env
DISCORD_TOKEN=your_discord_bot_token_here
COMMAND_PREFIX=!
FFMPEG_EXECUTABLE=ffmpeg
LOG_LEVEL=INFO
TTS_RATE=+0%
TTS_VOLUME=+0%
TTS_PITCH=+0Hz
```

## Docker Setup

Build the image:

```powershell
docker build -t discord-vietnamese-tts-bot .
```

Run with a local `.env` file:

```powershell
docker run --rm --env-file .env discord-vietnamese-tts-bot
```

The container does not expose a port because this bot is a Discord worker, not a web server.

## Deploy On Northflank

1. Create a Project on Northflank.
2. Create a Service from the GitHub repository.
3. Select branch `main`.
4. Set Build type to `Dockerfile`.
5. Set Dockerfile path to `./Dockerfile`.
6. Do not configure a public port.
7. Add runtime environment variables:
   - `DISCORD_TOKEN`
   - `COMMAND_PREFIX`
   - `FFMPEG_EXECUTABLE`
   - `LOG_LEVEL`
   - `TTS_RATE`
   - `TTS_VOLUME`
   - `TTS_PITCH`
8. Set `FFMPEG_EXECUTABLE=ffmpeg` on Northflank.
9. Deploy the service.
10. Open logs and confirm the bot logs in successfully.

## Discord Developer Portal Setup

1. Open `https://discord.com/developers/applications`.
2. Create an application and bot.
3. Copy the bot token into `.env` locally or into `DISCORD_TOKEN` on Northflank.
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

### DISCORD_TOKEN is required

The bot exits when `DISCORD_TOKEN` is missing or still set to a placeholder. Set a real token in `.env` locally or in Northflank runtime variables.

### FFmpeg not found

Install FFmpeg and make sure it is available in `PATH`.

On Windows:

```powershell
winget install Gyan.FFmpeg
ffmpeg -version
```

For Docker and Northflank, keep:

```env
FFMPEG_EXECUTABLE=ffmpeg
```

Do not use a `C:/Users/...` FFmpeg path in Docker or Linux deployment.

### Missing PyNaCl

Discord voice requires voice dependencies. This project includes:

```text
discord.py[voice]
PyNaCl
```

Reinstall dependencies:

```powershell
pip install -r requirements.txt
```

### Bot does not join a voice channel

Confirm the user is already in a voice channel before running the command. Also confirm the bot has `Connect`, `Speak`, and `Use Voice Activity` permissions for that server and channel.

### Token leaked

If `.env` or a real `DISCORD_TOKEN` was ever committed, rotate the token immediately in the Discord Developer Portal. Removing `.env` from the latest commit is not enough because Git history can still contain the secret. Rewrite history with `git filter-repo` or BFG, then force-push only after coordinating with anyone else using the repository.

## Project Structure

```text
discord-voice-reader-bot/
|-- main.py
|-- bot.py
|-- commands/
|-- services/
|-- config/
|-- Dockerfile
|-- .dockerignore
|-- .env.example
|-- requirements.txt
|-- README.md
`-- VOICE_ISSUES_AND_FIXES.md
```
