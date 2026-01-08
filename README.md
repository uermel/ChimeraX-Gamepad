# ChimeraX-Gamepad

A ChimeraX plugin that enables gamepad/controller input for manipulating the 3D view and models. Useful
in combination with spatial reality displays or while recording movies.

## Features

- **Cross-platform gamepad support** via SDL2 (Xbox, PlayStation, generic USB controllers)
- **View manipulation**: Pan, rotate, and zoom the camera using analog sticks and triggers
- **Model manipulation**: Translate and rotate selected models
- **Custom button bindings**: Map any gamepad button to ChimeraX commands
- **Configurable sensitivity** and dead zones

## Requirements

- ChimeraX 1.9 or later
- SDL2 library (see installation instructions below)
- A compatible gamepad/controller

## Installation

### 1. Install SDL2

**macOS (Homebrew):**
```bash
brew install sdl2
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install libsdl2-2.0-0
```

**Windows:**
The `pysdl2-dll` package is automatically installed as a dependency.

### 2. Install the Plugin

**From source (development):**
```bash
cd /path/to/chimerax-gamepad
.launch/prelaunch.sh .
```

Or manually in ChimeraX:
```
devel build /path/to/chimerax-gamepad
devel install /path/to/chimerax-gamepad
```

## Usage

### Starting the Gamepad Tool

In ChimeraX, run:
```
gamepad
```

This opens the Gamepad tool panel and begins listening for controller input.

### Control Mapping

| Input | View Mode | Model Mode |
|-------|-----------|------------|
| Left Stick | Pan XY | Translate XY |
| Right Stick | Rotate | Rotate |
| Left Trigger | Zoom out | Translate -Z |
| Right Trigger | Zoom in | Translate +Z |
| Start Button | Toggle mode | Toggle mode |

### Commands

| Command | Description |
|---------|-------------|
| `gamepad` | Open the gamepad tool |
| `gamepad start` | Start gamepad polling |
| `gamepad stop` | Stop gamepad polling |
| `gamepad mode view` | Switch to view control mode |
| `gamepad mode model` | Switch to model control mode |
| `gamepad sensitivity view <value>` | Set view sensitivity (0.1-5.0) |
| `gamepad sensitivity model <value>` | Set model sensitivity (0.1-5.0) |
| `gamepad deadzone <value>` | Set dead zone (0.0-0.5) |
| `gamepad bind <button> <command>` | Bind button to ChimeraX command |
| `gamepad unbind <button>` | Remove button binding |
| `gamepad settings` | Open settings dialog |

### Button Names for Binding

- `A`, `B`, `X`, `Y`
- `LEFTSHOULDER`, `RIGHTSHOULDER`
- `LEFTSTICK`, `RIGHTSTICK`
- `BACK`, `START`, `GUIDE`
- `DPAD_UP`, `DPAD_DOWN`, `DPAD_LEFT`, `DPAD_RIGHT`

### Example: Bind Buttons to Commands

```
gamepad bind A "select clear"
gamepad bind B "view initial"
gamepad bind X "surface"
gamepad bind Y "hide surfaces"
```

## Configuration

Settings are stored in `~/.chimerax/gamepad/config.json` and include:

- **Dead zone**: Percentage of stick movement to ignore (default: 15%)
- **View sensitivity**: Speed multiplier for view manipulation (default: 1.0)
- **Model sensitivity**: Speed multiplier for model manipulation (default: 1.0)
- **Invert Y axis**: Flip vertical stick direction
- **Button mappings**: Custom button-to-command mappings

Use `gamepad settings` to open the configuration dialog.

## Troubleshooting

### Controller not detected

1. Ensure the controller is connected before starting ChimeraX
2. Check that SDL2 is properly installed
3. Try disconnecting and reconnecting the controller

### Movements are too fast/slow

Adjust sensitivity using:
```
gamepad sensitivity view 0.5   # Slower
gamepad sensitivity view 2.0   # Faster
```

### Stick drift

Increase the dead zone:
```
gamepad deadzone 0.2   # 20% dead zone
```

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/uermel/chimerax-gamepad.git
cd chimerax-gamepad

# Build and install
.launch/prelaunch.sh .
```

## License

MIT License
