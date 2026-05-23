import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("alicey.nowplaying")
except Exception:
    pass

from twitter import run_gui

run_gui()
