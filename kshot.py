import subprocess
import os
import tempfile
import json
from PyQt6.QtGui import QAction, QImage
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QTimer, QDateTime, Qt, QThread, pyqtSignal
from AppKit import NSEvent, NSKeyDownMask

class ScreenshotWorker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name

            result = subprocess.run(["screencapture", "-i", tmp_path], check=False)
            
            if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                self.finished_signal.emit(tmp_path)
            else:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def stop(self):
        self.terminate()
        self.wait()

class Plugin:
    def __init__(self, ktools):
        self.ktools = ktools
        self.name = "kshot"
        self.config_path = os.path.join(os.path.dirname(__file__), "kshot.json")

        self.load_config()
        self.worker = None

        def handler(event):
            mask = (1 << 20) | (1 << 19)
            if event.keyCode() == 50 and (event.modifierFlags() & mask) == mask:
                QTimer.singleShot(0, self.take_screenshot)
                return None
            return event

        self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, handler)
        self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, handler)

        self.action = QAction("take screenshot (⌥⌘`)", self.ktools.menu)
        self.action.triggered.connect(self.take_screenshot)

    def load_config(self):
        default_path = os.path.join(os.path.expanduser("~"), "Pictures", "kshots")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    self.config = json.load(f)
            except:
                self.config = {"save_path": default_path, "enabled": True}
        else:
            self.config = {"save_path": default_path, "enabled": True}
            self.save_config()

        if self.config["enabled"] and not os.path.exists(self.config["save_path"]):
            os.makedirs(self.config["save_path"], exist_ok=True)

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def take_screenshot(self):
        if self.worker and self.worker.isRunning():
            return

        self.worker = ScreenshotWorker()
        self.worker.finished_signal.connect(self.process_screenshot)
        self.worker.error_signal.connect(lambda msg: self.ktools.notify(f"error: {msg}"))
        self.worker.start()

    def process_screenshot(self, tmp_path):
        try:
            image = QImage(tmp_path)
            if not image.isNull():
                QApplication.clipboard().setImage(image)

                if self.config.get("enabled"):
                    if not os.path.exists(self.config["save_path"]):
                        os.makedirs(self.config["save_path"], exist_ok=True)
                    
                    filename = f"shot_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.png"
                    save_full_path = os.path.join(self.config["save_path"], filename)
                    image.save(save_full_path, "PNG")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def select_screenshots_folder(self):
        folder = QFileDialog.getExistingDirectory(None, "select screenshots folder", self.config["save_path"])
        if folder:
            self.config["save_path"] = folder
            self.save_config()
            self.ktools.notify(f"folder changed")

    def toggle_saving(self):
        self.config["enabled"] = not self.config.get("enabled", True)
        self.save_config()
        status = "enabled" if self.config["enabled"] else "disabled"
        self.ktools.notify(f"saving to disk: {status}")

    def unload(self):
        try:
            if hasattr(self, 'global_monitor') and self.global_monitor:
                NSEvent.removeMonitor_(self.global_monitor)
                self.global_monitor = None
            if hasattr(self, 'local_monitor') and self.local_monitor:
                NSEvent.removeMonitor_(self.local_monitor)
                self.local_monitor = None
        except: pass

        if self.worker and self.worker.isRunning():
            self.worker.finished_signal.disconnect()
            self.worker.stop()
            self.worker = None

        try:
            self.action.triggered.disconnect()
        except: pass

        import gc
        gc.collect()
        print("kshot: monitors and workers cleaned up")

    def get_actions(self):
        return [self.action]

    def update_theme(self):
        pass