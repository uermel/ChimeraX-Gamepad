# vim: set expandtab shiftwidth=4 softtabstop=4:

import json
import os
from enum import IntEnum


class ControlMode(IntEnum):
    """Control mode enum."""

    VIEW = 1
    MODEL = 2


class GamepadConfig:
    """Manages gamepad configuration settings."""

    DEFAULT_CONFIG = {
        "dead_zone": 0.15,  # 15% dead zone
        "translation_sensitivity": 1.0,  # For pan (view) and translate (model)
        "rotation_sensitivity": 1.0,  # For rotate in both modes
        "zoom_sensitivity": 1.0,  # For zoom (view) and Z-translate (model)
        "invert_y": False,
        "button_mappings": {
            # Default button mappings: button_name -> ChimeraX command
            # "A": "select clear",
            # "B": "view initial",
        },
    }

    # SDL button name mapping
    BUTTON_NAMES = {
        0: "A",
        1: "B",
        2: "X",
        3: "Y",
        4: "BACK",
        5: "GUIDE",
        6: "START",
        7: "LEFTSTICK",
        8: "RIGHTSTICK",
        9: "LEFTSHOULDER",
        10: "RIGHTSHOULDER",
        11: "DPAD_UP",
        12: "DPAD_DOWN",
        13: "DPAD_LEFT",
        14: "DPAD_RIGHT",
    }

    def __init__(self):
        """Initialize the configuration."""
        self._config = dict(self.DEFAULT_CONFIG)
        self._config["button_mappings"] = dict(self.DEFAULT_CONFIG["button_mappings"])
        self._config_path = self._get_config_path()
        self.load()

    def _get_config_path(self):
        """Get path to config file in user's ChimeraX config dir.

        Returns
        -------
        str
            The path to the config file.
        """
        config_dir = os.path.expanduser("~/.chimerax/gamepad")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    def load(self):
        """Load configuration from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path) as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
            except (json.JSONDecodeError, OSError):
                pass  # Use defaults on error

    def save(self):
        """Save configuration to file."""
        try:
            with open(self._config_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except OSError:
            pass  # Silently fail if can't save

    @property
    def dead_zone(self):
        """Get the dead zone value.

        Returns
        -------
        float
            The dead zone (0.0 to 0.5).
        """
        return self._config["dead_zone"]

    @dead_zone.setter
    def dead_zone(self, value):
        """Set the dead zone value.

        Parameters
        ----------
        value : float
            The dead zone value (clamped to 0.0-0.5).
        """
        self._config["dead_zone"] = max(0.0, min(0.5, value))

    @property
    def translation_sensitivity(self):
        """Get the translation sensitivity.

        Returns
        -------
        float
            The translation sensitivity (0.1 to 5.0).
        """
        return self._config.get("translation_sensitivity", 1.0)

    @translation_sensitivity.setter
    def translation_sensitivity(self, value):
        """Set the translation sensitivity.

        Parameters
        ----------
        value : float
            The sensitivity value (clamped to 0.1-5.0).
        """
        self._config["translation_sensitivity"] = max(0.1, min(5.0, value))

    @property
    def rotation_sensitivity(self):
        """Get the rotation sensitivity.

        Returns
        -------
        float
            The rotation sensitivity (0.1 to 5.0).
        """
        return self._config.get("rotation_sensitivity", 1.0)

    @rotation_sensitivity.setter
    def rotation_sensitivity(self, value):
        """Set the rotation sensitivity.

        Parameters
        ----------
        value : float
            The sensitivity value (clamped to 0.1-5.0).
        """
        self._config["rotation_sensitivity"] = max(0.1, min(5.0, value))

    @property
    def zoom_sensitivity(self):
        """Get the zoom sensitivity.

        Returns
        -------
        float
            The zoom sensitivity (0.1 to 5.0).
        """
        return self._config.get("zoom_sensitivity", 1.0)

    @zoom_sensitivity.setter
    def zoom_sensitivity(self, value):
        """Set the zoom sensitivity.

        Parameters
        ----------
        value : float
            The sensitivity value (clamped to 0.1-5.0).
        """
        self._config["zoom_sensitivity"] = max(0.1, min(5.0, value))

    @property
    def invert_y(self):
        """Get whether Y axis is inverted.

        Returns
        -------
        bool
            True if Y axis is inverted.
        """
        return self._config["invert_y"]

    @invert_y.setter
    def invert_y(self, value):
        """Set whether Y axis is inverted.

        Parameters
        ----------
        value : bool
            True to invert Y axis.
        """
        self._config["invert_y"] = bool(value)

    def button_to_name(self, button):
        """Convert SDL button constant to string name.

        Parameters
        ----------
        button : int
            The SDL button constant.

        Returns
        -------
        str
            The button name.
        """
        return self.BUTTON_NAMES.get(button, f"BUTTON_{button}")

    def get_button_command(self, button):
        """Get command mapped to button, or None.

        Parameters
        ----------
        button : int
            The SDL button constant.

        Returns
        -------
        str or None
            The ChimeraX command mapped to the button.
        """
        button_name = self.button_to_name(button)
        return self._config["button_mappings"].get(button_name)

    def set_button_command(self, button_name, command):
        """Map a button to a ChimeraX command.

        Parameters
        ----------
        button_name : str
            The button name (e.g., "A", "B", "X", "Y").
        command : str or None
            The ChimeraX command to execute, or None to remove mapping.
        """
        if command:
            self._config["button_mappings"][button_name] = command
        elif button_name in self._config["button_mappings"]:
            del self._config["button_mappings"][button_name]

    def to_dict(self):
        """Export config for session saving.

        Returns
        -------
        dict
            The configuration dictionary.
        """
        return dict(self._config)

    def from_dict(self, data):
        """Import config from session restore.

        Parameters
        ----------
        data : dict
            The configuration dictionary.
        """
        self._config.update(data)
