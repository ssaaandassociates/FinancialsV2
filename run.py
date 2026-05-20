import uvicorn
import webbrowser
import threading
import time
import os


def open_browser():
    """Wait for server to start, then open browser (local only)."""
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000/")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    port = int(os.environ.get("PORT", 8000))
    is_cloud = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT")

    if not is_cloud:
        threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 50)
    print("  TCE Financial Statement Engine v4.0")
    print("  TrustFactON Compliance Engine")
    print("=" * 50)
    print(f"  Running on port {port}")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_cloud,
    )