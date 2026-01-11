import pyautogui
import time
import pyperclip
import ctypes
from ctypes import wintypes

def open_chrome():
    pyautogui.press("win")
    time.sleep(0.5)
    pyautogui.write("chrome")
    pyautogui.press("enter")

def open_notepad():
    pyautogui.press("win")
    time.sleep(0.5)
    pyautogui.write("notepad")
    pyautogui.press("enter")

# Windows virtual key codes for media
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

def _keybd_event(vk_code):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

def media_play_pause():
    _keybd_event(VK_MEDIA_PLAY_PAUSE)

def media_next():
    _keybd_event(VK_MEDIA_NEXT_TRACK)

def media_prev():
    _keybd_event(VK_MEDIA_PREV_TRACK)

def volume_up():
    _keybd_event(VK_VOLUME_UP)

def volume_down():
    _keybd_event(VK_VOLUME_DOWN)

def mute_toggle():
    _keybd_event(VK_VOLUME_MUTE)

def switch_window_alt_tab():
    # hold alt, press tab
    pyautogui.keyDown('alt')
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.keyUp('alt')

def maximize_active():
    pyautogui.hotkey('win', 'up')

def minimize_active():
    pyautogui.hotkey('win', 'down')

def snap_left():
    pyautogui.hotkey('win', 'left')

def snap_right():
    pyautogui.hotkey('win', 'right')

def copy_to_clipboard(text: str):
    pyperclip.copy(text)

def paste_from_clipboard():
    return pyperclip.paste()
