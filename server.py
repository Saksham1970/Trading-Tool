from app_config import app, socketio
from utils.startup import startup
from scheduler import setup_scheduler, start_quote_streaming
import threading

startup()  # Comment out to avoid unnecessary data fetching
from routes.__init__ import *


@app.route("/")
def home():
    return "Flask is running", 200


def run_quote_streaming():
    import asyncio

    asyncio.set_event_loop(asyncio.new_event_loop())
    start_quote_streaming()


if __name__ == "__main__":
    setup_scheduler()

    # Start quote streaming in a separate thread
    quote_streaming_thread = threading.Thread(target=run_quote_streaming)
    quote_streaming_thread.daemon = True
    quote_streaming_thread.start()

    # Run the Flask app with SocketIO
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
