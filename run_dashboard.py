from app import app
import threading
import webbrowser
import time

def run_flask():
    # Port 80 requires admin privileges
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000")
    while True:
        time.sleep(60) 