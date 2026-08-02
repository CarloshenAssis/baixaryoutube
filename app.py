import json
import os
import re
import subprocess
import threading
import uuid
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

YOUTUBE_HOST_RE = re.compile(
    r"^(www\.|m\.|music\.)?(youtube\.com|youtu\.be)$", re.IGNORECASE
)

# Estado em memória
queue = []  # lista de dicts: {id, url, title, status, error}
queue_lock = threading.Lock()
current_process = None
process_lock = threading.Lock()
worker_thread = None
cancel_requested = False
settings_lock = threading.Lock()


def load_settings():
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {"ytdlp_dir": data.get("ytdlp_dir", "")}
        except Exception:
            pass
    return {"ytdlp_dir": ""}


def save_settings(settings):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


settings = load_settings()


def get_ytdlp_dir():
    with settings_lock:
        return settings.get("ytdlp_dir", "")


def get_ytdlp_exe():
    return os.path.join(get_ytdlp_dir(), "yt-dlp.exe")


def get_downloads_dir():
    return os.path.join(get_ytdlp_dir(), "downloads")


def is_youtube_url(url):
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        return bool(YOUTUBE_HOST_RE.match(parsed.netloc))
    except Exception:
        return False


def check_installation():
    ytdlp_dir = get_ytdlp_dir()
    if not ytdlp_dir:
        return ["pasta do yt-dlp não configurada"]
    missing = []
    if not os.path.isfile(os.path.join(ytdlp_dir, "yt-dlp.exe")):
        missing.append("yt-dlp.exe")
    for exe in ("ffmpeg.exe", "ffprobe.exe"):
        if not os.path.isfile(os.path.join(ytdlp_dir, exe)):
            missing.append(exe)
    return missing


def ensure_downloads_dir():
    os.makedirs(get_downloads_dir(), exist_ok=True)


def process_queue(no_playlist):
    global current_process, cancel_requested

    ensure_downloads_dir()
    ytdlp_dir = get_ytdlp_dir()
    ytdlp_exe = get_ytdlp_exe()
    downloads_dir = get_downloads_dir()

    for item in queue:
        with queue_lock:
            if cancel_requested:
                item["status"] = "cancelado" if item["status"] == "pendente" else item["status"]
                continue
            if item["status"] != "pendente":
                continue
            item["status"] = "baixando"

        cmd = [
            ytdlp_exe,
            "-x",
            "--audio-format", "mp3",
            "--ffmpeg-location", ytdlp_dir,
            "-o", os.path.join(downloads_dir, "%(title)s.%(ext)s"),
            "--print", "after_move:filepath",
        ]
        if no_playlist:
            cmd.insert(3, "--no-playlist")
        cmd.append(item["url"])

        try:
            with process_lock:
                if cancel_requested:
                    item["status"] = "cancelado"
                    continue
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                current_process = proc

            output_lines = []
            for line in proc.stdout:
                output_lines.append(line)
                title_match = re.search(r"\[download\] Destination: (.+)", line)
                if title_match:
                    base = os.path.basename(title_match.group(1))
                    item["title"] = os.path.splitext(base)[0]
                extract_match = re.search(r"\[ExtractAudio\] Destination: (.+)", line)
                if extract_match:
                    base = os.path.basename(extract_match.group(1))
                    item["title"] = os.path.splitext(base)[0]

            proc.wait()

            with process_lock:
                current_process = None

            if cancel_requested:
                item["status"] = "cancelado"
                continue

            if proc.returncode == 0:
                item["status"] = "concluido"
            else:
                item["status"] = "erro"
                item["error"] = friendly_error("".join(output_lines))

        except FileNotFoundError:
            item["status"] = "erro"
            item["error"] = "yt-dlp.exe ou ffmpeg.exe não encontrado. Verifique a instalação."
        except Exception as exc:
            item["status"] = "erro"
            item["error"] = str(exc)


def friendly_error(output):
    lowered = output.lower()
    if "video unavailable" in lowered or "this video is unavailable" in lowered:
        return "Vídeo indisponível ou removido."
    if "private video" in lowered:
        return "Vídeo privado."
    if "sign in to confirm" in lowered or "age" in lowered and "restrict" in lowered:
        return "Vídeo com restrição de idade/login."
    if "unable to extract" in lowered:
        return "Não foi possível extrair informações do vídeo (link inválido ou formato não suportado)."
    if "http error 429" in lowered:
        return "Muitas requisições ao YouTube (erro 429). Tente novamente mais tarde."
    tail = output.strip().splitlines()
    return tail[-1] if tail else "Erro desconhecido ao baixar o vídeo."


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/check")
def api_check():
    missing = check_installation()
    return jsonify({"ok": len(missing) == 0, "missing": missing, "path": get_ytdlp_dir()})


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify({"ytdlp_dir": get_ytdlp_dir()})


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    data = request.get_json(force=True) or {}
    path = (data.get("ytdlp_dir") or "").strip().strip('"')

    if not path:
        return jsonify({"error": "Informe um caminho de pasta."}), 400
    if not os.path.isdir(path):
        return jsonify({"error": "A pasta informada não existe."}), 400

    with settings_lock:
        settings["ytdlp_dir"] = path
        save_settings(settings)

    missing = check_installation()
    return jsonify({"ytdlp_dir": path, "ok": len(missing) == 0, "missing": missing})


@app.route("/api/browse-folder", methods=["POST"])
def api_browse_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return jsonify({"error": "Seleção de pasta nativa não disponível neste sistema."}), 400

    result = {}

    def run_dialog():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        initial = get_ytdlp_dir() or os.path.expanduser("~")
        chosen = filedialog.askdirectory(initialdir=initial, title="Selecione a pasta do yt-dlp")
        root.destroy()
        result["path"] = chosen

    dialog_thread = threading.Thread(target=run_dialog)
    dialog_thread.start()
    dialog_thread.join()

    return jsonify({"path": result.get("path") or ""})


@app.route("/api/queue", methods=["POST"])
def api_add_queue():
    global queue, cancel_requested

    with queue_lock:
        if any(i["status"] == "baixando" for i in queue):
            return jsonify({"error": "Já existe um processamento em andamento."}), 400

    data = request.get_json(force=True)
    urls = data.get("urls", [])
    urls = [u.strip() for u in urls if u.strip()][:10]

    if not urls:
        return jsonify({"error": "Nenhum link informado."}), 400

    with queue_lock:
        queue = []
        cancel_requested = False
        for url in urls:
            item = {
                "id": str(uuid.uuid4()),
                "url": url,
                "title": url,
                "status": "pendente",
                "error": None,
            }
            if not is_youtube_url(url):
                item["status"] = "erro"
                item["error"] = "Link inválido: não parece ser uma URL do YouTube."
            queue.append(item)

    return jsonify({"queue": queue})


@app.route("/api/start", methods=["POST"])
def api_start():
    global worker_thread, cancel_requested

    if not get_ytdlp_dir():
        return jsonify({"error": "Configure a pasta do yt-dlp antes de iniciar."}), 400

    missing = check_installation()
    if missing:
        return jsonify({
            "error": f"Arquivos não encontrados na pasta configurada: {', '.join(missing)}. Verifique o caminho de instalação."
        }), 400

    with queue_lock:
        if not queue:
            return jsonify({"error": "A fila está vazia."}), 400
        if worker_thread and worker_thread.is_alive():
            return jsonify({"error": "Já existe um processamento em andamento."}), 400

    data = request.get_json(force=True) or {}
    no_playlist = data.get("no_playlist", True)

    cancel_requested = False
    worker_thread = threading.Thread(target=process_queue, args=(no_playlist,), daemon=True)
    worker_thread.start()

    return jsonify({"started": True})


@app.route("/api/cancel", methods=["POST"])
def api_cancel():
    global cancel_requested, current_process

    cancel_requested = True
    with process_lock:
        if current_process and current_process.poll() is None:
            try:
                current_process.terminate()
            except Exception:
                pass

    return jsonify({"cancelled": True})


@app.route("/api/status")
def api_status():
    with queue_lock:
        snapshot = [dict(i) for i in queue]
    concluidos = sum(1 for i in snapshot if i["status"] == "concluido")
    total = len(snapshot)
    running = worker_thread is not None and worker_thread.is_alive()
    return jsonify({
        "queue": snapshot,
        "concluidos": concluidos,
        "total": total,
        "running": running,
        "downloads_dir": get_downloads_dir() if get_ytdlp_dir() else "",
    })


@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    if not get_ytdlp_dir():
        return jsonify({"error": "Configure a pasta do yt-dlp antes de abrir a pasta."}), 400
    ensure_downloads_dir()
    try:
        os.startfile(get_downloads_dir())  # noqa: only valid on Windows
        return jsonify({"opened": True})
    except AttributeError:
        return jsonify({"error": "Abrir pasta só é suportado no Windows."}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    if get_ytdlp_dir():
        ensure_downloads_dir()
    app.run(host="127.0.0.1", port=5000, debug=False)
