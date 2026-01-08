# vim: set expandtab shiftwidth=4 softtabstop=4:

from sdl2 import (
    SDL_CONTROLLER_AXIS_LEFTX,
    SDL_CONTROLLER_AXIS_LEFTY,
    SDL_CONTROLLER_AXIS_RIGHTX,
    SDL_CONTROLLER_AXIS_RIGHTY,
    SDL_CONTROLLER_AXIS_TRIGGERLEFT,
    SDL_CONTROLLER_AXIS_TRIGGERRIGHT,
    SDL_GameControllerClose,
    SDL_GameControllerGetAxis,
    SDL_GameControllerGetButton,
    SDL_GameControllerName,
)


class Controller:
    """Represents a single game controller and handles input reading."""

    # Axis value range from SDL2
    AXIS_MIN = -32768
    AXIS_MAX = 32767

    def __init__(self, sdl_controller, instance_id, config):
        """Initialize the controller.

        Parameters
        ----------
        sdl_controller : SDL_GameController
            The SDL game controller handle.
        instance_id : int
            The SDL joystick instance ID.
        config : GamepadConfig
            The gamepad configuration.
        """
        self.sdl_controller = sdl_controller
        self.instance_id = instance_id
        self.config = config

        # Get controller name for identification
        name = SDL_GameControllerName(sdl_controller)
        self.name = name.decode("utf-8") if name else "Unknown Controller"

    def close(self):
        """Close the SDL controller."""
        if self.sdl_controller:
            SDL_GameControllerClose(self.sdl_controller)
            self.sdl_controller = None

    def get_left_stick(self):
        """Get left analog stick values normalized to -1.0 to 1.0.

        Returns
        -------
        tuple
            (x, y) values from -1.0 to 1.0 with dead zone applied.
        """
        x = SDL_GameControllerGetAxis(self.sdl_controller, SDL_CONTROLLER_AXIS_LEFTX)
        y = SDL_GameControllerGetAxis(self.sdl_controller, SDL_CONTROLLER_AXIS_LEFTY)

        # Apply Y inversion if configured
        if self.config.invert_y:
            y = -y

        return self._normalize_axis(x), self._normalize_axis(y)

    def get_right_stick(self):
        """Get right analog stick values normalized to -1.0 to 1.0.

        Returns
        -------
        tuple
            (x, y) values from -1.0 to 1.0 with dead zone applied.
        """
        x = SDL_GameControllerGetAxis(self.sdl_controller, SDL_CONTROLLER_AXIS_RIGHTX)
        y = SDL_GameControllerGetAxis(self.sdl_controller, SDL_CONTROLLER_AXIS_RIGHTY)

        # Apply Y inversion if configured
        if self.config.invert_y:
            y = -y

        return self._normalize_axis(x), self._normalize_axis(y)

    def get_left_trigger(self):
        """Get left trigger value normalized to 0.0 to 1.0.

        Returns
        -------
        float
            Trigger value from 0.0 to 1.0.
        """
        value = SDL_GameControllerGetAxis(self.sdl_controller, SDL_CONTROLLER_AXIS_TRIGGERLEFT)
        return max(0, value) / self.AXIS_MAX

    def get_right_trigger(self):
        """Get right trigger value normalized to 0.0 to 1.0.

        Returns
        -------
        float
            Trigger value from 0.0 to 1.0.
        """
        value = SDL_GameControllerGetAxis(self.sdl_controller, SDL_CONTROLLER_AXIS_TRIGGERRIGHT)
        return max(0, value) / self.AXIS_MAX

    def get_button(self, button):
        """Check if a button is pressed.

        Parameters
        ----------
        button : int
            The SDL button constant.

        Returns
        -------
        bool
            True if the button is pressed.
        """
        return SDL_GameControllerGetButton(self.sdl_controller, button) == 1

    def _normalize_axis(self, value):
        """Normalize axis value to -1.0 to 1.0 with dead zone.

        Parameters
        ----------
        value : int
            The raw SDL axis value (-32768 to 32767).

        Returns
        -------
        float
            Normalized value from -1.0 to 1.0 with dead zone applied.
        """
        dead_zone = self.config.dead_zone

        # Normalize to -1.0 to 1.0
        normalized = value / self.AXIS_MAX

        # Apply dead zone
        if abs(normalized) < dead_zone:
            return 0.0

        # Scale remaining range to 0-1 after dead zone
        sign = 1 if normalized > 0 else -1
        return sign * (abs(normalized) - dead_zone) / (1.0 - dead_zone)
