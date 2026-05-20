"""
Run this ONCE to create a Desktop shortcut for TCE Engine.
Usage: python create_shortcut.py
"""
import os
import sys


def create_shortcut():
    bat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TCE Engine.bat")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")

    if os.name != 'nt':
        print("This script is for Windows only.")
        return

    try:
        # Use PowerShell to create .lnk shortcut
        shortcut_path = os.path.join(desktop, "TCE Engine.lnk")
        working_dir = os.path.dirname(bat_path)

        ps_script = f'''
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{bat_path}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "TCE Financial Statement Engine - TrustFactON"
$Shortcut.Save()
'''
        os.system(f'powershell -Command "{ps_script.strip()}"')
        print(f"Desktop shortcut created: {shortcut_path}")
        print("You can now double-click 'TCE Engine' on your Desktop!")

    except Exception as e:
        print(f"Could not create shortcut: {e}")
        print(f"\nManual alternative:")
        print(f"  1. Right-click Desktop → New → Shortcut")
        print(f"  2. Location: {bat_path}")
        print(f"  3. Name: TCE Engine")


if __name__ == "__main__":
    create_shortcut()
