import cgi
import html
import shutil
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .video import VideoAnalyzer


UPLOAD_DIR = Path("data/uploads")
REPORTS_DIR = Path("reports")


def serve(config, host: str = "127.0.0.1", port: int = 8080) -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    class Handler(AnalyzerRequestHandler):
        analyzer_config = config

    server = ThreadingHTTPServer((host, port), Handler)
    print("Локальный интерфейс запущен: http://%s:%s" % (host, port))
    print("Для остановки нажмите Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановка сервера")
    finally:
        server.server_close()


class AnalyzerRequestHandler(BaseHTTPRequestHandler):
    analyzer_config = {}

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self._send_html(self._render_form())
            return
        if self.path.startswith("/runs/"):
            self._serve_report_file()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self):
        if self.path != "/analyze":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type"),
            },
        )
        upload = form["video"] if "video" in form else None
        if upload is None or not getattr(upload, "filename", None):
            self._send_html(self._render_form("Выберите видеофайл для анализа."), HTTPStatus.BAD_REQUEST)
            return

        safe_name = _safe_filename(upload.filename)
        run_id = datetime.now().strftime("web-%Y%m%d-%H%M%S")
        upload_path = UPLOAD_DIR / ("%s-%s" % (run_id, safe_name))
        output_dir = REPORTS_DIR / run_id

        with upload_path.open("wb") as target:
            shutil.copyfileobj(upload.file, target)

        try:
            analyzer = VideoAnalyzer(self.analyzer_config)
            analyzer.analyze(str(upload_path), str(output_dir))
        except Exception as exc:  # noqa: BLE001 - show local operator the failure.
            self._send_html(
                self._render_form("Ошибка анализа: %s" % html.escape(str(exc))),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/runs/%s/report.html" % run_id)
        self.end_headers()

    def _serve_report_file(self):
        relative = unquote(self.path[len("/runs/") :]).lstrip("/")
        path = (REPORTS_DIR / relative).resolve()
        reports_root = REPORTS_DIR.resolve()
        if reports_root not in path.parents and path != reports_root:
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        if path.suffix.lower() == ".html":
            content_type = "text/html; charset=utf-8"
        elif path.suffix.lower() == ".json":
            content_type = "application/json; charset=utf-8"
        elif path.suffix.lower() in {".jpg", ".jpeg"}:
            content_type = "image/jpeg"
        elif path.suffix.lower() == ".png":
            content_type = "image/png"
        else:
            content_type = "application/octet-stream"

        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, body: str, status=HTTPStatus.OK):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _render_form(self, message: str = "") -> str:
        message_html = "<p class=\"message\">%s</p>" % message if message else ""
        return """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Анализ касок</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; max-width: 760px; }}
    form {{ border: 1px solid #d8dee4; padding: 24px; border-radius: 8px; }}
    button {{ margin-top: 16px; padding: 10px 16px; }}
    .message {{ color: #9b1c1c; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Локальный анализ наличия касок</h1>
  <p>Загрузите одно видео. Файл будет обработан локально, отчет сохранится в папку <code>reports/</code>.</p>
  {message}
  <form method="post" action="/analyze" enctype="multipart/form-data">
    <label>Видео: <input type="file" name="video" accept="video/*" required></label><br>
    <button type="submit">Запустить анализ</button>
  </form>
</body>
</html>
""".format(message=message_html)


def _safe_filename(filename: str) -> str:
    allowed = []
    for char in filename:
        if char.isalnum() or char in {".", "-", "_"}:
            allowed.append(char)
        else:
            allowed.append("_")
    return "".join(allowed).strip("._") or "video"
