"""하모니아 Harmonia 웹서버 (Cloud Run용)"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

PORT = int(os.environ.get('PORT', 8080))


class Handler(SimpleHTTPRequestHandler):
    # Extend MIME type mappings for audio files
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        '.mid': 'audio/midi',
        '.midi': 'audio/midi',
    }

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        return super().do_GET()

    def end_headers(self):
        # Cache static assets (MIDI files, CSS, JS) for 1 hour
        if any(self.path.endswith(ext) for ext in ('.mid', '.midi', '.css', '.js', '.json')):
            self.send_header('Cache-Control', 'public, max-age=3600')
        super().end_headers()

    def log_message(self, format, *args):
        # Use standard format for Cloud Run logging
        print(f"{self.client_address[0]} - {format % args}")


if __name__ == '__main__':
    print(f"Serving on port {PORT}")
    try:
        HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
