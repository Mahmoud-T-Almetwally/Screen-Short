from config.config import load_config
from utils.utils import get_active_monitor_name
from ui.overlay import ScreenshotOverlay
from logging import getLogger
import subprocess
import sys

from PySide6.QtWidgets import QApplication


logger = getLogger(__name__)


if __name__ == "__main__":
    conf = load_config()
    
    active_monitor = get_active_monitor_name()
    if not active_monitor:
        logger.error("Failed to identify an active monitor. Exiting.")
        sys.exit(1)
    
    logger.info(f"Capturing active monitor: {active_monitor}")

    try:
        capture_command = ['grim', '-o', active_monitor, '-']
        result = subprocess.run(capture_command, capture_output=True, check=True)
        fullscreen_capture_data = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Failed to run grim: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    all_screens = app.screens()
    target_screen = None
    for screen in all_screens:
        if screen.name() == active_monitor:
            target_screen = screen
            break

    if not target_screen:
        logger.warning(f"Could not find a screen named '{active_monitor}'. Defaulting to primary screen.")
        target_screen = app.primaryScreen()

    overlay = ScreenshotOverlay(fullscreen_capture_data, conf) 
    overlay.setScreen(target_screen)
    overlay.setGeometry(target_screen.geometry())
    overlay.showFullScreen()
    sys.exit(app.exec())