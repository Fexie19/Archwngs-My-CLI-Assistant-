#!/usr/bin/env python3
"""
archwngs.py - Archwngs

Run: pip install groq rich ddgs requests openai || pip install -r requirements.txt
Run : .\venv\Scripts\Activate.ps1
Run: python archwngs.py
"""

import os
import sys
import json
import platform
import shutil
import subprocess
import fnmatch
import re
from pathlib import Path
from typing import Optional

os.system("cls")

# KONFIGURASI
API_KEY = ""
MODEL = ""


# IMPORTS
try:
    from groq import Groq
except ImportError:
    print("ERROR: groq belum terinstall. pip install groq rich. pip install -U ddgs")
    sys.exit(1)

try:
    from rich.console import Console
except ImportError:
    Console = None

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


# INIT

if not API_KEY:
    print("ERROR: API_KEY belum diset")
    sys.exit(1)

client = Groq(api_key=API_KEY)
console = Console() if Console else None

SYSTEM_PROMPT = """WAJIB berbahasa Indonesia. Kamu adalah Archwngs, asisten pribadi yang setia dan patuh kepada Dafa Jaya Priyatna (panggilan: Dafa).

Jika konteks/informasi tidak dipahami: gunakan search_internet WAJIB jadi aksi PERTAMA — TANPA teks pembuka apa pun 
(DILARANG: "tidak mengerti", "maksud Anda apa", "saya akan mencari..."). Jawab hanya setelah hasil pencarian didapat.
Jangan translate kecuali diminta. Jangan basa-basi: langsung, ringkas, tanpa intro/kesimpulan/saran tambahan. Jelaskan alasan hanya jika diminta. Setelah tools dipakai, laporkan hasil dalam 1-2 kalimat.
Jika mendeteksi ada bahasa selain Indonesia dan tanpa minta ditranslate, langsung gunakan search_internet.

TOOLS:
* search_files: cari file/folder; jika ketemu -> otomatis buka file manager (jangan buka jika belum ketemu)
* read_file: baca isi file teks
* open_file: buka file/folder dengan app default
* create_folder / create_file: buat folder/file baru
* delete_path: hapus file/folder (WAJIB konfirmasi "YA" dulu)
* edit_file: edit isi file
* open_app: buka aplikasi (cari di PATH; tidak ada -> error "tidak ditemukan di PATH"; app sudah jalan -> window baru dengan --new-window/-n)
* search_internet: cari & rangkum dari 5+ sumber berbeda, lalu berikan respon akhir hanya dengan 1 kalimat atau kesimpulan.

ATURAN:
1. Jangan pernah menebak path, selalu search_files dulu.
2. Task multi-step: panggil beberapa tools berurutan sesuai kebutuhan.
3. Utamakan tools daripada asumsi sendiri.
4. Sertakan path saat kerja dengan file.
5. Respons akhir: singkat & humoris.
6. Jangan membuat penjabaran atau list jika user tidak minta untuk DIJELASKAN.

FORMAT: * untuk list, 1.2.3 untuk langkah, **bold** untuk penekanan."""

BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".command", ".msi", ".app", ".scr", ".ps1", ".vbs", ".jar", ".dll", ".sys", ".com", ".pif", ".gadget"}
SKIP_DIR_NAMES = {"Windows", "Program Files", "Program Files (x86)", "ProgramData", "AppData", "$Recycle.Bin", "System Volume Information", "Library", "System", "private", "proc", "sys", "dev", "node_modules", "venv", ".venv", "__pycache__", ".cache", ".git"}

C_SKIP = "\033[90m"
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_ARCH = "\033[38;5;147m"
C_BASE = "\033[36m"

def p(text, end="\n"):
    sys.stdout.write(str(text) + end)
    sys.stdout.flush()

def open_in_file_manager(path):
    """Buka file manager di path yang ditentukan."""
    if not path:
        return False

    path = os.path.expanduser(str(path)).strip()
    if not path:
        return False

    # Get directory (if it's a file, open its parent)
    if os.path.isfile(path):
        path = os.path.dirname(path)

    if not path:
        return False

    try:
        if not os.path.isdir(path):
            return False

        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["open", path], check=True, timeout=5)
        else:
            subprocess.run(["xdg-open", path], check=True, timeout=5)
        return True
    except:
        return False

def print_banner():
    banner = """ \033[38;5;147m
    █████╗ ██████╗ ██████╗██╗  ██╗
   ██╔══██╗██╔══██╗██╔════╝██║  ██║
   ███████║██████╔╝██║     ███████║
   ██╔══██║██╔══██╗██║     ██╔══██║  
   ██║  ██║██║  ██║╚██████╗██║  ██║
   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ 
              \033[36m██╗    ██╗███╗   ██╗ ██████╗ ███████╗\033[0m
              \033[36m██║    ██║████╗  ██║██╔════╝ ██╔════╝\033[0m
              \033[36m██║ █╗ ██║██╔██╗ ██║██║  ███╗███████╗\033[0m
              \033[36m██║███╗██║██║╚██╗██║██║   ██║╚════██║\033[0m
              \033[36m╚███╔███╔╝██║ ╚████║╚██████╔╝███████║\033[0m
              \033[36m ╚══╝╚══╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝\033[0m

          \033[36mArchwngs by fexie
                    
                    Loyalty is everything.\033[0m      
"""
    sys.stdout.write(banner)
    sys.stdout.flush()

def show_banner_and_prompt():
    if console:
        console.clear()
    else:
        p("\n" * 20)
    print_banner()
    p(f"\n{C_SKIP}Ketik 'exit' atau 'quit' untuk keluar.{C_RESET}")
    p("")

def render_transcript(history):
    show_banner_and_prompt()
    for line in history:
        if line.startswith("Archwngs:"):
            msg = line[len("Archwngs:"):]
            p(f"{C_BOLD}\033[36mArchwngs:\033[0m{msg}")
        elif line.startswith("[EXEC]") or line.startswith("[TOOL]") or line.startswith("[SEARCH]"):
            p(f"{C_SKIP}{line}{C_RESET}")
        elif line.startswith("[CONFIRM]"):
            p(f"{C_BOLD}\033[33m{line}\033[0m")
        elif line.startswith("[ERROR]"):
            p(f"\033[31m{line}\033[0m")
        elif line.startswith("[SUCCESS]"):
            p(f"\033[32m{line}\033[0m")
        else:
            p(line)

def search_files(query, root_dir=None, max_results=50):
    root_dir = os.path.expanduser(root_dir) if root_dir else os.path.expanduser("~")
    if not os.path.isdir(root_dir):
        return f"ERROR: Folder '{root_dir}' tidak ditemukan.", None

    matches = []
    first_folder_path = None
    first_file_path = None
    pattern = f"*{query}*".lower()

    try:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIR_NAMES]

            for name in dirnames:
                if fnmatch.fnmatch(name.lower(), pattern):
                    full_path = os.path.join(dirpath, name)
                    matches.append(f"[FOLDER] {full_path}")
                    if first_folder_path is None:
                        first_folder_path = dirpath
                    if len(matches) >= max_results:
                        return "\n".join(matches), first_folder_path

            for name in filenames:
                if fnmatch.fnmatch(name.lower(), pattern):
                    full_path = os.path.join(dirpath, name)
                    matches.append(full_path)
                    if first_file_path is None:
                        first_file_path = os.path.dirname(full_path)
                    if len(matches) >= max_results:
                        return "\n".join(matches), first_file_path or first_folder_path
    except PermissionError:
        return "WARNING: Beberapa folder tidak dapat diakses.", None
    except Exception as e:
        return f"ERROR: {str(e)}", None

    # Return both results and the best path to open
    best_path = first_file_path or first_folder_path
    if matches:
        return "\n".join(matches), best_path
    return "Tidak ada file atau folder yang cocok.", None

def read_file(path, max_chars=8000):
    path = os.path.expanduser(path).replace("[FOLDER] ", "").strip()
    if not path:
        return "ERROR: Path kosong."
    if not os.path.isfile(path):
        return f"ERROR: '{path}' bukan file valid."

    ext = os.path.splitext(path)[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        return f"ERROR: File executable tidak aman dibaca."

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars)
        suffix = "\n\n[...dipotong...]" if len(content) >= max_chars else ""
        return content + suffix
    except PermissionError:
        return f"ERROR: Tidak punya permission membaca '{path}'."
    except Exception as e:
        return f"ERROR: {str(e)}"

def open_file(path):
    path = os.path.expanduser(path).replace("[FOLDER] ", "").strip()
    if not path:
        return "ERROR: Path kosong."
    if not os.path.exists(path):
        return f"ERROR: '{path}' tidak ditemukan."

    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        if ext in BLOCKED_EXTENSIONS:
            return f"ERROR: Executable tidak aman dibuka."

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["open", path], check=True, timeout=10)
        else:
            subprocess.run(["xdg-open", path], check=True, timeout=10)
        return f"SUCCESS: Berhasil membuka '{path}'."
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout saat membuka."
    except Exception as e:
        return f"ERROR: {str(e)}"

def create_folder(path):
    if not path:
        return "ERROR: Path kosong."
    path = os.path.expanduser(path)
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"SUCCESS: Folder dibuat: {path}"
    except PermissionError:
        return f"ERROR: Tidak punya permission membuat folder di '{path}'."
    except Exception as e:
        return f"ERROR: {str(e)}"

def create_file(path, content=""):
    if not path:
        return "ERROR: Path kosong."
    path = os.path.expanduser(path)
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return f"SUCCESS: File dibuat: {path}"
    except PermissionError:
        return f"ERROR: Tidak punya permission di '{path}'."
    except Exception as e:
        return f"ERROR: {str(e)}"

def delete_path(path):
    path = os.path.expanduser(path).strip()
    if not path:
        return "ERROR: Path kosong."

    target = Path(path)
    if not target.exists():
        return f"ERROR: '{path}' tidak ditemukan."

    target_type = "folder" if target.is_dir() else "file"
    confirm_msg = f"\n[CONFIRM] Konfirmasi Penghapusan:\n"
    confirm_msg += f"{'='*50}\n"
    confirm_msg += f"  Type: {target_type.upper()}\n"
    confirm_msg += f"  Path: {path}\n"
    if target.is_dir():
        try:
            item_count = sum(1 for _ in target.rglob("*"))
            confirm_msg += f"  Isi: {item_count} item(s)\n"
        except:
            pass
    confirm_msg += f"{'='*50}\n"
    confirm_msg += f"  Ketik 'YA' untuk konfirmasi: "

    p(confirm_msg)

    try:
        user_confirm = input().strip().upper()
    except (EOFError, KeyboardInterrupt):
        p(f"{C_SKIP}[dibatalkan]{C_RESET}")
        return "INFO: Penghapusan dibatalkan."

    if user_confirm != "YA":
        return f"INFO: Penghapusan dibatalkan. '{path}' tetap aman."

    try:
        if target.is_dir():
            shutil.rmtree(target)
            return f"SUCCESS: Folder dihapus: {path}"
        else:
            target.unlink()
            return f"SUCCESS: File dihapus: {path}"
    except PermissionError:
        return f"ERROR: Tidak punya permission menghapus '{path}'."
    except Exception as e:
        return f"ERROR: {str(e)}"

def edit_file(path, content):
    if not path:
        return "ERROR: Path kosong."
    path = os.path.expanduser(path).strip()

    try:
        target = Path(path)
        if not target.exists():
            return f"ERROR: '{path}' tidak ditemukan."
        if target.is_dir():
            return f"ERROR: '{path}' adalah folder."

        ext = os.path.splitext(path)[1].lower()
        if ext in BLOCKED_EXTENSIONS:
            return f"ERROR: Executable tidak aman diedit."

        target.write_text(content, encoding="utf-8")
        return f"SUCCESS: File diubah: {path}"
    except PermissionError:
        return f"ERROR: Tidak punya permission edit '{path}'."
    except Exception as e:
        return f"ERROR: {str(e)}"

def find_app_executable(app_name):
    """Cari executable aplikasi di sistem."""
    app_name_lower = app_name.lower()

    # Mapping nama aplikasi ke command/nama executable
    app_mappings = {
        "chrome": ["google-chrome", "chrome", "chromium", "chromium-browser"],
        "firefox": ["firefox", "mozilla-firefox"],
        "edge": ["msedge", "microsoft-edge"],
        "vscode": ["code", "code.cmd", "code-insiders", "code-insiders.cmd"],
        "code": ["code", "code.cmd", "code-insiders", "code-insiders.cmd"],
        "notepad": ["notepad", "notepad++", "notepad++.exe"],
        "word": ["winword", "microsoft-word"],
        "excel": ["excel", "microsoft-excel"],
        "powerpoint": ["powerpnt", "microsoft-powerpoint"],
        "spotify": ["spotify"],
        "discord": ["discord"],
        "telegram": ["telegram-desktop", "telegram"],
        "whatsapp": ["whatsapp"],
        "zoom": ["zoom"],
        "teams": ["teams"],
        "slack": ["slack"],
        "git": ["git-bash", "bash"],
        "terminal": ["cmd", "powershell", "terminal"],
        "explorer": ["explorer", "explorer.exe"],
        "file explorer": ["explorer", "explorer.exe"],
        "putty": ["putty", "putty.exe"],
        "filezilla": ["filezilla"],
        "winrar": ["winrar", "winrar.exe"],
        "7zip": ["7z", "7zFM", "7zFM.exe"],
        "obsidian": ["obsidian"],
        "obs": ["obs64", "obs32", "obs"],
        "vlc": ["vlc", "vlc.exe"],
        "gimp": ["gimp", "gimp-2.10"],
        "inkscape": ["inkscape"],
        "blender": ["blender"],
        "unity": ["unity", "unity-editor"],
        "unreal": ["unreal-editor"],
        "steam": ["steam"],
        "epic": ["epicgameslauncher"],
        "gog": ["goggalaxy"],
        "dropbox": ["dropbox"],
        "onedrive": ["onedrive"],
        "photoshop": ["photoshop"],
        "illustrator": ["illustrator"],
        "premiere": ["premiere", "adobe-premiere-pro"],
        "after effects": ["afterfx", "aftereffects"],
        "audacity": ["audacity"],
        "vscodium": ["codium", "codium.exe"],
        "brave": ["brave", "brave-browser"],
        "opera": ["opera", "opera-browser"],
        "browsers": ["chrome", "firefox", "edge", "brave"],
    }

    # Get list of candidates based on mapping
    candidates = []

    # Exact match for mapped names (use word boundary check)
    mapped = False
    for key, names in app_mappings.items():
        # Check if the app name exactly matches the key or is contained within
        # but be more strict to avoid partial matches
        if app_name_lower == key or app_name_lower.startswith(key + " ") or app_name_lower.endswith(" " + key):
            candidates.extend(names)
            mapped = True
            break
        # Also check for key being in app_name as whole word
        if key.replace(" ", "") in app_name_lower.replace(" ", "") and len(key) > 3:
            candidates.extend(names)
            mapped = True
            break

    # If no candidates from mapping, try exact or very close match
    if not candidates:
        # Only use the exact name as candidate
        candidates.append(app_name_lower)

    # Windows-specific common paths - only add if app was matched in mapping
    if sys.platform.startswith("win"):
        if mapped:
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            programfiles = os.environ.get("PROGRAMFILES", "")
            programfiles_x86 = os.environ.get("PROGRAMFILES(X86)", "")

            common_paths = [
                os.path.join(local_appdata, "Programs", "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(local_appdata, "Programs", "Microsoft VS Code", "bin", "code.cmd"),
                os.path.join(local_appdata, "Programs", "Microsoft VS Code Insiders", "bin", "code-insiders.cmd"),
                os.path.join(local_appdata, "Programs", "Microsoft VS Code", "bin", "code"),
                os.path.join(programfiles, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(programfiles, "Mozilla Firefox", "firefox.exe"),
                os.path.join(programfiles, "Microsoft Edge", "Application", "msedge.exe"),
                os.path.join(programfiles, "Microsoft VS Code", "Code.exe"),
                os.path.join(programfiles, "VideoLAN", "VLC", "vlc.exe"),
                os.path.join(programfiles, "Notepad++", "notepad++.exe"),
                os.path.join(local_appdata, "Programs", "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            ]
            candidates.extend(common_paths)

        # Search in PATH
        path_env = os.environ.get("PATH", "")
        for path_dir in path_env.split(os.pathsep):
            for c in candidates:
                exe_path = os.path.join(path_dir, c)
                for ext in ["", ".exe", ".cmd", ".bat"]:
                    full_path = exe_path + ext
                    if os.path.exists(full_path):
                        return full_path
    else:
        # Unix-like systems
        for c in candidates:
            found = shutil.which(c)
            if found:
                return found

    # Try direct which with original name only if no mapping match
    if not mapped:
        found = shutil.which(app_name_lower)
        if found:
            return found

    return None

def open_app(app, path=None):
    """Buka aplikasi apapun."""
    app = app.strip()
    if not app:
        return "ERROR: Nama aplikasi kosong.", False

    p(f"[EXEC] Mencari aplikasi: {app}")

    exe = find_app_executable(app)
    app_opened = False

    # Apps that need --new-window flag to open in new window
    NEW_WINDOW_APPS = {
        'chrome': '--new-window',
        'firefox': '--new-window',
        'edge': '--new-window',
        'msedge': '--new-window',
        'brave': '--new-window',
        'chromium': '--new-window',
        'vscode': '--new-window',
        'code': '--new-window',
        'vscodium': '--new-window',
    }

    if exe:
        try:
            target_path = str(Path(path).expanduser()) if path else None

            if sys.platform.startswith("win"):
                # Build command with new window flag
                cmd = [exe]
                app_key = app.lower().replace('microsoft ', '').replace('google ', '')

                # Add new window flag for specific apps
                if app_key in NEW_WINDOW_APPS:
                    cmd.append(NEW_WINDOW_APPS[app_key])

                if target_path:
                    cmd.append(target_path)

                if exe.endswith(".cmd"):
                    cmdline = subprocess.list2cmdline(cmd)
                    subprocess.Popen(["cmd", "/c", cmdline], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(cmd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                app_opened = True
            else:
                # Unix-like systems
                cmd = [exe]
                app_key = app.lower()

                if app_key in NEW_WINDOW_APPS:
                    cmd.append(NEW_WINDOW_APPS[app_key])

                if target_path:
                    cmd.append(target_path)

                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                app_opened = True

        except PermissionError:
            return f"ERROR: Tidak punya permission menjalankan '{app}'.", False
        except Exception as e:
            return f"ERROR: Gagal membuka {app}: {str(e)}", False
    else:
        # exe not found in PATH or common locations - this is a definite failure
        return f"ERROR: Aplikasi '{app}' tidak ditemukan di PATH sistem.", False

    if app_opened:
        return f"SUCCESS: {app} dibuka" + (f" di {path}" if path else ""), True
    else:
        return f"ERROR: Gagal membuka {app}.", False

def search_internet(query, max_results=10):
    """Cari informasi di internet menggunakan DuckDuckGo."""
    if not HAS_DDGS:
        return "ERROR: duckduckgo-search belum terinstall. Jalankan: pip install duckduckgo-search"

    if not query or not query.strip():
        return "ERROR: Query pencarian kosong."

    p(f"[SEARCH] Mencari: {query}")

    results = []
    sources = []

    try:
        with DDGS() as ddgs:
            # News search
            try:
                for r in ddgs.news(query, max_results=max_results):
                    if r.get("url"):
                        results.append({
                            "title": r.get("title", "Tanpa judul"),
                            "url": r.get("url", ""),
                            "body": r.get("body", r.get("description", ""))[:300],
                            "source": r.get("source", "Unknown")
                        })
            except:
                pass

            # If no news, try general search
            if len(results) < 3:
                try:
                    for i, r in enumerate(ddgs.text(query, max_results=max_results)):
                        if r.get("href"):
                            # Check if already added
                            if not any(x["url"] == r["href"] for x in results):
                                results.append({
                                    "title": r.get("title", "Tanpa judul"),
                                    "url": r.get("href", ""),
                                    "body": r.get("body", r.get("description", ""))[:300],
                                    "source": r.get("source", r.get("hostname", "Unknown"))
                                })
                        if len(results) >= max_results:
                            break
                except:
                    pass

    except Exception as e:
        return f"ERROR: Gagal mencari: {str(e)}"

    if not results:
        return "INFO: Tidak ada hasil pencarian ditemukan."

    # Build formatted response
    response = f"[SEARCH] {query}\n\n"

    for i, r in enumerate(results, 1):
        response += C_ARCH +f"※ {r['title']}"
        if r.get("body"):
            response += C_BASE + f"   {r['body'][:200]}...\n" if len(r.get("body", "")) > 200 else f"   {r['body']}\n"
        response += C_BASE + f"   {C_SKIP}Source: {r['source']} | {r['url']}{C_RESET}\n\n"

    return response

import json

with open("tools.json", "r", encoding="utf-8") as f:
    TOOLS = json.load(f)

def execute_tool(tool_name, tool_input):
    """Execute a tool and return the result."""
    if tool_name == "search_files":
        p(f"\n[TOOL] search_files: {tool_input.get('query', '')}")
        result, open_path = search_files(tool_input.get("query", ""), tool_input.get("root_dir"))
        # Auto-open file manager if results found
        if open_path and not result.startswith("ERROR") and not result.startswith("WARNING"):
            p(f"\n[TOOL] Membuka file manager di: {open_path}")
            open_in_file_manager(open_path)
        return result
    elif tool_name == "read_file":
        p(f"\n[TOOL] read_file: {tool_input.get('path', '')}")
        return read_file(tool_input.get("path", ""), tool_input.get("max_chars", 8000))
    elif tool_name == "open_file":
        p(f"\n[TOOL] open_file: {tool_input.get('path', '')}")
        return open_file(tool_input.get("path", ""))
    elif tool_name == "create_folder":
        p(f"\n[TOOL] create_folder: {tool_input.get('path', '')}")
        return create_folder(tool_input.get("path", ""))
    elif tool_name == "create_file":
        p(f"\n[TOOL] create_file: {tool_input.get('path', '')}")
        return create_file(tool_input.get("path", ""), tool_input.get("content", ""))
    elif tool_name == "delete_path":
        p(f"\n[TOOL] delete_path: {tool_input.get('path', '')}")
        return delete_path(tool_input.get("path", ""))
    elif tool_name == "edit_file":
        p(f"\n[TOOL] edit_file: {tool_input.get('path', '')}")
        return edit_file(tool_input.get("path", ""), tool_input.get("content", ""))
    elif tool_name == "open_app":
        p(f"\n[TOOL] open_app: {tool_input.get('app', '')} (path: {tool_input.get('path', 'none')})")
        result, _ = open_app(tool_input.get("app", ""), tool_input.get("path"))
        return result
    elif tool_name == "search_internet":
        p(f"\n[TOOL] search_internet: {tool_input.get('query', '')}")
        return search_internet(tool_input.get("query", ""), tool_input.get("max_results", 10))
    else:
        return f"ERROR: Tool '{tool_name}' tidak dikenal."

def agent_loop(messages, history):
    """Agent loop: call model & execute tools until done."""
    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.5
            )
        except Exception as e:
            return messages, f"ERROR: Gagal menghubungi API: {str(e)}"

        msg = response.choices[0].message
        assistant_entry = {"role": "assistant", "content": msg.content or ""}

        if msg.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]

        messages.append(assistant_entry)

        if msg.content:
            history.append(f"\n" + C_ARCH + "◉ Archwngs:" + C_RESET + f" {msg.content}\n")

        if not msg.tool_calls:
            break

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = execute_tool(tc.function.name, args)
            result_preview = result[:200] + "..." if len(result) > 200 else result
            history.append(f"[TOOL] {tc.function.name} -> {result_preview}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return messages, None

def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    history = []
    render_transcript(history)

    while True:
        try:
            console.rule(style="white")
            user_input = input("❯ ").strip()
            
        except (EOFError, KeyboardInterrupt):
            history.append(f"\n" + C_ARCH + "◉ Archwngs:" + C_RESET + "Sampai jumpa! Aku selalu siap kalau kamu butuh aku lagi.")
            render_transcript(history)
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            history.append(f"\n" + C_ARCH + "◉ Archwngs:" + C_RESET + "Sampai jumpa! Aku selalu siap kalau kamu butuh aku lagi.")
            render_transcript(history)
            console.rule(style="sky_blue3")
            break

        history.append(f"❯ {user_input}\n")
        messages.append({"role": "user", "content": user_input})

        try:
            messages, error = agent_loop(messages, history)
            if error:
                history.append(error)
        except Exception as e:
            history.append(f"ERROR: {str(e)}")

        render_transcript(history)

if __name__ == "__main__":
    main()
    
