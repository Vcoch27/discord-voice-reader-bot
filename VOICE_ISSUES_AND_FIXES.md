# 🔍 Phân Tích Các Vấn Đề Voice Không Đúng Trong Discord

## ❌ Nguyên Nhân Chính Gây Voice Không Đúng

### 1. **Race Condition - Queue Worker Bị Stuck** (CRITICAL)
**Vị trí:** `services/queue_service.py` - Method `_worker()` (dòng 75-102)

**Vấn đề:**
- Nếu `queue.get()` được gọi trong khi queue trống, nó sẽ chờ vô thời hạn
- Khi `stop()` được gọi và queue trở nên trống, worker thread không thể thoát
- Điều này khiến voice playback bị treo hoặc delay không lý do

**Cách sửa (đã áp dụng):**
- Thêm `asyncio.wait_for()` với timeout để tránh infinite waiting
- Nếu queue trống trong 1 giây, worker sẽ thoát gracefully

```python
# Trước (sai):
item = await self.queue.get()  # Sẽ chờ vô thời hạn nếu queue trống

# Sau (đúng):
try:
    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
except asyncio.TimeoutError:
    if self.queue.empty():
        break
```

---

### 2. **FFmpeg Audio Filter Gây Biến Dạng Giọng**
**Vị trí:** `services/audio_service.py` - Method `create_audio_source()` (dòng 18)

**Vấn đề:**
```python
options="-vn -filter:a loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 -ac 2"
```
- `loudnorm` filter áp dụng **normalization quá mạnh** trên giọng nói
- Khiến giọng bị nén (compressed), hoặc biến dạng chất lượng âm thanh
- Giọng nghe có vẻ "robot", "bóp" hoặc không tự nhiên

**Cách sửa (đã áp dụng):**
- Loại bỏ `loudnorm` filter
- Thay thế bằng `volume=0.8` để điều chỉnh âm lượng nhẹ nhàng

```python
# Trước (luôn biến dạng):
options="-vn -filter:a loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 -ac 2"

# Sau (giữ nguyên chất lượng):
options="-vn -af \"volume=0.8\" -ar 48000 -ac 2"
```

---

### 3. **Không Có Error Handling Cho Edge-TTS Failures**
**Vị trí:** `services/tts_service.py` - Method `synthesize()` (dòng 31-49)

**Vấn đề:**
- Nếu Edge-TTS API bị lỗi, không có error message rõ ràng
- Không biết đó là lỗi gì (network, invalid voice, API failure...)
- Code chỉ in ra `print()` thay vì `logger.info()`

**Cách sửa (đã áp dụng):**
- Thêm proper exception handling với chi tiết error
- Ghi log tất cả TTS settings (voice, rate, volume, pitch)
- Giúp debug dễ dàng khi có vấn đề

```python
# Trước (không log):
print("VOICE USED:", voice_name)  # Vô dụng
await communicate.save(str(file_path))

# Sau (có log chi tiết):
logger.info("Synthesizing Vietnamese speech with voice %s (gender=%s)...", voice_name, gender)
try:
    await communicate.save(str(file_path))
except Exception as e:
    logger.error("Failed to synthesize TTS with voice %s. Error: %s", voice_name, str(e))
    raise
```

---

### 4. **Voice Gender Reset Khi Bot Restart**
**Vị trí:** `services/queue_service.py` - `GuildTTSQueue.__init__()` (dòng 19)

**Vấn đề:**
- Khi bot khởi động lại, tất cả voice gender được reset về **FEMALE** (default)
- Không có persistence (lưu trữ) voice preference của user
- User phải re-select voice sau mỗi lần bot restart

**Giải pháp lâu dài:**
- Cần thêm database (SQLite) hoặc file để lưu user preferences
- Khi bot start, load preferences từ database

```python
# Cần thêm vào config/settings.py:
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_data.db")

# Sau đó add migration để load voice preferences khi bot start
```

---

### 5. **Thiếu Logging Chi Tiết Cho Voice Gender Changes**
**Vị trí:** `services/queue_service.py` - Method `set_voice_gender()` (dòng 57-59)

**Vấn đề:**
- Không log khi voice gender được thay đổi
- Khó debug nếu voice sai

**Cách sửa (đã áp dụng):**
```python
logger.info(
    "Guild %s: Voice gender changed from %s to %s. Using voice: %s",
    self.guild_id, old_gender, gender, voice_name
)
```

---

## ✅ Các Bước Đã Hoàn Thành

- [x] Sửa race condition trong queue worker
- [x] Loại bỏ FFmpeg loudnorm filter gây biến dạng
- [x] Thêm proper error handling cho Edge-TTS
- [x] Thêm chi tiết logging cho voice gender
- [x] Improve TTS settings logging (rate, volume, pitch)

---

## 🧪 Kiểm Tra Kết Quả

Sau các sửa chữa, bạn sẽ thấy logs chi tiết hơn:

```
2026-06-08 10:00:00 | INFO | services.tts_service | Synthesizing Vietnamese speech with Edge-TTS voice vi-VN-HoaiMyNeural (gender=female). Rate=+0%, Volume=+0%, Pitch=+0Hz
2026-06-08 10:00:02 | INFO | services.tts_service | Successfully saved TTS audio to C:\...\tts-abc123def456.mp3
2026-06-08 10:00:02 | INFO | services.queue_service | Guild 123456789: Voice gender changed from female to male. Using voice: vi-VN-NamMinhNeural
```

---

## 🚀 Khuyến Nghị Thêm

### 1. **Lưu trữ Voice Preference**
Thêm SQLite database để lưu voice preference per guild:
```python
# services/db_service.py
class DatabaseService:
    async def save_guild_voice_gender(self, guild_id: int, gender: VoiceGender) -> None:
        # INSERT OR UPDATE vào database
        pass
    
    async def load_guild_voice_gender(self, guild_id: int) -> VoiceGender:
        # SELECT từ database, default FEMALE nếu không tìm thấy
        pass
```

### 2. **Retry Mechanism Cho Edge-TTS**
Thêm exponential backoff retry nếu Edge-TTS API fail:
```python
@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3),
)
async def synthesize(self, text: str, gender: VoiceGender) -> Path:
    # ...
```

### 3. **Health Check Cho Voice**
Thêm command để test voice:
```python
@app_commands.command(name="test_voice")
async def test_voice(self, interaction: discord.Interaction):
    # Synthesize test text "Đây là giọng test" để xác nhận voice đang hoạt động
    pass
```

---

## 📊 Tóm Tắt

| Vấn đề | Mức Độ | Trạng Thái |
|--------|--------|-----------|
| Queue worker race condition | 🔴 CRITICAL | ✅ Đã sửa |
| FFmpeg loudnorm distortion | 🟠 HIGH | ✅ Đã sửa |
| Missing error handling | 🟠 HIGH | ✅ Đã sửa |
| Voice persistence | 🟡 MEDIUM | ⏳ Cần thêm |
| Missing logging | 🟡 MEDIUM | ✅ Đã sửa |


