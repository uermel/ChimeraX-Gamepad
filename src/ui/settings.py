# vim: set expandtab shiftwidth=4 softtabstop=4:

"""Settings dialog for gamepad configuration."""

from Qt.QtCore import Qt
from Qt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """Configuration dialog for gamepad settings."""

    def __init__(self, session, config, parent=None):
        """Initialize the settings dialog.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        config : GamepadConfig
            The gamepad configuration.
        parent : QWidget, optional
            The parent widget.
        """
        super().__init__(parent)
        self.session = session
        self.config = config

        self.setWindowTitle("Gamepad Settings")
        self.setMinimumWidth(450)

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Sensitivity Group
        sensitivity_group = QGroupBox("Sensitivity")
        sens_layout = QFormLayout()

        # Dead zone slider
        self.dead_zone_slider = QSlider(Qt.Horizontal)
        self.dead_zone_slider.setRange(0, 50)  # 0-50%
        self.dead_zone_slider.valueChanged.connect(self._on_dead_zone_changed)
        self.dead_zone_label = QLabel("15%")
        self.dead_zone_label.setMinimumWidth(40)
        dz_layout = QHBoxLayout()
        dz_layout.addWidget(self.dead_zone_slider)
        dz_layout.addWidget(self.dead_zone_label)
        sens_layout.addRow("Dead Zone:", dz_layout)

        # View sensitivity
        self.view_sens_slider = QSlider(Qt.Horizontal)
        self.view_sens_slider.setRange(10, 500)  # 0.1-5.0
        self.view_sens_slider.valueChanged.connect(self._on_view_sens_changed)
        self.view_sens_label = QLabel("1.0")
        self.view_sens_label.setMinimumWidth(40)
        vs_layout = QHBoxLayout()
        vs_layout.addWidget(self.view_sens_slider)
        vs_layout.addWidget(self.view_sens_label)
        sens_layout.addRow("View Sensitivity:", vs_layout)

        # Model sensitivity
        self.model_sens_slider = QSlider(Qt.Horizontal)
        self.model_sens_slider.setRange(10, 500)
        self.model_sens_slider.valueChanged.connect(self._on_model_sens_changed)
        self.model_sens_label = QLabel("1.0")
        self.model_sens_label.setMinimumWidth(40)
        ms_layout = QHBoxLayout()
        ms_layout.addWidget(self.model_sens_slider)
        ms_layout.addWidget(self.model_sens_label)
        sens_layout.addRow("Model Sensitivity:", ms_layout)

        # Invert Y axis
        self.invert_y_check = QCheckBox("Invert Y Axis")
        sens_layout.addRow("", self.invert_y_check)

        sensitivity_group.setLayout(sens_layout)
        layout.addWidget(sensitivity_group)

        # Button Mappings Group
        mapping_group = QGroupBox("Button Mappings")
        mapping_layout = QVBoxLayout()

        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Button", "Command"])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.setMinimumHeight(150)
        mapping_layout.addWidget(self.mapping_table)

        # Add/Remove buttons
        btn_layout = QHBoxLayout()
        self.add_mapping_btn = QPushButton("Add Mapping")
        self.add_mapping_btn.clicked.connect(self._add_mapping)
        self.remove_mapping_btn = QPushButton("Remove")
        self.remove_mapping_btn.clicked.connect(self._remove_mapping)
        btn_layout.addWidget(self.add_mapping_btn)
        btn_layout.addWidget(self.remove_mapping_btn)
        btn_layout.addStretch()
        mapping_layout.addLayout(btn_layout)

        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        apply_btn = buttons.button(QDialogButtonBox.Apply)
        if apply_btn:
            apply_btn.clicked.connect(self._apply)
        layout.addWidget(buttons)

    def _load_values(self):
        """Load current config values into UI."""
        self.dead_zone_slider.setValue(int(self.config.dead_zone * 100))
        self.view_sens_slider.setValue(int(self.config.view_sensitivity * 100))
        self.model_sens_slider.setValue(int(self.config.model_sensitivity * 100))
        self.invert_y_check.setChecked(self.config.invert_y)

        # Load button mappings
        self._refresh_mappings_table()

    def _refresh_mappings_table(self):
        """Refresh the button mappings table."""
        mappings = self.config._config.get("button_mappings", {})
        self.mapping_table.setRowCount(len(mappings))
        for row, (button, command) in enumerate(mappings.items()):
            self.mapping_table.setItem(row, 0, QTableWidgetItem(button))
            self.mapping_table.setItem(row, 1, QTableWidgetItem(command))

    def _on_dead_zone_changed(self, value):
        """Handle dead zone slider change."""
        self.dead_zone_label.setText(f"{value}%")

    def _on_view_sens_changed(self, value):
        """Handle view sensitivity slider change."""
        self.view_sens_label.setText(f"{value / 100:.1f}")

    def _on_model_sens_changed(self, value):
        """Handle model sensitivity slider change."""
        self.model_sens_label.setText(f"{value / 100:.1f}")

    def _add_mapping(self):
        """Add a new button mapping row."""
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)

        # Button selector combo
        button_combo = QComboBox()
        button_combo.addItems(
            [
                "A",
                "B",
                "X",
                "Y",
                "LEFTSHOULDER",
                "RIGHTSHOULDER",
                "BACK",
                "GUIDE",
                "LEFTSTICK",
                "RIGHTSTICK",
                "DPAD_UP",
                "DPAD_DOWN",
                "DPAD_LEFT",
                "DPAD_RIGHT",
            ],
        )
        self.mapping_table.setCellWidget(row, 0, button_combo)

        # Command input
        command_edit = QLineEdit()
        command_edit.setPlaceholderText("ChimeraX command...")
        self.mapping_table.setCellWidget(row, 1, command_edit)

    def _remove_mapping(self):
        """Remove selected mapping row."""
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)

    def _apply(self):
        """Apply current settings to config."""
        self.config.dead_zone = self.dead_zone_slider.value() / 100
        self.config.view_sensitivity = self.view_sens_slider.value() / 100
        self.config.model_sensitivity = self.model_sens_slider.value() / 100
        self.config.invert_y = self.invert_y_check.isChecked()

        # Update button mappings
        self.config._config["button_mappings"].clear()
        for row in range(self.mapping_table.rowCount()):
            # Get button name
            button_widget = self.mapping_table.cellWidget(row, 0)
            if button_widget and isinstance(button_widget, QComboBox):
                button = button_widget.currentText()
            else:
                item = self.mapping_table.item(row, 0)
                button = item.text() if item else None

            # Get command
            cmd_widget = self.mapping_table.cellWidget(row, 1)
            if cmd_widget and isinstance(cmd_widget, QLineEdit):
                command = cmd_widget.text()
            else:
                cmd_item = self.mapping_table.item(row, 1)
                command = cmd_item.text() if cmd_item else ""

            if button and command:
                self.config._config["button_mappings"][button] = command

        self.config.save()

    def _save_and_close(self):
        """Apply settings and close dialog."""
        self._apply()
        self.accept()
