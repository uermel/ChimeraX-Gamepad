# vim: set expandtab shiftwidth=4 softtabstop=4:

"""Gamepad command implementations and registration."""


def gamepad(session):
    """Open the gamepad tool.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    from chimerax.core.commands import run

    run(session, "ui tool show Gamepad")


def gamepad_start(session):
    """Start gamepad control.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    tool = _get_or_create_tool(session)
    if tool and tool.gamepad_manager:
        tool.gamepad_manager.start()
        session.logger.info("Gamepad control started")


def gamepad_stop(session):
    """Stop gamepad control.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    if hasattr(session, "gamepad") and session.gamepad:
        session.gamepad.gamepad_manager.stop()
        session.logger.info("Gamepad control stopped")
    else:
        session.logger.warning("Gamepad tool not running")


def gamepad_mode(session, mode):
    """Set gamepad control mode.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    mode : str
        The mode to set ("view" or "model").
    """
    tool = _get_tool(session)
    if not tool:
        return

    from ..core.config import ControlMode

    if mode == "view":
        tool.gamepad_manager.mode = ControlMode.VIEW
        session.logger.info("Gamepad mode set to: view")
    elif mode == "model":
        tool.gamepad_manager.mode = ControlMode.MODEL
        session.logger.info("Gamepad mode set to: model")
    else:
        session.logger.warning(f"Unknown mode: {mode}")

    # Update UI if available
    if hasattr(tool, "_update_status"):
        tool._update_status()


def gamepad_sensitivity(session, target, value):
    """Set gamepad sensitivity.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    target : str
        The target to set ("view" or "model").
    value : float
        The sensitivity value (0.1 to 5.0).
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.gamepad_manager.config

    if target == "view":
        config.view_sensitivity = value
        session.logger.info(f"View sensitivity set to: {config.view_sensitivity}")
    elif target == "model":
        config.model_sensitivity = value
        session.logger.info(f"Model sensitivity set to: {config.model_sensitivity}")
    else:
        session.logger.warning(f"Unknown target: {target}")
        return

    config.save()


def gamepad_deadzone(session, value):
    """Set gamepad dead zone.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    value : float
        The dead zone value (0.0 to 0.5).
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.gamepad_manager.config
    config.dead_zone = value
    config.save()
    session.logger.info(f"Dead zone set to: {config.dead_zone}")


def gamepad_bind(session, button, command):
    """Bind a gamepad button to a ChimeraX command.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    button : str
        The button name (e.g., "A", "B", "X", "Y").
    command : str
        The ChimeraX command to execute.
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.gamepad_manager.config
    config.set_button_command(button.upper(), command)
    config.save()
    session.logger.info(f"Bound {button.upper()} to: {command}")


def gamepad_unbind(session, button):
    """Remove a gamepad button binding.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    button : str
        The button name to unbind.
    """
    tool = _get_tool(session)
    if not tool:
        return

    config = tool.gamepad_manager.config
    config.set_button_command(button.upper(), None)
    config.save()
    session.logger.info(f"Unbound {button.upper()}")


def gamepad_settings(session):
    """Open the gamepad settings dialog.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.
    """
    tool = _get_or_create_tool(session)
    if tool:
        tool._open_settings()


# Helper functions


def _get_tool(session):
    """Get the gamepad tool if it exists.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.

    Returns
    -------
    GamepadTool or None
        The gamepad tool instance, or None if not running.
    """
    if hasattr(session, "gamepad") and session.gamepad:
        return session.gamepad
    else:
        session.logger.warning("Gamepad tool not running. Use 'gamepad' to start it.")
        return None


def _get_or_create_tool(session):
    """Get or create the gamepad tool.

    Parameters
    ----------
    session : chimerax.core.session.Session
        The ChimeraX session.

    Returns
    -------
    GamepadTool
        The gamepad tool instance.
    """
    if hasattr(session, "gamepad") and session.gamepad:
        return session.gamepad

    # Start the tool
    from ..tool import GamepadTool

    return GamepadTool(session, "Gamepad")


# Command registration


def register_gamepad_commands(logger):
    """Register all gamepad commands with ChimeraX.

    Parameters
    ----------
    logger : chimerax.core.logger.Logger
        The ChimeraX logger.
    """
    from chimerax.core.commands import CmdDesc, EnumOf, FloatArg, StringArg, register

    # gamepad - open the tool
    register(
        "gamepad",
        CmdDesc(synopsis="Open the gamepad controller tool"),
        gamepad,
    )

    # gamepad start
    register(
        "gamepad start",
        CmdDesc(synopsis="Start gamepad control"),
        gamepad_start,
    )

    # gamepad stop
    register(
        "gamepad stop",
        CmdDesc(synopsis="Stop gamepad control"),
        gamepad_stop,
    )

    # gamepad mode <view|model>
    register(
        "gamepad mode",
        CmdDesc(
            required=[("mode", EnumOf(["view", "model"]))],
            synopsis="Set gamepad control mode (view or model)",
        ),
        gamepad_mode,
    )

    # gamepad sensitivity <view|model> <value>
    register(
        "gamepad sensitivity",
        CmdDesc(
            required=[("target", EnumOf(["view", "model"])), ("value", FloatArg)],
            synopsis="Set gamepad sensitivity (0.1 to 5.0)",
        ),
        gamepad_sensitivity,
    )

    # gamepad deadzone <value>
    register(
        "gamepad deadzone",
        CmdDesc(
            required=[("value", FloatArg)],
            synopsis="Set gamepad dead zone (0.0 to 0.5)",
        ),
        gamepad_deadzone,
    )

    # gamepad bind <button> <command>
    register(
        "gamepad bind",
        CmdDesc(
            required=[("button", StringArg), ("command", StringArg)],
            synopsis="Bind gamepad button to ChimeraX command",
        ),
        gamepad_bind,
    )

    # gamepad unbind <button>
    register(
        "gamepad unbind",
        CmdDesc(
            required=[("button", StringArg)],
            synopsis="Remove gamepad button binding",
        ),
        gamepad_unbind,
    )

    # gamepad settings
    register(
        "gamepad settings",
        CmdDesc(synopsis="Open gamepad settings dialog"),
        gamepad_settings,
    )
