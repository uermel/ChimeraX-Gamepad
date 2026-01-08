# vim: set expandtab shiftwidth=4 softtabstop=4:

import ctypes

from sdl2 import (
    SDL_CONTROLLER_BUTTON_START,
    SDL_CONTROLLERBUTTONDOWN,
    SDL_CONTROLLERDEVICEADDED,
    SDL_CONTROLLERDEVICEREMOVED,
    SDL_INIT_GAMECONTROLLER,
    SDL_Event,
    SDL_GameControllerGetJoystick,
    SDL_GameControllerOpen,
    SDL_GetError,
    SDL_Init,
    SDL_IsGameController,
    SDL_JoystickInstanceID,
    SDL_NumJoysticks,
    SDL_PollEvent,
    SDL_Quit,
)

from .config import ControlMode, GamepadConfig
from .controller import Controller


class GamepadManager:
    """Manages SDL2 initialization and gamepad polling."""

    def __init__(self, session):
        """Initialize the gamepad manager.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        """
        self.session = session
        self.controllers = {}  # instance_id -> Controller
        self.config = GamepadConfig()
        self._running = False
        self._sdl_initialized = False

        # Current control mode
        self.mode = ControlMode.VIEW

        # Action handlers (lazy import to avoid circular imports)
        self._view_action = None
        self._model_action = None

        # Callback for status changes (controller connect/disconnect)
        self.on_status_change = None

    @property
    def view_action(self):
        """Get the view action handler (lazy initialization).

        Returns
        -------
        ViewAction
            The view action handler.
        """
        if self._view_action is None:
            from .actions import ViewAction

            self._view_action = ViewAction(self.session, self.config)
        return self._view_action

    @property
    def model_action(self):
        """Get the model action handler (lazy initialization).

        Returns
        -------
        ModelAction
            The model action handler.
        """
        if self._model_action is None:
            from .actions import ModelAction

            self._model_action = ModelAction(self.session, self.config)
        return self._model_action

    def start(self):
        """Initialize SDL2 and open connected controllers."""
        if self._sdl_initialized:
            return

        # Initialize SDL2 with game controller support
        if SDL_Init(SDL_INIT_GAMECONTROLLER) < 0:
            error = SDL_GetError()
            error_str = error.decode("utf-8") if error else "Unknown error"
            raise RuntimeError(f"SDL2 initialization failed: {error_str}")

        self._sdl_initialized = True
        self._running = True

        # Enumerate connected controllers
        self._discover_controllers()

        self.session.logger.info(f"Gamepad: SDL2 initialized, found {len(self.controllers)} controller(s)")

    def stop(self):
        """Cleanup SDL2 resources."""
        self._running = False

        # Close all controllers
        for controller in self.controllers.values():
            controller.close()
        self.controllers.clear()

        # Quit SDL2
        if self._sdl_initialized:
            SDL_Quit()
            self._sdl_initialized = False

        self.session.logger.info("Gamepad: SDL2 shutdown complete")

    def _discover_controllers(self):
        """Find and open all connected game controllers."""
        num_joysticks = SDL_NumJoysticks()
        for i in range(num_joysticks):
            if SDL_IsGameController(i):
                self._open_controller(i)

    def _open_controller(self, device_index):
        """Open a game controller at the given index.

        Parameters
        ----------
        device_index : int
            The SDL joystick device index.
        """
        gc = SDL_GameControllerOpen(device_index)
        if gc:
            joystick = SDL_GameControllerGetJoystick(gc)
            instance_id = SDL_JoystickInstanceID(joystick)
            controller = Controller(gc, instance_id, self.config)
            self.controllers[instance_id] = controller
            self.session.logger.info(f"Gamepad: Connected - {controller.name}")
            self._notify_status_change()

    def _close_controller(self, instance_id):
        """Close a game controller.

        Parameters
        ----------
        instance_id : int
            The SDL joystick instance ID.
        """
        if instance_id in self.controllers:
            controller = self.controllers[instance_id]
            self.session.logger.info(f"Gamepad: Disconnected - {controller.name}")
            controller.close()
            del self.controllers[instance_id]
            self._notify_status_change()

    def update(self):
        """Poll SDL events and process controller input."""
        if not self._running:
            return

        # Process SDL events (controller connect/disconnect, button presses)
        event = SDL_Event()
        while SDL_PollEvent(ctypes.byref(event)):
            self._handle_event(event)

        # Process analog input from all controllers
        for controller in self.controllers.values():
            self._process_controller(controller)

    def _handle_event(self, event):
        """Handle SDL events for controller connect/disconnect and buttons.

        Parameters
        ----------
        event : SDL_Event
            The SDL event.
        """
        if event.type == SDL_CONTROLLERDEVICEADDED:
            self._open_controller(event.cdevice.which)
        elif event.type == SDL_CONTROLLERDEVICEREMOVED:
            self._close_controller(event.cdevice.which)
        elif event.type == SDL_CONTROLLERBUTTONDOWN:
            self._handle_button_press(event.cbutton)

    def _handle_button_press(self, button_event):
        """Handle button presses for mode toggle and custom commands.

        Parameters
        ----------
        button_event : SDL_ControllerButtonEvent
            The button event.
        """
        button = button_event.button

        # Check for mode toggle (Start button)
        if button == SDL_CONTROLLER_BUTTON_START:
            self.toggle_mode()
            return

        # Check for custom command mappings
        command = self.config.get_button_command(button)
        if command:
            from chimerax.core.commands import run

            try:
                run(self.session, command)
            except Exception as e:
                self.session.logger.warning(f"Gamepad: Command failed - {e}")

    def toggle_mode(self):
        """Toggle between VIEW and MODEL control modes."""
        if self.mode == ControlMode.VIEW:
            self.mode = ControlMode.MODEL
            self.session.logger.info("Gamepad: Mode set to MODEL")
        else:
            self.mode = ControlMode.VIEW
            self.session.logger.info("Gamepad: Mode set to VIEW")

    def _process_controller(self, controller):
        """Process analog stick input and apply to view/model.

        Parameters
        ----------
        controller : Controller
            The controller to process.
        """
        # Read stick values with dead zone applied
        left_x, left_y = controller.get_left_stick()
        right_x, right_y = controller.get_right_stick()
        left_trigger = controller.get_left_trigger()
        right_trigger = controller.get_right_trigger()

        # Calculate zoom from triggers (right - left gives -1 to 1 range)
        zoom = right_trigger - left_trigger

        if self.mode == ControlMode.VIEW:
            self.view_action.apply(
                pan_x=left_x,
                pan_y=left_y,
                rotate_x=right_x,
                rotate_y=right_y,
                zoom=zoom,
            )
        else:  # MODEL mode
            self.model_action.apply(
                translate_x=left_x,
                translate_y=left_y,
                rotate_x=right_x,
                rotate_y=right_y,
                translate_z=zoom,
            )

    def _notify_status_change(self):
        """Notify listener of controller status change."""
        if self.on_status_change is not None:
            import contextlib

            with contextlib.suppress(Exception):
                self.on_status_change()
