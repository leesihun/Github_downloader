from app import app

if __name__ == "__main__":
    # Port 80 requires admin privileges
    app.run(host="0.0.0.0", port=80, debug=False) 