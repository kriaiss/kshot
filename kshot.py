import subprocess
import os
import tempfile
import json
import gc
from PyQt6.QtGui import QAction, QImage
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QTimer, QDateTime, Qt, QProcess, QMimeData, QByteArray
from AppKit import NSEvent, NSKeyDownMask

class Plugin:
    def __init__(self, ktools):
        self.ktools = ktools
        self.name = "kshot"
        self.config_path = os.path.join(os.path.dirname(__file__), "kshot.json")
        self.config = {}

        self._load_config()
        self.worker = None

        self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, self._global_hotkey_handler)
        self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, self._local_hotkey_handler)

        self.action = QAction("take screenshot (⌥⌘`)", self.ktools.manager)
        self.action.triggered.connect(self.take_screenshot)

    def get_actions(self):
        return [self.action]

    def update_theme(self):
        pass
    
    def unload(self):
        try:
            if hasattr(self, 'global_monitor') and self.global_monitor:
                NSEvent.removeMonitor_(self.global_monitor)
                self.global_monitor = None
            if hasattr(self, 'local_monitor') and self.local_monitor:
                NSEvent.removeMonitor_(self.local_monitor)
                self.local_monitor = None
        except Exception: 
            pass

        if hasattr(self, 'capture_process') and self.capture_process:
            self.capture_process.kill()
            self.capture_process = None

        try:
            self.action.triggered.disconnect()
        except Exception: 
            pass
        gc.collect()

    def _load_config(self):
        default_path = os.path.join(os.path.expanduser("~"), "Pictures", "kshots")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {"save_path": default_path, "enabled": True}
        else:
            self.config = {"save_path": default_path, "enabled": True}
            self._save_config()

        if self.config.get("enabled", True) and not os.path.exists(self.config.get("save_path", default_path)):
            os.makedirs(self.config["save_path"], exist_ok=True)

    def _save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"kshot: failed to save config {e}")

    def _global_hotkey_handler(self, event):
        mask = (1 << 20) | (1 << 19)
        if event.keyCode() == 50 and (event.modifierFlags() & mask) == mask:
            QTimer.singleShot(0, self.take_screenshot)

    def _local_hotkey_handler(self, event):
        mask = (1 << 20) | (1 << 19)
        if event.keyCode() == 50 and (event.modifierFlags() & mask) == mask:
            QTimer.singleShot(0, self.take_screenshot)
            return None
        return event

    # multi-monitor crash fix
    def take_screenshot(self):
        if hasattr(self, 'capture_process') and self.capture_process and self.capture_process.state() == QProcess.ProcessState.Running:
            return

        self.tmp_path = os.path.join(tempfile.gettempdir(), f"kshot_{QDateTime.currentDateTime().toMSecsSinceEpoch()}.png")
        
        self.capture_process = QProcess()
        self.capture_process.finished.connect(self._on_capture_finished)
        self.capture_process.errorOccurred.connect(lambda err: self.ktools.notify(f"error: {err}"))

        self.capture_process.start("screencapture", ["-i", self.tmp_path])

    def _on_capture_finished(self, exitCode, exitStatus):
        if exitCode == 0 and os.path.exists(self.tmp_path) and os.path.getsize(self.tmp_path) > 0:
            self.process_screenshot(self.tmp_path)
        else:
            if os.path.exists(self.tmp_path):
                os.remove(self.tmp_path)
            self.ktools.notify("capture aborted")

    def process_screenshot(self, tmp_path):
        try:
            self.last_image = QImage(tmp_path)
            if not self.last_image.isNull():

                QApplication.clipboard().setImage(self.last_image)

                if self.config.get("enabled"):
                    if not os.path.exists(self.config["save_path"]):
                        os.makedirs(self.config["save_path"], exist_ok=True)
                    
                    filename = f"shot_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.png"
                    save_full_path = os.path.join(self.config["save_path"], filename)
                    self.last_image.save(save_full_path, "PNG")
                    
                    self.ktools.notify("screenshot saved")
                else:
                    self.ktools.notify("screenshot copied")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def select_screenshots_folder(self):
        folder = QFileDialog.getExistingDirectory(None, "select screenshots folder", self.config["save_path"])
        if folder:
            self.config["save_path"] = folder
            self._save_config()
            self.ktools.notify("folder changed")

    def toggle_saving(self):
        self.config["enabled"] = not self.config.get("enabled", True)
        self._save_config()
        status = "enabled" if self.config["enabled"] else "disabled"
        self.ktools.notify(f"saving to disk: {status}")
