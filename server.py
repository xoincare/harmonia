"""
Harmonia Backend v3.0 (GCS Cloud-Native)
- SQLite DB on GCS (Cached locally)
- MIDI Streaming directly from GCS
- Fallback to local files
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os, json, sqlite3, urllib.parse
from google.cloud import storage
from google.api_core import exceptions

PORT = int(os.environ.get('PORT', 8080))
BUCKET_NAME = os.environ.get('GCS_BUCKET', 'harmonia-midi')
DB_FILE = 'harmonia.db'
LOCAL_DB_CACHE = '/tmp/harmonia.db'

class HarmoniaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        self.ensure_db_ready()
        super().__init__(*args, **kwargs)

    def ensure_db_ready(self):
        """Ensure DB is available locally (from GCS or local)"""
        if not os.path.exists(LOCAL_DB_CACHE):
            try:
                # GCS_BUCKET 환경변수가 없으면 기본값 사용
                bucket_name = os.environ.get('GCS_BUCKET', 'harmonia-midi')
                blob = self.storage_client.bucket(bucket_name).blob(DB_FILE)
                blob.download_to_filename(LOCAL_DB_CACHE)
                print(f"✅ DB downloaded from GCS: gs://{bucket_name}/{DB_FILE}")
            except Exception as e:
                print(f"⚠️ GCS DB download failed: {e}")
                # 로컬에 파일이 있으면 복사 (빌드 시 포함된 경우)
                if os.path.exists(DB_FILE):
                    import shutil
                    shutil.copy2(DB_FILE, LOCAL_DB_CACHE)
                    print("✅ Using local bundled DB")
                else:
                    # 빈 DB라도 생성하여 크래시 방지
                    conn = sqlite3.connect(LOCAL_DB_CACHE)
                    conn.execute("CREATE TABLE IF NOT EXISTS tracks (id INTEGER PRIMARY KEY)")
                    conn.close()
                    print("⚠️ Created empty fallback DB")

    def do_GET(self):
        # 1. API: Search
        if self.path.startswith('/api/search'):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q', [''])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            results = self.search_db(query)
            self.wfile.write(json.dumps(results).encode())
            return

        # 2. API: Get Channel
        if self.path.startswith('/api/channel'):
            channel_id = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('id', [''])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            results = self.get_channel_songs(channel_id)
            self.wfile.write(json.dumps(results).encode())
            return

        # 3. API: Stream MIDI (Redirect or Proxy GCS)
        if self.path.startswith('/api/stream'):
            track_id = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('id', [''])[0]
            self.stream_midi_gcs(track_id)
            return

        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        return super().do_GET()

    def search_db(self, query):
        if len(query) < 2: return []
        conn = sqlite3.connect(LOCAL_DB_CACHE)
        c = conn.cursor()
        q = f"%{query}%"
        c.execute('''SELECT id, title, composer, dataset, era, tags, license_type, license_summary 
                     FROM tracks 
                     WHERE title LIKE ? OR composer LIKE ? OR tags LIKE ?
                     LIMIT 100''', (q, q, q))
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "title": r[1], "composer": r[2], "dataset": r[3], "era": r[4], "tags": r[5], "license": r[6], "license_text": r[7]} for r in rows]

    def get_channel_songs(self, channel_id):
        conn = sqlite3.connect(LOCAL_DB_CACHE)
        c = conn.cursor()
        if channel_id == 'classical':
            c.execute('SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks WHERE dataset = "mutopia_midi" ORDER BY title LIMIT 100')
        elif channel_id == 'korean_master':
            c.execute('SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks WHERE dataset = "korean_jeongganbo" ORDER BY title LIMIT 100')
        elif channel_id == 'piano_healing':
            c.execute('SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks WHERE dataset = "adl-piano-midi" ORDER BY title LIMIT 100')
        else:
            c.execute('SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks ORDER BY RANDOM() LIMIT 100')
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "title": r[1], "composer": r[2], "dataset": r[3], "era": r[4], "tags": r[5], "license": r[6], "license_text": r[7]} for r in rows]
        elif channel_id == 'piano_healing':
            c.execute('SELECT id, title, composer, dataset, era, tags FROM tracks WHERE dataset = "adl-piano-midi" LIMIT 100')
        else:
            c.execute('SELECT id, title, composer, dataset, era, tags FROM tracks LIMIT 100')
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "title": r[1], "composer": r[2], "dataset": r[3], "era": r[4], "tags": r[5]} for r in rows]

    def stream_midi_gcs(self, track_id):
        conn = sqlite3.connect(LOCAL_DB_CACHE)
        c = conn.cursor()
        c.execute('SELECT path FROM tracks WHERE id = ?', (track_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            gcs_path = row[0]
            blob = self.bucket.blob(f"datasets/{gcs_path}")
            try:
                # Sign URL for temporary access (1 hour)
                signed_url = blob.generate_signed_url(version="v4", expiration=3600, method="GET")
                self.send_response(302) # Redirect to GCS
                self.send_header('Location', signed_url)
                self.end_headers()
            except Exception:
                # Fallback: Proxy streaming if signing fails
                self.send_response(200)
                self.send_header('Content-Type', 'audio/midi')
                self.end_headers()
                blob.download_to_file(self.wfile)
        else:
            self.send_error(404)

if __name__ == '__main__':
    print(f"🎵 Harmonia GCS-Ready Server on port {PORT}")
    HTTPServer(('0.0.0.0', PORT), HarmoniaHandler).serve_forever()
