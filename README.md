# Vietnamese Discord TTS Bot

A Python 3.12 Discord voice bot that reads Vietnamese text naturally with Microsoft Edge-TTS.

The bot no longer uses gTTS. Vietnamese speech is generated with Edge-TTS neural voices:

- Female: `vi-VN-HoaiMyNeural`
- Male: `vi-VN-NamMinhNeural`

## Features

- `/tts text:<message>` reads Vietnamese text in your current voice channel.
- `/voice gender:<female|male>` changes the Vietnamese voice for the current server.
- `/join` joins your current voice channel.
- `/leave` disconnects from voice.
- `/stop` stops playback immediately and clears the server queue.
- `/ping` health check.
- Automatically joins the user's voice channel for TTS.
- Prevents overlapping playback.
- Queues TTS messages per Discord server.
- Deletes temporary audio files after playback.
- Uses FFmpeg playback settings tuned for Discord voice.

## Requirements

- Python 3.12
- FFmpeg installed and available in `PATH`
- Discord bot token

## Setup on Windows

1. Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create `.env`:

```powershell
Copy-Item .env.example .env
```

4. Add your Discord token to `.env`:

```env
DISCORD_TOKEN=your_real_token_here
```

5. Run the bot:

```powershell
python main.py
```

You can also run:

```powershell
python bot.py
```

## FFmpeg on Windows

Install with winget:

```powershell
winget install Gyan.FFmpeg
```

Close and reopen PowerShell, then verify:

```powershell
ffmpeg -version
```

Manual install:

1. Download FFmpeg from `https://www.gyan.dev/ffmpeg/builds/`.
2. Extract it to a folder such as `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your Windows `PATH`.
4. Reopen PowerShell and run `ffmpeg -version`.

If FFmpeg is not in `PATH`, set the exact executable path in `.env`:

```env
FFMPEG_EXECUTABLE=C:\ffmpeg\bin\ffmpeg.exe
```

## Discord Developer Portal Setup

1. Open `https://discord.com/developers/applications`.
2. Create a new application.
3. Go to **Bot** and create a bot.
4. Copy the bot token into `.env`.
5. Go to **OAuth2** -> **URL Generator**.
6. Select scopes:
   - `bot`
   - `applications.commands`
7. Select bot permissions:
   - `Connect`
   - `Speak`
   - `Use Voice Activity`
   - `Send Messages`
8. Open the generated invite URL and add the bot to your server.

No privileged gateway intents are required.

## Usage

Join a voice channel, then run:

```text
/voice gender:female
/tts text:Xin chao moi nguoi, hom nay ban the nao?
```

Switch to the male voice:

```text
/voice gender:male
/tts text:Day la giong nam tieng Viet tu Edge TTS.
```

Stop playback:

```text
/stop
```

## Configuration

`.env` values:

```env
DISCORD_TOKEN=your_discord_bot_token_here
COMMAND_PREFIX=!
FFMPEG_EXECUTABLE=ffmpeg
LOG_LEVEL=INFO
TTS_RATE=+0%
TTS_VOLUME=+0%
TTS_PITCH=+0Hz
```

For the most natural Vietnamese, keep the default rate and pitch:

```env
TTS_RATE=+0%
TTS_PITCH=+0Hz
```

You can slightly lower the speed for clearer pronunciation:

```env
TTS_RATE=-5%
```

## Project Structure

```text
discord-tts-bot/
├── main.py
├── bot.py
├── commands/
│   ├── voice.py
│   └── utility.py
├── services/
│   ├── tts_service.py
│   ├── audio_service.py
│   └── queue_service.py
├── config/
│   └── settings.py
├── .env.example
├── requirements.txt
└── README.md
```
