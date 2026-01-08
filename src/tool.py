# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.tools import ToolInstance
from chimerax.ui import MainToolWindow
from Qt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GamepadTool(ToolInstance):
    """ChimeraX tool for gamepad controller support."""

    # Does this instance persist when session closes
    SESSION_ENDURING = False
    # We do save/restore in sessions
    SESSION_SAVE = True
    # Help page
    help = "help:user/tools/gamepad.html"

    def __init__(self, session, tool_name):
        """Initialize the Gamepad tool.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        tool_name : str
            The name of the tool.
        """
        super().__init__(session, tool_name)

        self.display_name = "Gamepad Controller"

        # Store self in session for access from commands
        session.gamepad = self

        # Create the gamepad manager
        from .core.gamepad import GamepadManager

        self.gamepad_manager = GamepadManager(session)
        self.gamepad_manager.on_status_change = self._update_status

        # Create tool window
        self.tool_window = MainToolWindow(self, close_destroys=True)
        self._build_ui()

        # Register for frame updates
        self._frame_handler = session.triggers.add_handler("new frame", self._on_frame)

        # Start the gamepad manager
        try:
            self.gamepad_manager.start()
            self._update_status()
        except Exception as e:
            session.logger.warning(f"Failed to initialize gamepad: {e}")

    def _build_ui(self):
        """Build the minimal status UI."""
        tw = self.tool_window

        layout = QVBoxLayout()

        # Status section
        status_layout = QHBoxLayout()
        self._status_label = QLabel("Status: Not connected")
        status_layout.addWidget(self._status_label)
        layout.addLayout(status_layout)

        # Mode section
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self._mode_label = QLabel("View")
        mode_layout.addWidget(self._mode_label)
        mode_layout.addStretch()

        self._toggle_mode_btn = QPushButton("Toggle Mode")
        self._toggle_mode_btn.clicked.connect(self._toggle_mode)
        mode_layout.addWidget(self._toggle_mode_btn)
        layout.addLayout(mode_layout)

        # Settings button
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        self._settings_btn = QPushButton("Settings...")
        self._settings_btn.clicked.connect(self._open_settings)
        settings_layout.addWidget(self._settings_btn)
        layout.addLayout(settings_layout)

        layout.addStretch()

        container = QWidget()
        container.setLayout(layout)
        tw.ui_area.setLayout(QVBoxLayout())
        tw.ui_area.layout().addWidget(container)
        tw.manage("right")

    def _on_frame(self, trigger_name, update_loop):
        """Called each frame to poll gamepad and apply actions.

        Parameters
        ----------
        trigger_name : str
            The name of the trigger.
        update_loop : object
            The update loop object.
        """
        if self.gamepad_manager:
            self.gamepad_manager.update()

    def _update_status(self):
        """Update the status label with controller info."""
        if not self.gamepad_manager:
            self._status_label.setText("Status: Not initialized")
            return

        num_controllers = len(self.gamepad_manager.controllers)
        if num_controllers == 0:
            self._status_label.setText("Status: No controller connected")
        elif num_controllers == 1:
            controller = list(self.gamepad_manager.controllers.values())[0]
            self._status_label.setText(f"Status: {controller.name}")
        else:
            self._status_label.setText(f"Status: {num_controllers} controllers connected")

        # Update mode label
        from .core.gamepad import ControlMode

        if self.gamepad_manager.mode == ControlMode.VIEW:
            self._mode_label.setText("View")
        else:
            self._mode_label.setText("Model")

    def _toggle_mode(self):
        """Toggle between view and model control modes."""
        if self.gamepad_manager:
            self.gamepad_manager.toggle_mode()
            self._update_status()

    def _open_settings(self):
        """Open the settings dialog."""
        from .ui.settings import SettingsDialog

        dialog = SettingsDialog(self.session, self.gamepad_manager.config, self.tool_window.ui_area)
        if dialog.exec():
            self.session.logger.info("Gamepad settings saved")

    def delete(self):
        """Cleanup when tool is closed."""
        # Remove frame handler
        if hasattr(self, "_frame_handler") and self._frame_handler:
            self.session.triggers.remove_handler(self._frame_handler)
            self._frame_handler = None

        # Stop gamepad manager
        if hasattr(self, "gamepad_manager") and self.gamepad_manager:
            self.gamepad_manager.stop()
            self.gamepad_manager = None

        # Remove from session
        if hasattr(self.session, "gamepad"):
            del self.session.gamepad

        super().delete()

    def take_snapshot(self, session, flags):
        """Save session state.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        flags : int
            Snapshot flags.

        Returns
        -------
        dict
            The session state.
        """
        return {
            "version": 1,
            "config": self.gamepad_manager.config.to_dict() if self.gamepad_manager else {},
        }

    @classmethod
    def restore_snapshot(cls, session, data):
        """Restore from session.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        data : dict
            The saved session state.

        Returns
        -------
        GamepadTool
            The restored tool instance.
        """
        inst = cls(session, "Gamepad")
        if inst.gamepad_manager and "config" in data:
            inst.gamepad_manager.config.from_dict(data["config"])
        return inst
