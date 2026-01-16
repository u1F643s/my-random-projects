import sys
import ctypes
from ctypes import wintypes
import threading
from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

import requests
import os

# I spent hours trying to spell opasity, oops i mean opacity
FRAME_OPACITY = 0.38
GLASS_OPACITY = 0.15

# Some pixels transparent, so it works better, like a window
def make_white_transparent(img: Image.Image, threshold: int = 12) -> Image.Image:
    img = img.convert("RGBA")
    datas = list(img.getdata())
    out = []
    min_alpha = int(round(255 * GLASS_OPACITY))
    
    # Loop through every pixel
    for (r, g, b, a) in datas:
        dist = max(255 - r, 255 - g, 255 - b)
        if dist <= threshold:
            if threshold == 0:
                alpha_from_white = min_alpha
            else:
                # um what is this? oh I remember, some math to make it look smoother
                alpha_from_white = int(round(min_alpha + (255 - min_alpha) * (dist / threshold)))
            final_alpha = int(round(a * (alpha_from_white / 255)))
            out.append((r, g, b, final_alpha))
        else:
            out.append((r, g, b, a))
    img.putdata(out)
    return img

# Stretch that image to fit my screen
def stretch_and_save(source_path: Path, out_path: Path, screen_width: int, screen_height: int, white_threshold: int = 12):
    img = Image.open(source_path)
    try:
        resample = Image.Resampling.LANCZOS  # The fancy high-quality way
    except AttributeError:
        resample = Image.LANCZOS  # The old-school way 
    
    # Stretch it to fit the whole screen - no aspect ratio mercy, or it'll have no mercy on me
    stretched = img.resize((screen_width, screen_height), resample=resample)
    processed = make_white_transparent(stretched, threshold=white_threshold)
    processed.save(out_path, format="PNG")

# Our overlay class, where it slaps the image on the screen
class Overlay(QLabel):
    def __init__(self, image_path):
        super().__init__()

        # Load nice image to make our ac work
        pixmap = QPixmap(str(image_path))
        
        # frameless the window
        self.setWindowFlags(
            Qt.FramelessWindowHint | # frameless
            Qt.WindowStaysOnTopHint |  # topmost
            Qt.Tool  # remove in taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # Transparent background
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # click-through

        self.setPixmap(pixmap)
        self.resize(pixmap.size())
        self.setWindowOpacity(FRAME_OPACITY)  # Set the see-through level

        self.show()  # Tada! 🎉
        
        # click through enchance for windows 
        try:
            hwnd = int(self.winId())  
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            prev = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, prev | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        except Exception:
            pass  # if this fails, we'll just cry silently
        
        # setup our escape routre
        self.setup_global_hotkey()
    # omg i'm tired of adding comments
    # Setup the global hotkey
    def setup_global_hotkey(self):
        # Windows API constants, the part the makes me scream at wikipedia
        MOD_CONTROL = 0x0002  # Ctrl
        MOD_SHIFT = 0x0004   # Shift 
        VK_A = 0x41          # The letter 'A' - surprise!
        WM_HOTKEY = 0x0312   # Hotkey message
        hotkey_id = 1        # hotkey's ID number

        def loop():
            print("trying to start a thread for the hotkey")
            # Register our hotkey
            result = ctypes.windll.user32.RegisterHotKey(None, hotkey_id, MOD_CONTROL | MOD_SHIFT, VK_A)
            print(f"RegisterHotKey's nice result: {result}")
            if result == 0:
                error = ctypes.windll.kernel32.GetLastError()
                print(f"RegisterHotKey failed with a creepy error: {error}")
                return  # 😭 failed
            
            print("waiting for hotkey,  ")
            msg = wintypes.MSG()
            # listen for windows messages like some creep
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                print(f"Received message, it's: {msg.message}")
                if msg.message == WM_HOTKEY:
                    print("ay now ur ac wont work")
                    os._exit(0)  # BYE MORTAL
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        # Start the hotkey listening thread
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        print("hmm it started, the thread btw")

# the main function - where everything comes together! 🎉 FINALLY
def main():
    # Our image files, pls dont visit my github
    src = Path("windoww.png")
    cache = Path("windowtemp.png")
    url = "https://cdn.jsdelivr.net/gh/u1F643s/assets-for-my-projects@main/windoww.png"

    # Download the image if we don't have it locally
    try:
        if not src.exists():
            print("Local image not found. Downloading...from the url in the code")
            response = requests.get(url)
            response.raise_for_status()
            with open(src, "wb") as f:
                f.write(response.content)
            print(f"Downloaded the grand image to {src.resolve()}")
    except Exception as e:
        print(f"omg shot, Error getting image: {e}")
        sys.exit(1)  # just shit it

    # gui engine
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    screen_size = screen.size()
    w, h = screen_size.width(), screen_size.height()

    # Process our image and create the overlay, omg my arms are hurting typing comments
    stretch_and_save(src, cache, w, h, white_threshold=12)

    # Create our beautiful overlay window (it's not cinematic)
    overlay = Overlay(cache)
    
    # here goes nothing.. i mean something
    sys.exit(app.exec())
    

# Check if we're running the script directly
if __name__ == "__main__":
    main()


"""
“A computer is like air conditioning — it becomes useless when you open Windows.”
— Linus Torvalds
"""
# i wish this program helps
# i added a window overlay for Windows, now AC will work




#My Windows still freezes and eats up my RAM.



#I like Linux, btw, even though I don’t get to use it except in my VM, which doesn’t work because I don’t have enough RAM to do anything except run the desktop (Ubuntu).
