<div align="center">
    <pre>
    ____  __.  _________ ___ ___ ___________________
    |    |/ _| /   _____//   |   \\_____  \__    ___/
    |      <   \_____  \/    ~    \/   |   \|    |   
    |    |  \  /        \    Y    /    |    \    |   
    |____|__ \/_______  /\___|_  /\_______  /____|   
            \/        \/       \/         \/         
    </pre>
</div>
<p align="center">
    Custom screenshot utility for ktools.
</p>
<p align="center">
    <img src="https://img.shields.io/badge/python-3.12+-blue?style=flat-square" alt="Python">
    <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="Platform">
</p>

⠀

## What is kshot?

`kshot` is a background worker that wraps the native macOS `screencapture` utility. It allows you to grab regions of your screen and instantly pushes them to your clipboard, completely bypassing the desktop clutter created by the default macOS screenshot tool.

### Core Features
* **Native Capture**: Seamlessly integrates with the system-level macOS `screencapture` crosshair.
* **Smart Clipboard**: Images are pushed directly to your clipboard so you can paste them into chats or docs immediately.
* **Disk Persistence**: Optionally auto-saves timestamped `.png` files to local storage (`~/Pictures/kshots` by default).

⠀

## How to Use (For Users)

1. Download the `kshot` `.zip` archive from the Releases page.
2. Open the **ktools Plugin Manager** from your menu bar and click **import plugins** to install it.
3. Press `⌥⌘\`` (Option + Command + Backtick) anywhere in macOS.
4. Your cursor will turn into the native macOS selection crosshair. Select the area you want to grab.
5. The image is instantly copied to your clipboard.

### Configuring Settings

`kshot` exposes two quick-actions directly in the `ktools` Plugin Manager UI:
* **toggle saving**: Click this to enable or disable writing screenshots to disk. When disabled, images are *only* copied to the clipboard.
* **select screenshots folder**: Click this to open a folder picker and change where the timestamped `.png` files are saved.

⠀

by kriaiss.
