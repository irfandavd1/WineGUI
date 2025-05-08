import sys
import os
import subprocess
import platform
import gi

try:
    gi.require_version('Gtk', '3.0')
except ValueError as e:
     print(f"Error: Cannot require GTK 3.0 - {e}")
     print("Make sure GTK3 and its GObject introspection bindings are installed.")
     sys.exit(1)

from gi.repository import Gtk, Gio, GLib, Pango

wine_executable_path = None
winetricks_executable_path = None

def find_command(command_name):
    """Tries to find the full path of a command (like 'wine' or 'winetricks')."""
    try:
        result = subprocess.run(['which', command_name], capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass

    common_paths = []
    if sys.platform == "darwin":
        common_paths = ['/usr/local/bin/', '/opt/homebrew/bin/']
    elif sys.platform.startswith("linux"):
        common_paths = ['/usr/bin/', '/bin/', '/usr/local/bin/']

    for path_dir in common_paths:
        full_path = os.path.join(path_dir, command_name)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            return full_path
    try:
        system_path = os.environ.get("PATH", "")
        for path_dir in system_path.split(os.pathsep):
             full_path = os.path.join(path_dir, command_name)
             if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                 return full_path
    except Exception: pass
    return None

def get_wine_environment(prefix_path=None):
    """Prepares the environment variables for Wine commands."""
    env = os.environ.copy()
    if prefix_path and os.path.isdir(prefix_path):
        env['WINEPREFIX'] = prefix_path
    return env

class WineAppWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_default_size(650, 480)
        self.set_border_width(12)

        self.exe_entry = None
        self.prefix_entry = None
        self.statusbar = None
        self.status_context_id = None
        self.run_exe_button = None
        self.tool_buttons = []

        self.find_executables()

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "Wine Launcher Deluxe"
        header.props.subtitle = "GTK3 Edition"
        self.set_titlebar(header)

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.add(main_vbox)

        run_label = Gtk.Label(xalign=0.0)
        run_label.set_markup("<b>Run Windows Executable</b>")
        main_vbox.pack_start(run_label, False, False, 0)

        exe_grid = Gtk.Grid(column_spacing=10, row_spacing=8, margin_top=5)
        main_vbox.pack_start(exe_grid, False, False, 0)

        exe_path_label = Gtk.Label(label="Executable (.exe):", xalign=1.0)
        exe_grid.attach(exe_path_label, 0, 0, 1, 1)

        self.exe_entry = Gtk.Entry(hexpand=True, placeholder_text="Path to .exe file")
        self.exe_entry.set_tooltip_text("Select the Windows application you want to run")
        exe_grid.attach(self.exe_entry, 1, 0, 1, 1)

        exe_browse_button = Gtk.Button.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON)
        exe_browse_button.set_tooltip_text("Browse for executable file")
        exe_browse_button.connect('clicked', self.on_browse_exe_clicked)
        exe_grid.attach(exe_browse_button, 2, 0, 1, 1)

        self.run_exe_button = Gtk.Button(label="Run with Wine")
        self.run_exe_button.set_tooltip_text("Launch the selected executable using Wine")
        self.run_exe_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.run_exe_button.set_halign(Gtk.Align.CENTER)
        self.run_exe_button.set_margin_top(10)
        self.run_exe_button.connect('clicked', self.on_run_exe_clicked)
        main_vbox.pack_start(self.run_exe_button, False, False, 0)
        self.tool_buttons.append(self.run_exe_button)

        main_vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin_top=15, margin_bottom=15),
                              False, False, 0)

        env_label = Gtk.Label(xalign=0.0)
        env_label.set_markup("<b>Wine Environment (WINEPREFIX)</b>")
        main_vbox.pack_start(env_label, False, False, 0)

        prefix_desc_label = Gtk.Label(label="Specify a WINEPREFIX directory (leave blank for default: ~/.wine)",
                                      xalign=0.0, margin_top=2)
        prefix_desc_label.get_style_context().add_class(Gtk.STYLE_CLASS_DIM_LABEL)
        main_vbox.pack_start(prefix_desc_label, False, False, 0)

        prefix_grid = Gtk.Grid(column_spacing=10, row_spacing=5, margin_top=8)
        main_vbox.pack_start(prefix_grid, False, False, 0)

        prefix_path_label = Gtk.Label(label="Prefix Path:", xalign=1.0)
        prefix_grid.attach(prefix_path_label, 0, 0, 1, 1)

        self.prefix_entry = Gtk.Entry(hexpand=True, placeholder_text="Optional: Path to WINEPREFIX")
        self.prefix_entry.set_tooltip_text("Select a directory to act as the Wine 'C:' drive and configuration location")
        prefix_grid.attach(self.prefix_entry, 1, 0, 1, 1)

        prefix_browse_button = Gtk.Button.new_from_icon_name("folder-open-symbolic", Gtk.IconSize.BUTTON)
        prefix_browse_button.set_tooltip_text("Browse for WINEPREFIX directory")
        prefix_browse_button.connect('clicked', self.on_browse_prefix_clicked)
        prefix_grid.attach(prefix_browse_button, 2, 0, 1, 1)

        tools_label = Gtk.Label(xalign=0.0, margin_top=15)
        tools_label.set_markup("<b>Common Wine Tools</b>")
        main_vbox.pack_start(tools_label, False, False, 0)

        tools_desc_label = Gtk.Label(label="These tools operate on the selected WINEPREFIX above.",
                                      xalign=0.0, margin_top=2)
        tools_desc_label.get_style_context().add_class(Gtk.STYLE_CLASS_DIM_LABEL)
        main_vbox.pack_start(tools_desc_label, False, False, 0)

        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10,
                           halign=Gtk.Align.CENTER,
                           margin_top=10)
        main_vbox.pack_start(tools_box, False, False, 0)

        tool_defs = [
            ("winecfg", "preferences-system-symbolic", "Open Wine Configuration (winecfg)"),
            ("uninstaller", "edit-delete-symbolic", "Open Add/Remove Programs (uninstaller)"),
            ("regedit", "document-properties-symbolic", "Open Registry Editor (regedit)"),
            ("winetricks", "accessories-character-map-symbolic", "Run Winetricks Helper")
        ]

        for name, icon, tip in tool_defs:
            btn = Gtk.Button(label=name.capitalize())
            btn.set_tooltip_text(tip)
            btn.connect('clicked', getattr(self, f'on_{name}_clicked'))
            tools_box.pack_start(btn, False, False, 0)
            self.tool_buttons.append(btn)
            if name == "winetricks":
                 self.winetricks_button = btn

        spacer = Gtk.Box()
        main_vbox.pack_start(spacer, True, True, 0)


        self.statusbar = Gtk.Statusbar()
        main_vbox.pack_start(self.statusbar, False, False, 0)
        self.status_context_id = self.statusbar.get_context_id("default")

        self.update_status_check()
        self.set_initial_sensitivity()
        self.show_all()

    def find_executables(self):
        global wine_executable_path, winetricks_executable_path
        wine_executable_path = find_command("wine")
        winetricks_executable_path = find_command("winetricks")

    def set_initial_sensitivity(self):
        global wine_executable_path, winetricks_executable_path
        has_wine = bool(wine_executable_path)
        has_winetricks = bool(winetricks_executable_path)

        for btn in self.tool_buttons:
            is_winetricks = (hasattr(self, 'winetricks_button') and btn == self.winetricks_button)
            if is_winetricks:
                btn.set_sensitive(has_wine and has_winetricks)
            else:
                btn.set_sensitive(has_wine)

    def update_status_check(self):
        global wine_executable_path, winetricks_executable_path
        status = []
        if wine_executable_path:
            status.append(f"Wine: Ready ({os.path.basename(wine_executable_path)})")
        else:
            status.append("❌ Wine not found! Most functions disabled.")
            self.update_status("Error: Wine command not found. Check installation.", is_error=True)


        if winetricks_executable_path:
            status.append(f"Winetricks: Ready ({os.path.basename(winetricks_executable_path)})")
        else:
            status.append("ℹ️ Winetricks not found (optional tool).")
            if hasattr(self, 'winetricks_button') and self.winetricks_button:
                 self.winetricks_button.set_sensitive(False)

        if wine_executable_path:
             self.update_status("Ready. Select an executable or use tools.")

    def update_status(self, message, clear_after=0, is_error=False):
        """Pushes a message to the status bar."""
        print(f"Status: {message}")
        if self.statusbar and self.status_context_id is not None:

             if is_error:
                 message_markup = f'<span color="red">{GLib.markup_escape_text(message)}</span>'
             else:
                 message_markup = GLib.markup_escape_text(message)

             self.statusbar.push(self.status_context_id, message_markup)

             if clear_after > 0:
                 GLib.timeout_add(clear_after * 1000, self.clear_status)


    def clear_status(self):
        """Clears the last message from the status bar."""
        if self.statusbar and self.status_context_id is not None:
             self.statusbar.pop(self.status_context_id)
        return False

    def get_current_prefix_path(self):
        if self.prefix_entry:
             return self.prefix_entry.get_text().strip() or None
        return None

    def show_dialog(self, dialog_type, title, secondary_text):
         """Generic dialog display."""
         dialog = Gtk.MessageDialog(
             transient_for=self.get_toplevel(),
             flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
             message_type=dialog_type,
             buttons=Gtk.ButtonsType.OK,
             text=title
         )
         dialog.format_secondary_text(secondary_text)
         dialog.run()
         dialog.destroy()

    def show_error_dialog(self, title, secondary_text):
        self.show_dialog(Gtk.MessageType.ERROR, title, secondary_text)

    def show_warning_dialog(self, title, secondary_text):
        self.show_dialog(Gtk.MessageType.WARNING, title, secondary_text)

    def _run_file_chooser(self, title, action, entry_widget):
        dialog = Gtk.FileChooserDialog(
            title=title,
            transient_for=self.get_toplevel(),
            action=action
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN if action == Gtk.FileChooserAction.OPEN else Gtk.STOCK_SELECT, Gtk.ResponseType.OK
        )
        dialog.set_default_response(Gtk.ResponseType.OK)

        if action == Gtk.FileChooserAction.OPEN:
            filter_exe = Gtk.FileFilter()
            filter_exe.set_name("Executable files (*.exe)")
            filter_exe.add_pattern("*.exe")
            filter_exe.add_pattern("*.EXE")
            dialog.add_filter(filter_exe)
            filter_any = Gtk.FileFilter()
            filter_any.set_name("All files")
            filter_any.add_pattern("*")
            dialog.add_filter(filter_any)
        elif action == Gtk.FileChooserAction.SELECT_FOLDER:
             try:
                current_value = entry_widget.get_text().strip()
                if current_value and os.path.isdir(current_value):
                     dialog.set_current_folder(current_value)
                else:
                    home_dir = GLib.get_home_dir()
                    default_prefix = os.path.join(home_dir, ".wine")
                    if os.path.isdir(default_prefix):
                        dialog.set_current_folder(default_prefix)
             except Exception as e:
                print(f"Could not set initial folder: {e}")


        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename() if action == Gtk.FileChooserAction.OPEN else dialog.get_current_folder()
            if filepath and entry_widget:
                entry_widget.set_text(filepath)
                self.update_status(f"Selected: {os.path.basename(filepath)}")
        dialog.destroy()

    def on_browse_exe_clicked(self, button):
        self._run_file_chooser("Select Windows Executable", Gtk.FileChooserAction.OPEN, self.exe_entry)

    def on_browse_prefix_clicked(self, button):
         self._run_file_chooser("Select WINEPREFIX Directory", Gtk.FileChooserAction.SELECT_FOLDER, self.prefix_entry)


    def _run_external_process(self, command, env_dict, work_dir=None, tool_name="Process"):
         """Wrapper for running external tools using Popen."""
         global wine_executable_path, winetricks_executable_path

         base_cmd = os.path.basename(command[0])
         if base_cmd == "wine" and not wine_executable_path:
             self.show_error_dialog("Wine Not Found", f"Cannot run {tool_name}.")
             return False
         if base_cmd == "winetricks" and not winetricks_executable_path:
              self.show_error_dialog("Winetricks Not Found", f"Cannot run {tool_name}.")
              return False

         self.update_status(f"Launching {tool_name}...")
         print(f"Executing: {' '.join(command)}")
         print(f"Env Prefix: {env_dict.get('WINEPREFIX', 'Default')}")
         print(f"CWD: {work_dir or 'Default'}")
         try:
             subprocess.Popen(command, env=env_dict, cwd=work_dir,
                              creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                              start_new_session=True if sys.platform != 'win32' else False)

             self.update_status(f"Launched {tool_name}.", clear_after=5)
             return True
         except FileNotFoundError:
            error_msg = f"Command not found: '{command[0]}'. Check installation."
            self.show_error_dialog(f"{tool_name} Error", error_msg)
            self.update_status(f"Error: {error_msg}", is_error=True)
            return False
         except Exception as e:
             error_msg = f"Failed to launch {tool_name}: {e}"
             self.show_error_dialog(f"{tool_name} Error", error_msg)
             self.update_status(f"Error launching {tool_name}: {e}", is_error=True)
             return False

    def on_run_exe_clicked(self, button):
        exe_path = self.exe_entry.get_text().strip()
        if not exe_path:
            self.show_error_dialog("No File Selected", "Please select a Windows executable file (.exe) to run.")
            return
        if not os.path.isfile(exe_path):
             self.show_error_dialog("File Not Found", f"The selected item is not a valid file:\n{exe_path}")
             return
        if not exe_path.lower().endswith('.exe') and '.' in os.path.basename(exe_path):
            self.update_status(f"Warning: '{os.path.basename(exe_path)}' may not be an executable.", clear_after=10)

        prefix_path = self.get_current_prefix_path()
        env_dict = get_wine_environment(prefix_path)
        work_dir = os.path.dirname(exe_path)
        command = [wine_executable_path, exe_path]
        tool_name = f"'{os.path.basename(exe_path)}'"

        self._run_external_process(command, env_dict, work_dir, tool_name)

    def _run_wine_tool(self, wine_arg, tool_name):
        global wine_executable_path
        if not wine_executable_path: return
        prefix_path = self.get_current_prefix_path()
        env_dict = get_wine_environment(prefix_path)
        command = [wine_executable_path, wine_arg]
        self._run_external_process(command, env_dict, None, tool_name)

    def on_winecfg_clicked(self, button):
        self._run_wine_tool('winecfg', "Wine Configuration")

    def on_uninstaller_clicked(self, button):
        self._run_wine_tool('uninstaller', "Wine Uninstaller")

    def on_regedit_clicked(self, button):
        self._run_wine_tool('regedit', "Registry Editor")

    def on_winetricks_clicked(self, button):
        global winetricks_executable_path
        if not winetricks_executable_path: return
        prefix_path = self.get_current_prefix_path()
        env_dict = get_wine_environment(prefix_path)
        command = [winetricks_executable_path]
        self._run_external_process(command, env_dict, None, "Winetricks")


class WineApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='org.example.gtk3.winelauncher.deluxe',
                         flags=Gio.ApplicationFlags.FLAGS_NONE,
                         **kwargs)
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = WineAppWindow(application=self)
            self.window.present()
        else:
             self.window.present()

    def do_startup(self):
        Gtk.Application.do_startup(self)

if __name__ == "__main__":
    app = WineApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)