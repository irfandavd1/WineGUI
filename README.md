🍷 Wine Launcher Deluxe (GTK3 Edition)

A sleek, user-friendly GUI for running Windows .exe apps on Linux via Wine. Built with GTK 3, this Python app gives you control over Wine environments, tools, and prefixes — no terminal needed.
💡 Features

    🟢 Run Windows Executables: Launch .exe apps easily via Wine

    📁 Prefix Management: Set or browse for custom WINEPREFIX paths

    🛠️ Built-in Tools:

        winecfg (Wine configuration)

        regedit (Registry editor)

        uninstaller (Windows software manager)

        winetricks (extra tweaks and libraries)

    🧠 Smart Detection: Auto-detects Wine and Winetricks paths

    ✅ GTK3 Interface: Modern layout with header bar, tooltips, and status messages

    🔄 Cross-Platform Ready: Works on most Linux distros with GTK3 and Wine installed

📦 Requirements

    Python 3

    GTK 3 (python3-gi and gir1.2-gtk-3.0)

    Wine

    (Optional) Winetricks

Ubuntu/Debian:

sudo apt install python3-gi gir1.2-gtk-3.0 wine winetricks

🚀 How to Run

python3 Revamped_GUI-Wine.py

Or make it executable and run directly:

chmod +x Revamped_GUI-Wine.py
./Revamped_GUI-Wine.py

🧩 File Structure

Revamped_GUI-Wine.py   # main Python GTK3 app
README.md              

❗ Notes

    If Wine or Winetricks isn’t found, the buttons will be disabled automatically

    You can still run .exe files even without a custom WINEPREFIX (defaults to ~/.wine)

    winetricks is optional, but highly recommended

⚠️ Troubleshooting

    Gtk ImportError → Make sure GTK3 and its introspection bindings are installed

    .exe not running → Check if Wine is installed and functional on its own

    Permissions issue → Ensure the script is executable

