import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

from twitter import run_gui

if __name__ == "__main__":
    run_gui()
