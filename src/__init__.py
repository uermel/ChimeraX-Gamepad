# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.toolshed import BundleAPI


class _GamepadAPI(BundleAPI):
    """ChimeraX bundle API for the Gamepad plugin."""

    api_version = 1

    @staticmethod
    def start_tool(session, bi, ti):
        """Start the Gamepad tool."""
        if ti.name == "Gamepad":
            from .tool import GamepadTool

            return GamepadTool(session, ti.name)

    @staticmethod
    def register_command(bi, ci, logger):
        """Register gamepad commands."""
        if "gamepad" in ci.name:
            from .cmd.cmd import register_gamepad_commands

            register_gamepad_commands(logger)


# Create the ``bundle_api`` object that ChimeraX expects.
bundle_api = _GamepadAPI()
