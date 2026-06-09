from pathlib import Path
import socket
import sys

PROJECT_DIR = Path(__file__).resolve().parent
EXPECTED_PYTHON = PROJECT_DIR / "venv" / "Scripts" / "python.exe"
BOT_LOCK_PORT = 45192
_bot_lock_socket: socket.socket | None = None


def check_pycharm_interpreter() -> None:
    current_python = Path(sys.executable).resolve()
    expected_python = EXPECTED_PYTHON.resolve()

    print("================================")
    print("PYTHON ĐANG CHẠY:", current_python)
    print("PYTHON CẦN DÙNG :", expected_python)
    print("================================")

    if current_python != expected_python:
        raise RuntimeError(
            "PyCharm đang chạy sai Python interpreter.\n"
            f"Hãy chọn interpreter này trong PyCharm:\n{expected_python}"
        )

    try:
        import edge_tts
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Không tìm thấy edge_tts trong venv.\n"
            "Chạy lệnh: venv\\Scripts\\python.exe -m pip install -r requirements.txt"
        ) from exc

    print("edge-tts version:", edge_tts.__version__)
    print("Interpreter OK. Đang khởi động bot...")


def acquire_single_instance_lock() -> None:
    global _bot_lock_socket

    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)

    try:
        lock_socket.bind(("127.0.0.1", BOT_LOCK_PORT))
        lock_socket.listen(1)
    except OSError as exc:
        lock_socket.close()
        raise RuntimeError(
            "Bot đang được chạy ở một cửa sổ/process khác.\n"
            "Hãy stop toàn bộ bot cũ rồi chạy lại main.py."
        ) from exc

    _bot_lock_socket = lock_socket


from bot import main


if __name__ == "__main__":
    check_pycharm_interpreter()
    acquire_single_instance_lock()
    main()
