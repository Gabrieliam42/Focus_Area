# Script Developer: Gabriel Mihai Sandu
# GitHub Profile: https://github.com/Gabrieliam42

"""
Focus_Area for Windows - Python Implementation
Creates a dimmed or blackout overlay to help you focus on specific screen areas
"""

import os
import sys
import ctypes
import json
import webbrowser
from pathlib import Path

print("Configuring Tcl/Tk environment...")

is_frozen = getattr(sys, 'frozen', False)

if is_frozen:
    base_path = getattr(sys, '_MEIPASS', sys.prefix)
    print(f"Running as PyInstaller executable")
    print(f"Base path (sys._MEIPASS): {base_path}")
else:
    base_path = sys.prefix if hasattr(sys, 'prefix') else sys.base_prefix
    print(f"Running as Python script")
    print(f"Base path (sys.prefix): {base_path}")

tcl_dir = os.path.join(base_path, 'tcl')
tcl86_dir = os.path.join(tcl_dir, 'tcl8.6')
tk86_dir = os.path.join(tcl_dir, 'tk8.6')

print(f"Looking for Tcl at: {tcl86_dir}")
print(f"Looking for Tk at: {tk86_dir}")

if os.path.exists(tcl86_dir):
    os.environ['TCL_LIBRARY'] = tcl86_dir
    print(f"[OK] Set TCL_LIBRARY to: {tcl86_dir}")
else:
    print(f"[WARNING] Tcl directory not found at: {tcl86_dir}")

if os.path.exists(tk86_dir):
    os.environ['TK_LIBRARY'] = tk86_dir
    print(f"[OK] Set TK_LIBRARY to: {tk86_dir}")
else:
    print(f"[WARNING] Tk directory not found at: {tk86_dir}")

print("Attempting to import tkinter...")

import tkinter as tk
from tkinter import colorchooser, messagebox, Menu, simpledialog

print("[OK] Tkinter imported successfully!")

try:
    import pystray
    from PIL import Image, ImageDraw
    print("[OK] System tray support loaded (pystray)")
    TRAY_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] System tray support not available: {e}")
    print("[INFO] Install with: pip install pystray Pillow")
    TRAY_AVAILABLE = False

print()


SW_HIDE = 0
SW_SHOW = 5

DWMWA_USE_IMMERSIVE_DARK_MODE = 20

def set_dark_title_bar(window):
    """
    Set dark title bar for window using Windows DWM API

    Args:
        window: Tkinter window (Tk or Toplevel)
    """
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
    except Exception as e:
        print(f"[WARNING] Could not set dark title bar: {e}")

def get_console_window():
    """Get handle to console window"""
    return ctypes.windll.kernel32.GetConsoleWindow()

def show_console():
    """Show the console window"""
    hwnd = get_console_window()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)

def hide_console():
    """Hide the console window"""
    hwnd = get_console_window()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)


def create_tray_icon():
    """
    Create a simple icon for the system tray

    Returns:
        PIL.Image: Icon image (64x64)
    """
    if not TRAY_AVAILABLE:
        return None

    width = 64
    height = 64
    icon_image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(icon_image)

    draw.rectangle([8, 8, 56, 56], outline='red', width=3)

    draw.rectangle([20, 20, 44, 44], outline='white', width=2)

    corner_length = 8
    corner_width = 2

    draw.rectangle([8, 8, 8 + corner_length, 8 + corner_width], fill='red')
    draw.rectangle([8, 8, 8 + corner_width, 8 + corner_length], fill='red')

    draw.rectangle([56 - corner_length, 8, 56, 8 + corner_width], fill='red')
    draw.rectangle([56 - corner_width, 8, 56, 8 + corner_length], fill='red')

    draw.rectangle([8, 56 - corner_width, 8 + corner_length, 56], fill='red')
    draw.rectangle([8, 56 - corner_length, 8 + corner_width, 56], fill='red')

    draw.rectangle([56 - corner_length, 56 - corner_width, 56, 56], fill='red')
    draw.rectangle([56 - corner_width, 56 - corner_length, 56, 56], fill='red')

    return icon_image


def check_and_elevate_admin():
    """Check for admin privileges and re-run with elevation if needed"""
    print("Checking for administrator privileges...")

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(f"Error checking admin status: {e}")
        is_admin = False

    if not is_admin:
        print("Not running as administrator. Requesting elevation...")

        script_path = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])

        try:
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                f'"{script_path}" {params}',
                None,
                1
            )

            if ret > 32:
                print("Elevation successful. Closing this window...")
                sys.exit(0)
            else:
                print(f"Elevation failed with return code: {ret}")
                messagebox.showerror(
                    "Elevation Failed",
                    "Failed to run with administrator privileges.\nThe application may not function correctly."
                )
        except Exception as e:
            print(f"Error during elevation: {e}")
            messagebox.showerror("Error", f"Failed to elevate: {e}")
    else:
        print("Running with administrator privileges.")


class FocusArea:
    """Represents a transparent focus area that can be moved and resized"""

    MIN_SIZE = 10
    BORDER_WIDTH = 2
    BORDER_COLOR = "#FF0000"

    current = None

    def __init__(self, parent, x, y, width, height):
        print(f"Creating focus area at ({x}, {y}) with size ({width}, {height})")

        self.parent = parent
        self.canvas = parent.canvas
        self.start_x = x
        self.start_y = y

        self.rect_id = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=parent.transparency_key,
            outline=self.BORDER_COLOR,
            width=self.BORDER_WIDTH,
            tags="focus_area"
        )
        print(f"Focus area filled with transparency key: {parent.transparency_key}")

        self.move_handle_size = 8
        handle_x = x
        handle_y = y + height * 0.382
        self.move_handle_id = self.canvas.create_oval(
            handle_x - self.move_handle_size,
            handle_y - self.move_handle_size,
            handle_x + self.move_handle_size,
            handle_y + self.move_handle_size,
            fill="#8B00FF",
            outline="#6A00CC",
            width=2,
            tags="move_handle"
        )
        self.canvas.tag_raise(self.move_handle_id)
        print(f"Created violet move handle at golden ratio position (38.2% from top) on left side")

        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self.resize_mode = None
        self.resize_handle_size = 10

        self.bind_events()

    def bind_events(self):
        """Bind mouse events for moving and resizing"""
        self.canvas.tag_bind(self.rect_id, "<Button-1>", self.on_press)
        self.canvas.tag_bind(self.rect_id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect_id, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.rect_id, "<Enter>", self.on_enter)
        self.canvas.tag_bind(self.rect_id, "<Leave>", self.on_leave)
        self.canvas.tag_bind(self.rect_id, "<Motion>", self.on_motion)

        self.canvas.tag_bind(self.move_handle_id, "<Button-1>", self.on_handle_press)
        self.canvas.tag_bind(self.move_handle_id, "<B1-Motion>", self.on_handle_drag)
        self.canvas.tag_bind(self.move_handle_id, "<ButtonRelease-1>", self.on_handle_release)
        self.canvas.tag_bind(self.move_handle_id, "<Button-3>", self.on_handle_right_click)
        self.canvas.tag_bind(self.move_handle_id, "<Enter>", self.on_handle_enter)
        self.canvas.tag_bind(self.move_handle_id, "<Leave>", self.on_handle_leave)

    def get_resize_mode(self, event_x, event_y):
        """Determine if mouse is near edge/corner for resizing"""
        coords = self.canvas.coords(self.rect_id)
        if not coords or len(coords) < 4:
            return None

        x1, y1, x2, y2 = coords

        height = y2 - y1
        handle_y = y1 + height * 0.382
        move_handle_buffer = 4

        if (abs(event_x - x1) < self.resize_handle_size + 5 and
            handle_y - self.move_handle_size - move_handle_buffer <= event_y <=
            handle_y + self.move_handle_size + move_handle_buffer):
            return "move"

        handle = self.resize_handle_size

        near_left = abs(event_x - x1) < handle
        near_right = abs(event_x - x2) < handle
        near_top = abs(event_y - y1) < handle
        near_bottom = abs(event_y - y2) < handle

        if near_top and near_left:
            return "nw"
        elif near_top and near_right:
            return "ne"
        elif near_bottom and near_left:
            return "sw"
        elif near_bottom and near_right:
            return "se"
        elif near_top:
            return "n"
        elif near_bottom:
            return "s"
        elif near_left:
            return "w"
        elif near_right:
            return "e"
        else:
            return "move"

    def update_cursor(self, resize_mode):
        """Update cursor based on resize mode"""
        cursor_map = {
            "nw": "size_nw_se",
            "ne": "size_ne_sw",
            "sw": "size_ne_sw",
            "se": "size_nw_se",
            "n": "size_ns",
            "s": "size_ns",
            "w": "size_we",
            "e": "size_we",
            "move": "fleur"
        }
        cursor = cursor_map.get(resize_mode, "arrow")
        try:
            self.canvas.config(cursor=cursor)
        except:
            pass

    def on_motion(self, event):
        """Update cursor when mouse moves over focus area"""
        if not self.is_dragging:
            mode = self.get_resize_mode(event.x, event.y)
            self.update_cursor(mode)

    def on_enter(self, event):
        """Handle mouse entering focus area"""
        self.canvas.itemconfig(self.rect_id, outline="#FF3333", width=self.BORDER_WIDTH + 1)

    def on_leave(self, event):
        """Handle mouse leaving focus area"""
        if FocusArea.current == self:
            FocusArea.current = None
        self.canvas.itemconfig(self.rect_id, outline=self.BORDER_COLOR, width=self.BORDER_WIDTH)
        if not self.is_dragging:
            self.canvas.config(cursor="cross")

    def on_handle_enter(self, event):
        """Handle mouse entering move handle"""
        self.canvas.itemconfig(self.move_handle_id, fill="#AA00FF", outline="#8B00FF")
        self.canvas.config(cursor="fleur")

    def on_handle_leave(self, event):
        """Handle mouse leaving move handle"""
        if not self.is_dragging:
            self.canvas.itemconfig(self.move_handle_id, fill="#8B00FF", outline="#6A00CC")
            self.canvas.config(cursor="cross")

    def on_handle_press(self, event):
        """Handle move handle press"""
        print(f"Move handle pressed at ({event.x}, {event.y})")
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        self.resize_mode = "move"
        FocusArea.current = self

    def on_handle_drag(self, event):
        """Handle move handle drag"""
        if self.is_dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            self.canvas.move(self.rect_id, dx, dy)
            self.canvas.move(self.move_handle_id, dx, dy)

            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def on_handle_release(self, event):
        """Handle move handle release"""
        print(f"Move handle released at ({event.x}, {event.y})")
        self.is_dragging = False
        self.resize_mode = None
        self.canvas.itemconfig(self.move_handle_id, fill="#8B00FF", outline="#6A00CC")

    def on_handle_right_click(self, event):
        """Handle right-click on move handle - delete this focus area"""
        print(f"Move handle right-clicked - deleting focus area")
        self.parent.handle_right_clicked = True
        self.delete()
        return "break"

    def on_press(self, event):
        """Handle mouse button press"""
        print(f"Focus area pressed at ({event.x}, {event.y})")
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        self.resize_mode = self.get_resize_mode(event.x, event.y)
        print(f"Resize mode: {self.resize_mode}")

    def on_drag(self, event):
        """Handle mouse drag for moving or resizing"""
        if not self.is_dragging:
            return

        coords = self.canvas.coords(self.rect_id)
        if not coords or len(coords) < 4:
            return

        x1, y1, x2, y2 = coords
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        if self.resize_mode == "move":
            self.canvas.move(self.rect_id, dx, dy)
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        elif self.resize_mode:
            new_x1, new_y1, new_x2, new_y2 = x1, y1, x2, y2

            if "n" in self.resize_mode:
                new_y1 = event.y
            if "s" in self.resize_mode:
                new_y2 = event.y
            if "w" in self.resize_mode:
                new_x1 = event.x
            if "e" in self.resize_mode:
                new_x2 = event.x

            if new_x2 - new_x1 >= self.MIN_SIZE and new_y2 - new_y1 >= self.MIN_SIZE:
                self.canvas.coords(self.rect_id, new_x1, new_y1, new_x2, new_y2)
                self.update_handle_position()
                self.drag_start_x = event.x
                self.drag_start_y = event.y

    def on_release(self, event):
        """Handle mouse button release"""
        print(f"Focus area released at ({event.x}, {event.y})")
        self.is_dragging = False
        self.resize_mode = None
        self.canvas.config(cursor="cross")

    def update_handle_position(self):
        """Update the position of the move handle to golden ratio point (0.382 from top) on left side"""
        coords = self.canvas.coords(self.rect_id)
        if coords and len(coords) >= 4:
            x1, y1, x2, y2 = coords
            handle_x = x1
            height = y2 - y1
            handle_y = y1 + height * 0.382

            self.canvas.coords(
                self.move_handle_id,
                handle_x - self.move_handle_size,
                handle_y - self.move_handle_size,
                handle_x + self.move_handle_size,
                handle_y + self.move_handle_size
            )

    def delete(self):
        """Delete this focus area"""
        print("Deleting focus area")
        self.canvas.delete(self.rect_id)
        self.canvas.delete(self.move_handle_id)
        if FocusArea.current == self:
            FocusArea.current = None
        if self in self.parent.focus_areas:
            self.parent.focus_areas.remove(self)

    def get_coords(self):
        """Get the coordinates of this focus area"""
        return self.canvas.coords(self.rect_id)


class Focus_AreaWindow:
    """Main Focus_Area window - full screen transparent overlay"""

    MENU_BG = "#2B2B2B"
    MENU_FG = "#FFFFFF"
    MENU_ACTIVE_BG = "#3C3C3C"
    MENU_ACTIVE_FG = "#FFFFFF"

    def __init__(self):
        print("Initializing Focus_Area window...")

        self.root = tk.Tk()
        self.root.title("Focus_Area")

        self.config_file = os.path.join(os.getcwd(), "focus_area_config.json")
        print(f"Configuration file: {self.config_file}")

        self.veil_color = "#0C0000"
        self.veil_opacity = 1.0
        self.transparency_key = "#FF00FF"
        self.is_visible = True
        self.is_transparent_for_editing = False
        self.peek_opacity = 0.3
        self.peek_through_opacity = 0.55
        self.is_peeking = False
        self.last_user_opacity = 1.0
        self.show_quick_start_on_startup = True

        self.focus_areas = []
        self.drawing_rect = None
        self.draw_start_x = 0
        self.draw_start_y = 0

        self.tray_icon = None
        self.tray_thread = None

        self.handle_right_clicked = False

        self.console_visible = False
        hide_console()
        print("Console hidden (use menu to show)")

        self.setup_window()
        self.setup_canvas()

        print("Making window visible...")
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.focus_force()
        self.root.update()
        print("Window is now visible")

        self.setup_keybindings()
        self.load_config(show_message=False)
        self.setup_tray_icon()

        print("Focus_Area window initialized successfully")

    def setup_window(self):
        """Configure the main window properties"""
        print("Setting up window properties...")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        print(f"Screen dimensions: {screen_width}x{screen_height}")

        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.root.overrideredirect(True)

        self.root.attributes('-topmost', True)

        self.root.attributes('-transparentcolor', self.transparency_key)
        print(f"Set transparency key color to: {self.transparency_key}")

        self.update_opacity()

        self.root.configure(bg=self.veil_color)

        print("Window properties configured")

    def setup_canvas(self):
        """Setup the canvas for drawing focus areas"""
        print("Setting up canvas...")

        self.canvas = tk.Canvas(
            self.root,
            bg=self.veil_color,
            highlightthickness=0,
            cursor="cross"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.show_main_menu)
        self.canvas.bind("<Double-Button-1>", self.toggle_pause)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

        print("Canvas setup complete")

    def setup_keybindings(self):
        """
        Setup keyboard shortcuts using Tkinter bindings.

        Strategy: Using local Tkinter bindings instead of global Windows hotkeys.
        This works when the window is focused (which is always, since it's full-screen and topmost).

        Keyboard Shortcuts:
        - Escape: Show context menu
        - Delete: Delete current focus area
        - Shift: Peek through mode (temporary transparency)
        - Ctrl+Shift+X: Pause (hide veil)
        - Ctrl+A: Auto detect area (not implemented yet)
        - Ctrl+W: Auto detect window (not implemented yet)
        """
        print("Setting up keyboard bindings...")

        self.root.bind("<Escape>", lambda e: self.show_main_menu(e))

        self.root.bind("<Delete>", self.delete_current_focus_area)

        self.root.bind("<KeyPress-Shift_L>", self.on_shift_press)
        self.root.bind("<KeyPress-Shift_R>", self.on_shift_press)
        self.root.bind("<KeyRelease-Shift_L>", self.on_shift_release)
        self.root.bind("<KeyRelease-Shift_R>", self.on_shift_release)

        self.root.bind("<Control-Shift-X>", self.on_pause_shortcut)
        self.root.bind("<Control-Shift-x>", self.on_pause_shortcut)


        print("Keyboard bindings configured:")
        print("  - Escape: Show menu")
        print("  - Delete: Delete focus area")
        print("  - Shift: Peek through (hold)")
        print("  - Ctrl+Shift+X: Pause (hide veil)")

    def on_destroy(self, event=None):
        """Cleanup when window is destroyed"""
        if self.tray_icon:
            self.tray_icon.stop()

    def setup_tray_icon(self):
        """Setup system tray icon"""
        if not TRAY_AVAILABLE:
            print("[INFO] System tray icon not available (pystray not installed)")
            return

        print("Setting up system tray icon...")

        try:
            import threading

            icon_image = create_tray_icon()

            menu = pystray.Menu(
                pystray.MenuItem(
                    "Show/Hide",
                    self.tray_toggle_visibility,
                    default=True
                ),
                pystray.MenuItem(
                    lambda text: f"{'Resume' if not self.is_visible else 'Pause (Ctrl+Shift+X)'}",
                    self.tray_toggle_pause
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quick Start Guide", self.tray_show_quick_start),
                pystray.MenuItem(
                    lambda text: f"{'Hide' if self.console_visible else 'Show'} Console",
                    self.tray_toggle_console
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.tray_quit)
            )

            self.tray_icon = pystray.Icon(
                "Focus_Area",
                icon_image,
                "Focus_Area - Click to show/hide",
                menu
            )

            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()

            print("[OK] System tray icon created successfully")

        except Exception as e:
            print(f"[ERROR] Failed to create system tray icon: {e}")
            self.tray_icon = None

    def tray_toggle_visibility(self, icon=None, item=None):
        """Toggle main window visibility from tray - same as pause/resume"""
        self.root.after(0, self.toggle_pause)

    def tray_toggle_pause(self, icon=None, item=None):
        """Toggle pause/resume from tray - same as show/hide"""
        self.root.after(0, self.toggle_pause)

    def tray_show_quick_start(self, icon=None, item=None):
        """Show quick start guide from tray"""
        self.root.after(0, self.show_quick_start)

    def tray_toggle_console(self, icon=None, item=None):
        """Toggle console window visibility from tray"""
        self.root.after(0, self.toggle_console)

    def tray_quit(self, icon=None, item=None):
        """Quit application from tray"""
        self.root.after(0, self.quit_application)

    def on_canvas_press(self, event):
        """Start drawing a new focus area"""
        print(f"Canvas pressed at ({event.x}, {event.y})")

        overlapping = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item in overlapping:
            tags = self.canvas.gettags(item)
            if "focus_area" in tags or "move_handle" in tags:
                print("Clicked on existing focus area or move handle, not creating new one")
                return

        self.draw_start_x = event.x
        self.draw_start_y = event.y

        self.set_transparent_for_editing(True)

    def on_canvas_drag(self, event):
        """Continue drawing the focus area"""
        if self.draw_start_x == 0 and self.draw_start_y == 0:
            return

        if self.drawing_rect:
            self.canvas.delete(self.drawing_rect)

        x1 = min(self.draw_start_x, event.x)
        y1 = min(self.draw_start_y, event.y)
        x2 = max(self.draw_start_x, event.x)
        y2 = max(self.draw_start_y, event.y)

        self.drawing_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.transparency_key,
            outline=FocusArea.BORDER_COLOR,
            width=FocusArea.BORDER_WIDTH,
            tags="drawing"
        )

    def on_canvas_release(self, event):
        """Complete drawing the focus area"""
        print(f"Canvas released at ({event.x}, {event.y})")

        if self.draw_start_x == 0 and self.draw_start_y == 0:
            return

        if self.drawing_rect:
            x1 = min(self.draw_start_x, event.x)
            y1 = min(self.draw_start_y, event.y)
            x2 = max(self.draw_start_x, event.x)
            y2 = max(self.draw_start_y, event.y)

            width = x2 - x1
            height = y2 - y1

            self.canvas.delete(self.drawing_rect)
            self.drawing_rect = None

            if width >= FocusArea.MIN_SIZE and height >= FocusArea.MIN_SIZE:
                focus_area = FocusArea(self, x1, y1, width, height)
                self.focus_areas.append(focus_area)
                print(f"Created focus area: {len(self.focus_areas)} total")
            else:
                print("Focus area too small, not created")

        self.draw_start_x = 0
        self.draw_start_y = 0

        self.set_transparent_for_editing(False)

    def on_mousewheel(self, event):
        """Change opacity with mouse wheel"""
        delta = event.delta / 120

        if delta > 0:
            self.veil_opacity = min(1.0, self.veil_opacity + 0.01)
        else:
            self.veil_opacity = max(0.01, self.veil_opacity - 0.01)

        print(f"Opacity changed to: {self.veil_opacity:.2f}")
        self.update_opacity()

    def on_shift_press(self, event=None):
        """Handle Shift key press for peek through mode (default 55% opacity)"""
        if not self.is_peeking and self.is_visible:
            print("Shift key pressed - activating peek through mode")
            self.is_peeking = True
            if self.veil_opacity > self.peek_through_opacity:
                self.root.attributes('-alpha', self.peek_through_opacity)
                print(f"Peek through opacity: {self.peek_through_opacity} ({round(self.peek_through_opacity * 100)}%)")

    def on_shift_release(self, event=None):
        """Handle Shift key release to restore normal opacity"""
        if self.is_peeking:
            print("Shift key released - restoring normal opacity")
            self.is_peeking = False
            if not self.is_transparent_for_editing:
                self.root.attributes('-alpha', self.veil_opacity)
                print(f"Restored opacity: {self.veil_opacity}")

    def on_pause_shortcut(self, event=None):
        """
        Handle Ctrl+Shift+X keyboard shortcut to PAUSE (hide veil).

        This is a local Tkinter binding.
        Only pauses - does not toggle.
        """
        if self.is_visible:
            print("Ctrl+Shift+X pressed - Pausing (hiding veil)")
            self.is_visible = False
            self.root.withdraw()
        return "break"

    def set_transparent_for_editing(self, transparent):
        """Set semi-transparent mode for easier editing"""
        self.is_transparent_for_editing = transparent

        if transparent:
            self.root.attributes('-alpha', self.peek_opacity)
            print(f"Set to editing peek mode (opacity: {self.peek_opacity})")
        else:
            if not self.is_peeking:
                self.update_opacity()
                print(f"Restored normal opacity: {self.veil_opacity}")

    def update_opacity(self):
        """Update the window opacity"""
        self.last_user_opacity = self.veil_opacity
        if not self.is_peeking and not self.is_transparent_for_editing:
            self.root.attributes('-alpha', self.veil_opacity)

    def toggle_pause(self, event=None):
        """
        Toggle visibility (pause/resume)

        - If visible: Pause (hide veil)
        - If hidden: Resume (show veil)

        Also used for Show/Hide from tray - same functionality.
        """
        self.is_visible = not self.is_visible

        if self.is_visible:
            print("Resuming - showing veil")
            self.root.attributes('-alpha', self.veil_opacity)
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.focus_force()
            self.root.attributes('-alpha', self.veil_opacity)
            self.root.update()
            print(f"Restored opacity to: {self.veil_opacity}")
        else:
            print("Pausing - hiding veil")
            self.root.withdraw()

    def toggle_console(self):
        """Toggle console window visibility"""
        self.console_visible = not self.console_visible

        if self.console_visible:
            show_console()
            print("Console shown")
        else:
            hide_console()
            print("Console hidden")

    def create_styled_menu(self, parent):
        """Create a menu with dark anthracite styling"""
        menu = Menu(
            parent,
            tearoff=0,
            bg=self.MENU_BG,
            fg=self.MENU_FG,
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_ACTIVE_FG,
            relief=tk.FLAT,
            borderwidth=1
        )
        return menu

    def show_info_dialog(self, title, message):
        """Show styled info dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.MENU_BG)
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        set_dark_title_bar(dialog)

        dialog.update_idletasks()
        width = 400
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        msg_label = tk.Label(
            dialog,
            text=message,
            bg=self.MENU_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            wraplength=350,
            justify=tk.LEFT,
            padx=20,
            pady=20
        )
        msg_label.pack(expand=True, fill=tk.BOTH)

        btn_frame = tk.Frame(dialog, bg=self.MENU_BG)
        btn_frame.pack(pady=10)

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=dialog.destroy,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=30,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        ok_btn.pack()

        dialog.grab_set()
        dialog.wait_window()

    def show_warning_dialog(self, title, message):
        """Show styled warning dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.MENU_BG)
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        set_dark_title_bar(dialog)

        dialog.update_idletasks()
        width = 400
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        msg_label = tk.Label(
            dialog,
            text=message,
            bg=self.MENU_BG,
            fg="#FFA500",
            font=("Segoe UI", 10),
            wraplength=350,
            justify=tk.LEFT,
            padx=20,
            pady=20
        )
        msg_label.pack(expand=True, fill=tk.BOTH)

        btn_frame = tk.Frame(dialog, bg=self.MENU_BG)
        btn_frame.pack(pady=10)

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=dialog.destroy,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=30,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        ok_btn.pack()

        dialog.grab_set()
        dialog.wait_window()

    def show_error_dialog(self, title, message):
        """Show styled error dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.MENU_BG)
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        set_dark_title_bar(dialog)

        dialog.update_idletasks()
        width = 400
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        msg_label = tk.Label(
            dialog,
            text=message,
            bg=self.MENU_BG,
            fg="#FF4444",
            font=("Segoe UI", 10),
            wraplength=350,
            justify=tk.LEFT,
            padx=20,
            pady=20
        )
        msg_label.pack(expand=True, fill=tk.BOTH)

        btn_frame = tk.Frame(dialog, bg=self.MENU_BG)
        btn_frame.pack(pady=10)

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=dialog.destroy,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=30,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        ok_btn.pack()

        dialog.grab_set()
        dialog.wait_window()

    def show_confirm_dialog(self, title, message):
        """Show styled confirmation dialog - returns True if OK clicked"""
        result = [False]

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.MENU_BG)
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        set_dark_title_bar(dialog)

        dialog.update_idletasks()
        width = 400
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        msg_label = tk.Label(
            dialog,
            text=message,
            bg=self.MENU_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            wraplength=350,
            justify=tk.LEFT,
            padx=20,
            pady=20
        )
        msg_label.pack(expand=True, fill=tk.BOTH)

        btn_frame = tk.Frame(dialog, bg=self.MENU_BG)
        btn_frame.pack(pady=10)

        def on_ok():
            result[0] = True
            dialog.destroy()

        def on_cancel():
            result[0] = False
            dialog.destroy()

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=on_ok,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=30,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        ok_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=on_cancel,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=20,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        dialog.grab_set()
        dialog.wait_window()

        return result[0]

    def show_input_dialog(self, title, message, initial_value, min_val, max_val):
        """Show styled input dialog - returns integer or None"""
        result: list[int | None] = [None]

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.MENU_BG)
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        set_dark_title_bar(dialog)

        dialog.update_idletasks()
        width = 400
        height = 180
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        msg_label = tk.Label(
            dialog,
            text=message,
            bg=self.MENU_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            wraplength=350,
            justify=tk.LEFT,
            padx=20,
            pady=10
        )
        msg_label.pack()

        entry_frame = tk.Frame(dialog, bg=self.MENU_BG)
        entry_frame.pack(pady=10)

        entry_var = tk.StringVar(value=str(initial_value))
        entry = tk.Entry(
            entry_frame,
            textvariable=entry_var,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 11),
            insertbackground=self.MENU_FG,
            relief=tk.FLAT,
            width=10,
            justify=tk.CENTER
        )
        entry.pack(padx=20)
        entry.select_range(0, tk.END)
        entry.focus()

        btn_frame = tk.Frame(dialog, bg=self.MENU_BG)
        btn_frame.pack(pady=15)

        def on_ok():
            try:
                value = int(entry_var.get())
                if min_val <= value <= max_val:
                    result[0] = value
                    dialog.destroy()
                else:
                    entry.config(bg="#4B2B2B")
                    dialog.after(200, lambda: entry.config(bg=self.MENU_ACTIVE_BG))
            except ValueError:
                entry.config(bg="#4B2B2B")
                dialog.after(200, lambda: entry.config(bg=self.MENU_ACTIVE_BG))

        def on_cancel():
            result[0] = None
            dialog.destroy()

        def on_enter(event):
            on_ok()

        entry.bind('<Return>', on_enter)

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=on_ok,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=30,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        ok_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=on_cancel,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=20,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        dialog.grab_set()
        dialog.wait_window()

        return result[0]

    def show_main_menu(self, event):
        """Show the main context menu"""
        if self.handle_right_clicked:
            print("Handle was just right-clicked - not showing menu")
            self.handle_right_clicked = False
            return "break"

        print("Showing main menu")

        menu = self.create_styled_menu(self.root)

        pause_text = "Resume" if not self.is_visible else "Pause (Ctrl+Shift+X)"
        menu.add_command(label=pause_text, command=self.toggle_pause)
        menu.add_separator()

        color_menu = self.create_styled_menu(menu)
        color_menu.add_command(label="Choose Color...", command=self.choose_color)
        color_menu.add_command(label="Reset to Black", command=self.reset_to_black)
        menu.add_cascade(label="Color", menu=color_menu)

        opacity_menu = self.create_styled_menu(menu)
        opacity_menu.add_command(label=f"Set Opacity (Current: {round(self.veil_opacity * 100)}%)", command=self.set_opacity_dialog)
        opacity_menu.add_separator()
        opacity_menu.add_command(label="Set as Default", command=self.set_default_opacity)
        menu.add_cascade(label="Opacity", menu=opacity_menu)

        peek_opacity_menu = self.create_styled_menu(menu)
        peek_opacity_menu.add_command(label=f"Set Peek Through Opacity (Current: {round(self.peek_through_opacity * 100)}%)", command=self.set_peek_through_opacity_dialog)
        peek_opacity_menu.add_separator()
        peek_opacity_menu.add_command(label="Set as Default", command=self.set_default_peek_through_opacity)
        menu.add_cascade(label="Peek Through Opacity", menu=peek_opacity_menu)

        menu.add_separator()
        menu.add_command(
            label=f"Delete All Focus Areas ({len(self.focus_areas)})",
            command=self.delete_all_focus_areas
        )

        menu.add_separator()
        menu.add_command(label="Save Configuration", command=self.save_config)
        menu.add_command(label="Load Configuration", command=lambda: self.load_config(show_message=True))

        menu.add_separator()
        menu.add_command(label="Quick Start Guide", command=self.show_quick_start)
        menu.add_command(label="About", command=self.show_about)

        menu.add_separator()
        console_text = "Hide Console" if self.console_visible else "Show Console"
        menu.add_command(label=console_text, command=self.toggle_console)

        menu.add_separator()
        menu.add_command(label="Exit", command=self.quit_application)

        try:
            menu.post(event.x_root, event.y_root)
        except:
            menu.post(event.x, event.y)

    def choose_color(self):
        """Open color chooser dialog"""
        print("Opening color chooser...")

        color = colorchooser.askcolor(
            color=self.veil_color,
            title="Choose Veil Color"
        )

        if color[1]:
            new_color = color[1].upper()

            if new_color == self.transparency_key:
                print(f"Warning: Selected color {new_color} conflicts with transparency key")
                self.show_warning_dialog(
                    "Color Conflict",
                    "The selected color conflicts with the transparency key.\nPlease choose a different color."
                )
                return

            self.veil_color = new_color
            print(f"Veil color changed to: {self.veil_color}")
            self.root.configure(bg=self.veil_color)
            self.canvas.configure(bg=self.veil_color)

    def reset_to_black(self):
        """Reset to black color and full opacity"""
        print("Resetting to opaque black")
        self.veil_color = "#000000"
        self.veil_opacity = 1.0
        self.root.configure(bg=self.veil_color)
        self.canvas.configure(bg=self.veil_color)
        self.update_opacity()

    def change_opacity(self, delta):
        """Change opacity by delta"""
        self.veil_opacity = max(0.01, min(1.0, self.veil_opacity + delta))
        print(f"Opacity changed to: {self.veil_opacity:.2f}")
        self.last_user_opacity = self.veil_opacity
        if not self.is_peeking and not self.is_transparent_for_editing:
            self.root.attributes('-alpha', self.veil_opacity)

    def set_opacity_dialog(self):
        """Show dialog to set opacity percentage"""
        current_percent = round(self.veil_opacity * 100)

        result = self.show_input_dialog(
            "Set Opacity",
            f"Enter opacity percentage (1-100):\n\nCurrent: {current_percent}%",
            current_percent,
            1,
            100
        )

        if result is not None:
            self.veil_opacity = result / 100.0
            print(f"Opacity set to: {result}%")
            self.last_user_opacity = self.veil_opacity
            if not self.is_peeking and not self.is_transparent_for_editing:
                self.root.attributes('-alpha', self.veil_opacity)

    def set_default_opacity(self):
        """Save current opacity as default in config file"""
        opacity_percent = round(self.veil_opacity * 100)
        print(f"Setting default opacity to: {opacity_percent}%")

        self.save_config()

        self.show_info_dialog(
            "Default Opacity Set",
            f"Default opacity set to {opacity_percent}%\n\nThis will be loaded on next startup."
        )

    def change_peek_through_opacity(self, delta):
        """Change peek through opacity by delta"""
        self.peek_through_opacity = max(0.01, min(1.0, self.peek_through_opacity + delta))
        print(f"Peek through opacity changed to: {self.peek_through_opacity:.2f}")
        if self.is_peeking:
            self.root.attributes('-alpha', self.peek_through_opacity)

    def set_peek_through_opacity_dialog(self):
        """Show dialog to set peek through opacity percentage"""
        current_percent = round(self.peek_through_opacity * 100)

        result = self.show_input_dialog(
            "Set Peek Through Opacity",
            f"Enter peek through opacity percentage (1-100):\n\nCurrent: {current_percent}%",
            current_percent,
            1,
            100
        )

        if result is not None:
            self.peek_through_opacity = result / 100.0
            print(f"Peek through opacity set to: {result}%")
            if self.is_peeking:
                self.root.attributes('-alpha', self.peek_through_opacity)

    def set_default_peek_through_opacity(self):
        """Save current peek through opacity as default in config file"""
        opacity_percent = round(self.peek_through_opacity * 100)
        print(f"Setting default peek through opacity to: {opacity_percent}%")

        self.save_config()

        self.show_info_dialog(
            "Default Peek Through Opacity Set",
            f"Default peek through opacity set to {opacity_percent}%\n\nThis will be loaded on next startup."
        )

    def delete_current_focus_area(self, event=None):
        """Delete the currently selected focus area"""
        if FocusArea.current:
            print("Deleting current focus area")
            FocusArea.current.delete()
        else:
            print("No focus area selected to delete")

    def delete_all_focus_areas(self):
        """Delete all focus areas"""
        print(f"Deleting all {len(self.focus_areas)} focus areas")

        for focus_area in self.focus_areas[:]:
            focus_area.delete()

        self.focus_areas.clear()
        print("All focus areas deleted")

    def save_config(self):
        """Save current configuration to file"""
        print(f"Saving configuration to: {self.config_file}")

        config = {
            'veil_color': self.veil_color,
            'veil_opacity': self.veil_opacity,
            'peek_through_opacity': self.peek_through_opacity,
            'show_quick_start_on_startup': self.show_quick_start_on_startup,
            'focus_areas': [fa.get_coords() for fa in self.focus_areas]
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("Configuration saved successfully")
            self.show_info_dialog("Saved", "Configuration saved successfully!")
        except Exception as e:
            print(f"Error saving configuration: {e}")
            self.show_error_dialog("Error", f"Failed to save configuration:\n{e}")

    def load_config(self, show_message=False):
        """Load configuration from file"""
        print(f"Loading configuration from: {self.config_file}")

        if not os.path.exists(self.config_file):
            print("Configuration file not found")
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            self.veil_color = config.get('veil_color', '#0C0000')
            self.veil_opacity = config.get('veil_opacity', 1.0)
            self.peek_through_opacity = config.get('peek_through_opacity', 0.55)
            self.show_quick_start_on_startup = config.get('show_quick_start_on_startup', True)

            self.root.configure(bg=self.veil_color)
            self.canvas.configure(bg=self.veil_color)
            self.update_opacity()

            self.delete_all_focus_areas()

            for coords in config.get('focus_areas', []):
                if len(coords) == 4:
                    x1, y1, x2, y2 = coords
                    width = x2 - x1
                    height = y2 - y1
                    focus_area = FocusArea(self, x1, y1, width, height)
                    self.focus_areas.append(focus_area)

            print(f"Configuration loaded: {len(self.focus_areas)} focus areas restored")

            if show_message:
                self.show_info_dialog("Loaded", "Configuration loaded successfully!")

        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.show_error_dialog("Error", f"Failed to load configuration:\n{e}")

    def show_quick_start(self):
        """Show quick start guide"""
        print("Showing quick start guide")

        guide_text = """Focus_Area - Quick Start Guide

IMPORTANT TIP - START HERE:
Press and hold SHIFT to temporarily see through the veil (55% transparency)
This helps you see where to position your focus areas!

HOW TO USE:
- Click and drag on the dark area to create focus areas
- Drag the VIOLET HANDLE (left side) to move focus areas
- Drag edges or corners to resize focus areas
- Right-click the violet handle to DELETE a focus area
- Right-click the dimmed area to show menu
- Double-click anywhere to pause/resume
- Scroll mouse wheel to change opacity
- Hold SHIFT key to peek through the veil temporarily
- Look for Focus_Area in the system tray!

DELETING FOCUS AREAS:
- Right-click the violet move handle to delete instantly
- Or click the violet handle first, then press Delete key
- Or use menu: Delete All Focus Areas

SYSTEM TRAY:
- Click tray icon to show/hide the veil
- Right-click tray icon for quick menu access
- Access Quick Start and Exit from tray

KEYBOARD SHORTCUTS:
- Shift         : Hold to peek through (see underlying content)
- Ctrl+Shift+X  : Pause (hide veil)
- Escape        : Show menu
- Delete        : Delete focus area (after clicking violet handle)

MOUSE ACTIONS:
- Left-click drag (empty area)    : Create focus area
- Left-click drag (violet handle) : Move focus area
- Left-click drag (edge/corner)   : Resize focus area
- Right-click (violet handle)     : Delete focus area
- Right-click (dimmed area)       : Show menu
- Double-click                    : Pause/Resume
- Mouse wheel                     : Change opacity

TIP: Focus areas are transparent windows where
you can see your actual content clearly while
the rest of the screen remains dimmed.

Look for the small violet circle on the LEFT SIDE
(upper portion at golden ratio point) - that's your move handle!

PEEK THROUGH TIP: Hold Shift to temporarily make the veil
more transparent (55%) so you can see where to position
your focus areas!"""

        guide_window = tk.Toplevel(self.root)
        guide_window.title("Focus_Area - Quick Start")
        guide_window.geometry("550x650")
        guide_window.attributes('-topmost', True)
        guide_window.configure(bg="#2C2C2C")
        set_dark_title_bar(guide_window)

        text_widget = tk.Text(
            guide_window,
            wrap=tk.WORD,
            padx=20,
            pady=20,
            bg="#2C2C2C",
            fg="white",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            insertbackground="white"
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', guide_text)
        text_widget.config(state=tk.DISABLED)

        bottom_frame = tk.Frame(guide_window, bg="#2C2C2C")
        bottom_frame.pack(pady=10, fill=tk.X)

        dont_show_var = tk.BooleanVar(value=not self.show_quick_start_on_startup)

        def on_checkbox_toggle():
            """Handle checkbox toggle"""
            self.show_quick_start_on_startup = not dont_show_var.get()
            print(f"Show Quick Start on startup: {self.show_quick_start_on_startup}")
            self.save_config()

        checkbox = tk.Checkbutton(
            bottom_frame,
            text="Don't show me this again",
            variable=dont_show_var,
            command=on_checkbox_toggle,
            bg="#2C2C2C",
            fg="white",
            selectcolor="#3C3C3C",
            activebackground="#2C2C2C",
            activeforeground="white",
            font=("Segoe UI", 9),
            cursor="hand2"
        )
        checkbox.pack(side=tk.LEFT, padx=20)

        close_btn = tk.Button(
            bottom_frame,
            text="Close",
            command=guide_window.destroy,
            padx=20,
            pady=10,
            bg="#3C3C3C",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            activebackground="#4C4C4C",
            activeforeground="white",
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, padx=20)

    def show_about(self):
        """Show about dialog"""
        print("Showing about dialog")

        github_url = "https://github.com/Gabrieliam42"

        about_window = tk.Toplevel(self.root)
        about_window.title("About Focus_Area")
        about_window.configure(bg=self.MENU_BG)
        about_window.resizable(False, False)
        about_window.attributes('-topmost', True)
        set_dark_title_bar(about_window)

        about_window.update_idletasks()
        width = 450
        height = 300
        x = (about_window.winfo_screenwidth() // 2) - (width // 2)
        y = (about_window.winfo_screenheight() // 2) - (height // 2)
        about_window.geometry(f'{width}x{height}+{x}+{y}')

        text_widget = tk.Text(
            about_window,
            wrap=tk.WORD,
            padx=20,
            pady=20,
            bg=self.MENU_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            insertbackground=self.MENU_FG
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        text_widget.insert('1.0', """Focus_Area for Windows
Python Implementation
Version: 1.0.0

Developed by:
Gabriel Mihai
""")

        link_start = text_widget.index('end-1c')
        text_widget.insert('end', github_url)
        link_end = text_widget.index('end-1c')

        text_widget.insert('end', """

Focus_Area helps you focus on your current
task by dimming other screen areas.""")

        text_widget.tag_add("link", link_start, link_end)
        text_widget.tag_config("link", foreground="#5DADE2", underline=True)

        def open_link(event):
            webbrowser.open(github_url)

        def on_link_enter(event):
            text_widget.config(cursor="hand2")

        def on_link_leave(event):
            text_widget.config(cursor="")

        text_widget.tag_bind("link", "<Button-1>", open_link)
        text_widget.tag_bind("link", "<Enter>", on_link_enter)
        text_widget.tag_bind("link", "<Leave>", on_link_leave)

        text_widget.config(state=tk.DISABLED)

        bottom_frame = tk.Frame(about_window, bg=self.MENU_BG)
        bottom_frame.pack(pady=10)

        close_btn = tk.Button(
            bottom_frame,
            text="OK",
            command=about_window.destroy,
            bg=self.MENU_ACTIVE_BG,
            fg=self.MENU_FG,
            font=("Segoe UI", 10),
            padx=30,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.MENU_ACTIVE_BG,
            activeforeground=self.MENU_FG
        )
        close_btn.pack()

    def quit_application(self):
        """Exit the application"""
        print("Exiting Focus_Area...")

        if self.show_confirm_dialog("Exit", "Are you sure you want to exit Focus_Area?"):
            print("User confirmed exit")
            self.root.quit()
            self.root.destroy()
        else:
            print("Exit cancelled")

    def run(self):
        """Start the application main loop"""
        print("Starting Focus_Area main loop...")
        print("="*60)
        print("Focus_Area is now running!")
        print("Press Ctrl+Shift+X to pause (or double-click to toggle)")
        print("Right-click or press Escape to show menu")
        print("="*60)

        if self.show_quick_start_on_startup:
            print("Quick Start guide will be shown after 1 second")
            self.root.after(1000, self.show_quick_start)
        else:
            print("Quick Start guide disabled on startup (use menu to access)")

        self.root.mainloop()


def main():
    """Main entry point"""
    print("="*60)
    print("Focus_Area for Windows - Python Implementation")
    print("="*60)
    print()

    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    print()

    print("Listing directory contents:")
    for root, dirs, files in os.walk(cwd):
        level = root.replace(cwd, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")

        sub_indent = ' ' * 2 * (level + 1)
        for file in files[:10]:
            print(f"{sub_indent}{file}")

        if len(files) > 10:
            print(f"{sub_indent}... and {len(files) - 10} more files")

        if level > 2:
            break

    print()

    check_and_elevate_admin()

    print()
    print("Creating Focus_Area window...")

    try:
        app = Focus_AreaWindow()
        app.run()
    except Exception as e:
        print(f"ERROR: An error occurred while running Focus_Area: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Focus_Area encountered an error:\n\n{e}")

    print()
    print("Focus_Area has been closed.")
    print("="*60)


if __name__ == "__main__":
    main()
