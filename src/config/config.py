import tomllib
import toml
from pathlib import Path
from logging import getLogger


logger = getLogger(__name__)

def load_config():
    """
    Loads the config file from '~/.config/screen-short/config.toml'.
    If the file is missing, corrupt, or incomplete, it loads and fills
    in default values.

    Returns:
        dict: A dictionary containing the fully validated configuration.
    """
    # Note: I've corrected the spelling of "appearance" for best practice.
    # You should update this in your config.toml file as well.
    default_conf = {
        "paths": {
            "ask_before_save": False,
            "save_dir": "~/Pictures/Screenshots"
        },
        "appearance": {
            "selection_border_width": 2,
            "selection_border_color": "#1E90FF",
            "tooltip_bg_color": "#282828",
            "tooltip_font_color": "#EBDBB2",
            "initial_selection": "fullscreen"
        },
        "behavior": {
            "copy_to_clipboard": True,
            "open_after_save": False
        },
        "editing": {
            "shape_border_color": "#1E90FF",
            "shape_border_width": 2,
            "shape_rect": True,
            "shape_arrow": True,
            "shape_circle": True,

        }
    }

    config_path = Path.home() / ".config/screen-short/config.toml"
    logger.info(f"Loading config file from: {config_path}")

    user_conf = {}
    try:
        with open(config_path, "rb") as f:
            user_conf = tomllib.load(f)
    except FileNotFoundError:
        logger.warning("Config file not found. Creating a default one and continuing.")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            toml.dump(default_conf, f)
        return default_conf
    except tomllib.TOMLDecodeError as e:
        logger.error(f"Config file is corrupted or invalid: {e}")
        logger.warning("Loading default configurations!")
        return default_conf

    final_conf = default_conf.copy()

    for section, fields in default_conf.items():
        if section in user_conf:
            for field, default_value in fields.items():
                if field in user_conf[section]:
                    final_conf[section][field] = user_conf[section][field]
                else:
                    logger.warning(f"Field '{field}' not found in section '[{section}]'. Using default value.")
    
    for section, fields in user_conf.items():
        if section not in final_conf:
            logger.error(f"Unknown section '[{section}]' in config file will be ignored.")
        else:
            for field in fields:
                if field not in final_conf[section]:
                    logger.error(f"Unknown field '{field}' in section '[{section}]' will be ignored.")

    return final_conf