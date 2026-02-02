#   """
#   NSAC Competition Management System - WSGI Server Entry Point

#   This module serves as the entry point for running the WSGI server.
#   It performs database migrations and starts the development server using Werkzeug.
#   """

from werkzeug.serving import run_simple
from app import application
from db.migrations import migrate

if __name__ == "__main__":
    # Run database migrations before starting the server
    migrate()

    host, port = "127.0.0.1", 8000
    print(f"✅ Server running: http://{host}:{port}")

    run_simple(
        hostname=host,
        port=port,
        application=application,
        use_reloader=True,   # Auto restart on file change
        use_debugger=True    # Interactive debugger
    )

