from server import app, socketio, setup_scheduler, run_quote_streaming
import threading

setup_scheduler()

# Start quote streaming in a separate thread
quote_streaming_thread = threading.Thread(target=run_quote_streaming)
quote_streaming_thread.daemon = True
quote_streaming_thread.start()

# This is the application object that Gunicorn will use
application = socketio.middleware(app)
