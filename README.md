# Focus Area for Windows

**Focus Area** helps you concentrate on your current task by instantly dimming or darkening the surrounding screen areas, leaving only your important work visible. Focus_Area works system-wide and can help you write documents, watch videos, read articles, or work with any application without distractions.

Use Focus_Area to eliminate visual clutter from sidebars, advertisements, notifications, and background windows. With Focus_Area you no longer need to close applications, resize windows, or struggle with distracting screen elements competing for your attention.

Focus Area is intuitive: creating transparent focus areas is as simple as clicking and dragging rectangles on your screen. Add multiple focus areas wherever you need them. Easily move focus areas by dragging the violet handle, resize by dragging edges or corners, and save your configurations for reuse. Pause with Ctrl+Shift+X or double-click, adjust opacity with the mouse wheel, and hold Shift to peek through the veil temporarily.

[Download Latest Release (v1.0.0)](https://github.com/Gabrieliam42/Focus_Area/releases/tag/1.0.0)

## Features

- Full-screen transparent overlay** with configurable color and opacity
- Drawable transparent focus areas** - click and drag to create
- Move focus areas** - drag the violet handle on the left side
- Resize focus areas** - drag edges or corners (8 directions)
- Delete focus areas** - right-click the violet handle or press Delete key
- Pause/Resume** - Ctrl+Shift+X, double-click, or use menu/tray
- Peek through mode** - hold Shift to temporarily see through (default 55% transparency)
- Console window control** - hidden by default, show/hide via menu
- System tray icon** with quick access menu
- Configuration save/load** - JSON format with auto-save
- Quick start guide** - dark themed with "Don't show again" option
- Admin privilege auto-elevation** - seamless startup


### Environment Setup

```bash
python -m venv .venv312
.venv312\Scripts\activate
pip install -r requirements.txt
```

### Requirements

- `pillow`
- `pystray`

## Usage

### Quick Start

1. Launch Focus_Area - the screen will be dimmed with a dark overlay
2. **Hold Shift** to peek through the veil and see where to position focus areas
3. **Click and drag** on the dimmed area to create a transparent focus area
4. Drag the violet handle** (left side, upper portion) to move the focus area
5. **Drag edges or corners** to resize the focus area
6. **Right-click the violet handle** to delete the focus area
7. Right-click the dimmed area** to access the menu

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Shift** | Hold to peek through (temporary transparency) |
| **Ctrl+Shift+X** | Pause (hide veil) |
| **Escape** | Show menu |

### Mouse Controls

| Action | Description |
|--------|-------------|
| **Click & Drag** (empty area) | Create new focus area |
| **Click & Drag** (violet handle) | Move focus area |
| **Click & Drag** (edge/corner) | Resize focus area |
| **Right-click** (violet handle) | Delete focus area instantly |
| **Right-click** (dimmed area) | Show context menu |
| **Double-click** | Pause/Resume (toggle) |
| **Mouse Wheel** | Adjust opacity |

### System Tray

- **Click** tray icon to show/hide window
- **Right-click** tray icon for menu (Pause/Resume, Quick Start, Exit)

### Menu Options

- **Pause/Resume** - Toggle veil visibility
- **Color** - Choose custom dimming color or reset to black
- **Opacity** - Set main opacity (1-100%), set as default
- **Peek Through Opacity** - Set Shift key transparency (1-100%), set as default
- **Delete All Focus Areas** - Remove all focus areas
- **Save/Load Configuration** - Manage saved layouts
- **Quick Start Guide** - View help
- **About** - Application information
- **Show/Hide Console** - Toggle console window
- **Exit** - Close application

## Technical Details

- **Default opacity:** 100% (dimming), 55% (peek through)
- **Config file:** `focus_area_config.json` (in exe directory when frozen)

## Source Code

Focus_Area is written in Python


Note: This script was inspired by [CinemaDrape](https://github.com/aurelitec/cinemadrape-windows)


<br><br>



<br><br>



## License

See [LICENSE](https://github.com/Gabrieliam42/Focus_Area/blob/main/LICENSE) file for details.



### Author

**Gabriel Mihai**
GitHub: [Gabrieliam42](https://github.com/Gabrieliam42)
