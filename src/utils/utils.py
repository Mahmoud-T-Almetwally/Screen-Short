import re
import json
import subprocess
from logging import getLogger


logger = getLogger(__name__)


def get_active_monitor_name():
    """
    Gets the name of the monitor with the active window using hyprctl.
    """
    try:
        result = subprocess.run(
            ['hyprctl', 'activeworkspace', '-j'], 
            capture_output=True, text=True, check=True
        )
        active_window_info = json.loads(result.stdout)
        return active_window_info.get('monitor')
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not determine active monitor: {e}. Falling back.")
        # Fallback strategy: You could try parsing `hyprctl monitors -j` and finding
        # the one marked 'focused', or just default to the first one.
        return None


def get_monitor_data():
    """
    Retrieves monitor data from hyprctl in JSON format and parses it.
    Returns a dictionary mapping monitor names to their geometry.
    """
    try:
        result = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True, check=True)
        monitors_raw = json.loads(result.stdout)
        
        monitors = {}
        for monitor in monitors_raw:
            name = monitor['name']
            width = monitor['width']
            height = monitor['height']
            x = monitor['x']
            y = monitor['y']
            monitors[name] = (x, y, width, height)
            
        return monitors
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to get monitor data: {e}")
        return None


def parse_slurp_output(stdout: str) -> tuple[int, int, int, int]:
    """Parses slurp geometry stdout and returns a Tuple with four integers: (x, y, h, w)

    Args:
        stdout (str): slurp's string stdout

    Returns:
        tuple[int, int, int, int]: a tuple containing geometery coordinates (x, y, w, h)
    """

    pattern = re.compile(r"(\d+),(\d+)\s(\d+)x(\d+)")

    match = pattern.findall(stdout)[0]

    result = [0, 0, 0, 0]

    for idx, coordinate in enumerate(match):
        try:
            result[idx] = int(coordinate)
        except (ValueError, TypeError) as e:
            logger.error(f"Couldn't Parse slurp's stdout, Aborting with return (0, 0, 0, 0). Original Error: {e}")
            return (0, 0, 0, 0)

    return tuple(result)