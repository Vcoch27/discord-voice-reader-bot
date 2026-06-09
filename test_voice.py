import asyncio
import edge_tts

async def main():
    communicate = edge_tts.Communicate(
        "Xin chào buổi tối",
        "vi-VN-HoaiMyNeural"
    )
    await communicate.save("test.mp3")

asyncio.run(main())