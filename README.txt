# How to Build and Run the ETX Dashboard as an .exe

1. Install PyInstaller (if not already):
   pip install pyinstaller

2. Place your custom icon file (e.g., autosupercom.ico) in the project root.

3. Build the .exe:
   pyinstaller --noconsole --onefile --icon=autosupercom.ico run_dashboard.py

   - --noconsole: Runs in the background (no black window)
   - --onefile: Single .exe output
   - --icon: Sets the custom icon for the .exe

4. The .exe will be in the dist/ folder as run_dashboard.exe

5. To access the app at http://autosupercom:5000, edit your hosts file:
   - Open C:\Windows\System32\drivers\etc\hosts as Administrator
   - Add this line:
     127.0.0.1   autosupercom
   - Save the file

6. Double-click run_dashboard.exe to start the server in the background.

7. Open your browser to http://autosupercom:5000

# Optional: Use port 80 for http://autosupercom (no :5000)
- Edit run_dashboard.py to use port=80
- Run as Administrator 