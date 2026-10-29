#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import argparse
import subprocess
import plistlib
import hashlib
import zipfile
import tempfile
import shutil
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

def setup_args():
    parser = argparse.ArgumentParser(description="Extract IPA fingerprint to JSON")
    parser.add_argument("--input", required=True, help="Path to .ipa or .app directory")
    parser.add_argument("--output", required=True, help="Path to output fingerprint.json")
    return parser.parse_args()

def md5_file(filepath):
    h = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def get_dhash(image_path, hash_size=8):
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            img = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            diff = []
            for row in range(hash_size):
                for col in range(hash_size):
                    diff.append(pixels[row * (hash_size + 1) + col] > pixels[row * (hash_size + 1) + col + 1])
            decimal_value = sum(2**(i % 8) for i, val in enumerate(diff) if val)
            return "".join(hex(sum(2**(i % 8) for i, val in enumerate(diff[j:j+8]) if val))[2:].rjust(2, "0") for j in range(0, len(diff), 8))
    except Exception:
        return ""

class FingerprintExtractor:
    def __init__(self, target_path):
        self.target_path = target_path
        self.app_dir = ""
        self.temp_dir = None
        self.fp = {
            "meta": {},
            "binary": {"strings": [], "urls": [], "long_strings": [], "symbols": [], "swift_types": [], "frameworks": [], "opcode_histogram": {}, "call_graph_hash": ""},
            "extensions": [],
            "private_frameworks": [],
            "resources": {"assets_car_names": [], "assets_car_images": [], "app_icon_dhash": "", "lottie_files": [], "audio_files": [], "fonts": [], "loose_images": []},
            "metadata": {"info_plist": {"permissions": {}, "url_schemes": [], "bundle_id": "", "min_os": ""}, "entitlements": {}, "sdk_credentials": {}, "privacy_manifest": {}},
            "config_files": [],
            "localization": {}
        }

    def run(self):
        try:
            self.prepare_app_dir()
            self.extract_meta()
            main_exe = self.find_main_executable()
            if main_exe:
                self.extract_binary(main_exe, self.fp["binary"])
            self.extract_extensions()
            self.extract_private_frameworks()
            self.extract_resources()
            self.extract_metadata()
            self.extract_privacy_manifest()
            self.extract_config_files()
            self.extract_localization()
            return self.fp
        finally:
            self.cleanup()

    def prepare_app_dir(self):
        if self.target_path.endswith('.ipa'):
            self.temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(self.target_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            payload_dir = os.path.join(self.temp_dir, 'Payload')
            if not os.path.exists(payload_dir):
                raise Exception("Invalid IPA: No Payload directory")
            apps = [d for d in os.listdir(payload_dir) if d.endswith('.app')]
            if not apps:
                raise Exception("Invalid IPA: No .app directory found")
            self.app_dir = os.path.join(payload_dir, apps[0])
        elif self.target_path.endswith('.app'):
            self.app_dir = self.target_path
        else:
            raise Exception("Input must be .ipa or .app")

    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def find_main_executable(self):
        info_plist = os.path.join(self.app_dir, 'Info.plist')
        if os.path.exists(info_plist):
            try:
                with open(info_plist, 'rb') as f:
                    plist = plistlib.load(f)
                    exe = plist.get('CFBundleExecutable')
                    if exe:
                        return os.path.join(self.app_dir, exe)
            except: pass
        return None

    def extract_meta(self):
        self.fp["meta"]["extracted_at"] = datetime.now().isoformat()
        info_plist = os.path.join(self.app_dir, 'Info.plist')
        if os.path.exists(info_plist):
            try:
                with open(info_plist, 'rb') as f:
                    plist = plistlib.load(f)
                    self.fp["meta"]["app_name"] = plist.get('CFBundleDisplayName', plist.get('CFBundleName', 'Unknown'))
                    self.fp["meta"]["bundle_id"] = plist.get('CFBundleIdentifier', 'Unknown')
                    self.fp["meta"]["version"] = plist.get('CFBundleShortVersionString', 'Unknown')
            except: pass

    def extract_binary(self, exe_path, target_dict):
        # Strings & URLs
        try:
            res = subprocess.run(['strings', '-n', '6', exe_path], capture_output=True, text=True, timeout=30)
            all_strings = res.stdout.split('\n')
            for s in all_strings:
                s = s.strip()
                if not s: continue
                if s.startswith('http://') or s.startswith('https://'):
                    if s not in target_dict["urls"]: target_dict["urls"].append(s)
                elif len(s) > 30 and ' ' not in s: # Long strings without spaces (identifiers)
                    if s not in target_dict["long_strings"]: target_dict["long_strings"].append(s)
                else:
                    if len(s) < 100: # Exclude massive noise blocks
                        target_dict["strings"].append(s)
            target_dict["strings"] = list(set(target_dict["strings"]))
        except: pass

        # Symbols
        try:
            res = subprocess.run(['nm', '-gU', exe_path], capture_output=True, text=True, timeout=30)
            symbols = []
            for line in res.stdout.split('\n'):
                parts = line.split()
                if parts:
                    sym = parts[-1]
                    if sym.startswith('_OBJC_CLASS_$_'): sym = sym.replace('_OBJC_CLASS_$_', '')
                    if sym.startswith('_OBJC_METACLASS_$_'): sym = sym.replace('_OBJC_METACLASS_$_', '')
                    if not sym.startswith(('NS', 'UI', 'CG', 'CA', 'CF', '_', 'swift')):
                        symbols.append(sym)
            target_dict["symbols"] = list(set(symbols))
        except: pass

        # Frameworks
        try:
            res = subprocess.run(['otool', '-L', exe_path], capture_output=True, text=True, timeout=10)
            fws = [line.strip().split()[0].split('/')[-1] for line in res.stdout.split('\n') if '.framework' in line or '.dylib' in line]
            target_dict["frameworks"] = list(set(fws))
        except: pass

        self.extract_swift_types(exe_path, target_dict)
        self.extract_disassembly_features(exe_path, target_dict)

    def extract_swift_types(self, exe_path, target_dict):
        try:
            nm_res = subprocess.run(['nm', '-gU', exe_path], capture_output=True, text=True, timeout=30)
            mangled = set()
            for line in nm_res.stdout.split('\n'):
                parts = line.split()
                if not parts:
                    continue
                symbol = parts[-1].strip()
                symbol = symbol[1:] if symbol.startswith('_') else symbol
                if symbol.startswith('$s'):
                    mangled.add(symbol)
            if not mangled:
                return

            demangler = shutil.which("swift-demangle")
            cmd = [demangler] if demangler else ["xcrun", "swift-demangle"]
            demangle_input = "\n".join(sorted(mangled))
            demangled_res = subprocess.run(
                cmd,
                input=demangle_input,
                capture_output=True,
                text=True,
                timeout=40
            )
            if demangled_res.returncode != 0:
                return

            skip_tokens = {
                "Swift", "Optional", "Array", "Dictionary", "Set", "Int", "Int8", "Int16", "Int32", "Int64",
                "UInt", "UInt8", "UInt16", "UInt32", "UInt64", "Bool", "String", "Double", "Float", "Any",
                "Error", "Protocol", "Type", "Self", "Never", "Result"
            }
            types = set()
            for line in demangled_res.stdout.split('\n'):
                if not line.strip():
                    continue
                demangled = line.split(' ---> ')[-1].strip()
                subject = demangled.split(' ', 1)[0]
                for seg in re.split(r'[\.\<\>\(\)\[\],:]+', subject):
                    token = seg.strip()
                    if len(token) < 2:
                        continue
                    if not token[0].isupper():
                        continue
                    if token in skip_tokens:
                        continue
                    if token.startswith('_'):
                        continue
                    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', token):
                        continue
                    types.add(token)

            if types:
                target_dict["swift_types"] = sorted(types)
        except:
            pass

    def extract_opcode_from_line(self, line):
        if not line:
            return ""
        stripped = line.strip()
        if not stripped or stripped.endswith(':'):
            return ""
        m = re.search(r'^\s*[0-9a-fA-F]+\s+([A-Za-z][A-Za-z0-9\.]*)\b', line)
        if not m:
            m = re.search(r'^\s*[0-9a-fA-F]+\s+[0-9a-fA-F]{2}(?:\s+[0-9a-fA-F]{2})*\s+([A-Za-z][A-Za-z0-9\.]*)\b', line)
        if not m:
            return ""
        opcode = m.group(1).lower()
        if opcode in {"section", "(__text,__text)"}:
            return ""
        return opcode

    def extract_disassembly_features(self, exe_path, target_dict, max_instructions=100000):
        try:
            res = subprocess.run(['otool', '-tV', exe_path], capture_output=True, text=True, timeout=120)
            if res.returncode != 0 or not res.stdout:
                return

            opcode_counts = Counter()
            edge_counts = Counter()
            prev_opcode = ""
            total = 0
            branch_opcodes = {"b", "bl", "br", "blr", "cbz", "cbnz", "tbz", "tbnz"}

            for line in res.stdout.split('\n'):
                opcode = self.extract_opcode_from_line(line)
                if not opcode:
                    continue
                opcode_counts[opcode] += 1
                total += 1

                if prev_opcode:
                    edge_counts[f"{prev_opcode}>{opcode}"] += 1

                if opcode in branch_opcodes:
                    tail = line.split(opcode, 1)[-1] if opcode in line else line
                    target_match = re.search(r'(0x[0-9a-fA-F]+|_[A-Za-z0-9_.$]+)', tail)
                    if target_match:
                        edge_counts[f"{opcode}->{target_match.group(1)}"] += 1

                prev_opcode = opcode
                if total >= max_instructions:
                    break

            if total == 0:
                return

            target_dict["opcode_histogram"] = {
                k: round(v / total, 6) for k, v in sorted(opcode_counts.items(), key=lambda x: x[0])
            }

            hasher = hashlib.sha256()
            for edge_key in sorted(edge_counts.keys()):
                hasher.update(edge_key.encode('utf-8'))
                hasher.update(b':')
                hasher.update(str(edge_counts[edge_key]).encode('utf-8'))
                hasher.update(b';')
            target_dict["call_graph_hash"] = hasher.hexdigest()
        except:
            pass

    def extract_extensions(self):
        plugins_dir = os.path.join(self.app_dir, 'PlugIns')
        if not os.path.exists(plugins_dir): return
        for ext in os.listdir(plugins_dir):
            if ext.endswith('.appex'):
                ext_dir = os.path.join(plugins_dir, ext)
                info_plist = os.path.join(ext_dir, 'Info.plist')
                exe = None
                if os.path.exists(info_plist):
                    try:
                        with open(info_plist, 'rb') as f:
                            exe = plistlib.load(f).get('CFBundleExecutable')
                    except: pass
                if exe:
                    ext_data = {"name": ext, "strings": [], "urls": [], "long_strings": [], "symbols": [], "swift_types": [], "frameworks": [], "opcode_histogram": {}, "call_graph_hash": ""}
                    self.extract_binary(os.path.join(ext_dir, exe), ext_data)
                    self.fp["extensions"].append(ext_data)

    def extract_private_frameworks(self):
        fws_dir = os.path.join(self.app_dir, 'Frameworks')
        if not os.path.exists(fws_dir): return
        for fw in os.listdir(fws_dir):
            if fw.endswith('.framework') and not fw.startswith('Flutter'): # Skip known massive ones if needed
                fw_dir = os.path.join(fws_dir, fw)
                exe = fw.replace('.framework', '')
                exe_path = os.path.join(fw_dir, exe)
                if os.path.exists(exe_path):
                    fw_data = {"name": fw, "strings": [], "urls": [], "long_strings": [], "symbols": [], "swift_types": [], "frameworks": [], "opcode_histogram": {}, "call_graph_hash": ""}
                    self.extract_binary(exe_path, fw_data)
                    self.fp["private_frameworks"].append(fw_data)

    def extract_resources(self):
        # Assets.car
        assets_car = os.path.join(self.app_dir, 'Assets.car')
        if os.path.exists(assets_car):
            try:
                res = subprocess.run(['assetutil', '-I', assets_car], capture_output=True, text=True, timeout=30)
                data = json.loads(res.stdout)
                names = [item.get("Name") for item in data if isinstance(item, dict) and item.get("Name")]
                self.fp["resources"]["assets_car_names"] = list(set(names))
                
                cartool_path = shutil.which("cartool")
                if cartool_path:
                    out_dir = os.path.join(self.temp_dir if self.temp_dir else tempfile.mkdtemp(), "car_extracted")
                    os.makedirs(out_dir, exist_ok=True)
                    subprocess.run([cartool_path, assets_car, out_dir], capture_output=True, timeout=60)
                    for croot, _, cfiles in os.walk(out_dir):
                        for cf in cfiles:
                            if cf.endswith('.png'):
                                dh = get_dhash(os.path.join(croot, cf))
                                if dh:
                                    self.fp["resources"]["assets_car_images"].append({"name": cf, "dhash": dh})
            except: pass

        # App Icon Hash (find AppIcon in bundle)
        icon_paths = []
        for root, _, files in os.walk(self.app_dir):
            for f in files:
                if f.startswith('AppIcon') and f.endswith('.png'):
                    icon_paths.append(os.path.join(root, f))
        if icon_paths:
            # take the largest one
            largest_icon = max(icon_paths, key=os.path.getsize)
            self.fp["resources"]["app_icon_dhash"] = get_dhash(largest_icon)

        # Other resources
        for root, dirs, files in os.walk(self.app_dir):
            if 'Frameworks' in root or 'PlugIns' in root: continue
            for f in files:
                ext = f.lower().split('.')[-1]
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, self.app_dir)
                md5 = md5_file(path)
                
                if ext == 'json' and 'lottie' in f.lower():
                    self.fp["resources"]["lottie_files"].append({"path": rel_path, "md5": md5})
                elif ext in ['mp3', 'wav', 'm4a', 'caf']:
                    self.fp["resources"]["audio_files"].append({"path": rel_path, "md5": md5})
                elif ext in ['ttf', 'otf']:
                    self.fp["resources"]["fonts"].append({"path": rel_path, "md5": md5})
                elif ext in ['png', 'jpg', 'jpeg'] and not f.startswith('AppIcon'):
                    dh = get_dhash(path)
                    if dh:
                        self.fp["resources"]["loose_images"].append({"path": rel_path, "dhash": dh})

    def extract_metadata(self):
        info_plist = os.path.join(self.app_dir, 'Info.plist')
        if os.path.exists(info_plist):
            try:
                with open(info_plist, 'rb') as f:
                    plist = plistlib.load(f)
                    self.fp["metadata"]["info_plist"]["bundle_id"] = plist.get('CFBundleIdentifier', '')
                    self.fp["metadata"]["info_plist"]["min_os"] = plist.get('MinimumOSVersion', '')
                    
                    # Permissions
                    for k, v in plist.items():
                        if k.endswith('UsageDescription') and isinstance(v, str):
                            self.fp["metadata"]["info_plist"]["permissions"][k] = v
                            
                    # URL Schemes
                    schemes = []
                    for type_dict in plist.get('CFBundleURLTypes', []):
                        schemes.extend(type_dict.get('CFBundleURLSchemes', []))
                    self.fp["metadata"]["info_plist"]["url_schemes"] = schemes
                    
                    # SDK Credentials (common ones)
                    self.fp["metadata"]["sdk_credentials"]["facebook_app_id"] = plist.get('FacebookAppID')
                    self.fp["metadata"]["sdk_credentials"]["facebook_client_token"] = plist.get('FacebookClientToken')
            except: pass

        # Firebase / GoogleServices
        google_plist = os.path.join(self.app_dir, 'GoogleService-Info.plist')
        if os.path.exists(google_plist):
            try:
                with open(google_plist, 'rb') as f:
                    plist = plistlib.load(f)
                    self.fp["metadata"]["sdk_credentials"]["firebase_project_id"] = plist.get('PROJECT_ID')
                    self.fp["metadata"]["sdk_credentials"]["google_app_id"] = plist.get('GOOGLE_APP_ID')
                    self.fp["metadata"]["sdk_credentials"]["gcm_sender_id"] = plist.get('GCM_SENDER_ID')
            except: pass

        # Entitlements
        main_exe = self.find_main_executable()
        if main_exe:
            try:
                res = subprocess.run(['codesign', '-d', '--entitlements', ':-', main_exe], capture_output=True, text=True, timeout=10)
                if res.stdout.strip() and "<?xml" in res.stdout:
                    xml_start = res.stdout.find("<?xml")
                    ent_plist = plistlib.loads(res.stdout[xml_start:].encode('utf-8'))
                    self.fp["metadata"]["entitlements"]["app_groups"] = ent_plist.get('com.apple.security.application-groups', [])
                    self.fp["metadata"]["entitlements"]["keychain_groups"] = ent_plist.get('keychain-access-groups', [])
                    self.fp["metadata"]["entitlements"]["team_id"] = ent_plist.get('com.apple.developer.team-identifier')
            except: pass

    def collect_structural_keys(self, value, prefix="", out=None, limit=120):
        if out is None:
            out = set()
        if len(out) >= limit:
            return out

        if isinstance(value, dict):
            for k, v in value.items():
                key = f"{prefix}.{k}" if prefix else str(k)
                out.add(key)
                if len(out) >= limit:
                    break
                self.collect_structural_keys(v, key, out, limit)
        elif isinstance(value, list):
            for idx, item in enumerate(value[:5]):
                key = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
                out.add(key)
                if len(out) >= limit:
                    break
                self.collect_structural_keys(item, key, out, limit)
        return out

    def extract_privacy_manifest(self):
        manifests = []
        for root, _, files in os.walk(self.app_dir):
            for f in files:
                if f != "PrivacyInfo.xcprivacy":
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, 'rb') as pf:
                        data = plistlib.load(pf)
                    rel_path = os.path.relpath(path, self.app_dir)
                    entry = {"path": rel_path}
                    for k in (
                        "NSPrivacyTracking",
                        "NSPrivacyTrackingDomains",
                        "NSPrivacyCollectedDataTypes",
                        "NSPrivacyAccessedAPITypes"
                    ):
                        if k in data:
                            entry[k] = data.get(k)
                    manifests.append(entry)
                except:
                    pass
        if manifests:
            self.fp["metadata"]["privacy_manifest"] = {"manifests": manifests}

    def extract_config_files(self):
        target_exts = {".json", ".plist", ".yaml", ".yml", ".ini", ".conf", ".cfg", ".properties", ".env", ".data"}
        keyword_hits = ("config", "setting", "endpoint", "server", "env")
        collected = []

        for root, _, files in os.walk(self.app_dir):
            if "Frameworks" in root or "PlugIns" in root:
                continue
            for f in files:
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, self.app_dir)
                ext = os.path.splitext(f)[1].lower()
                lower_name = f.lower()

                if ext not in target_exts and not any(k in lower_name for k in keyword_hits):
                    continue
                if os.path.getsize(path) > 2 * 1024 * 1024:
                    continue

                entry = {"path": rel_path, "keys": [], "sample_strings": []}
                try:
                    if ext == ".json":
                        with open(path, 'r', encoding='utf-8', errors='ignore') as jf:
                            data = json.load(jf)
                        entry["keys"] = sorted(self.collect_structural_keys(data))
                    elif ext == ".plist":
                        with open(path, 'rb') as pf:
                            data = plistlib.load(pf)
                        entry["keys"] = sorted(self.collect_structural_keys(data))
                    elif ext == ".data":
                        res = subprocess.run(['strings', '-n', '6', path], capture_output=True, text=True, timeout=20)
                        candidates = []
                        for line in res.stdout.split('\n'):
                            s = line.strip()
                            if not s:
                                continue
                            if s.startswith('http://') or s.startswith('https://'):
                                candidates.append(s)
                            elif '=' in s and len(s) < 120:
                                candidates.append(s)
                            if len(candidates) >= 20:
                                break
                        entry["sample_strings"] = candidates
                    else:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as tf:
                            text = tf.read(200000)
                        keys = set(re.findall(r'^\s*([A-Za-z_][A-Za-z0-9_.-]{2,})\s*[:=]', text, flags=re.MULTILINE))
                        urls = re.findall(r'https?://[^\s"\'<>]+', text)
                        entry["keys"] = sorted(list(keys))[:120]
                        entry["sample_strings"] = urls[:20]
                except:
                    continue

                if entry["keys"] or entry["sample_strings"]:
                    collected.append(entry)

        self.fp["config_files"] = sorted(collected, key=lambda x: x["path"])

    def extract_localization(self):
        for root, dirs, files in os.walk(self.app_dir):
            if root.endswith('.lproj'):
                lang = os.path.basename(root).replace('.lproj', '')
                if lang not in self.fp["localization"]:
                    self.fp["localization"][lang] = {}
                for f in files:
                    if f == 'Localizable.strings':
                        path = os.path.join(root, f)
                        try:
                            # Use plutil to convert strings file to json
                            res = subprocess.run(['plutil', '-convert', 'json', '-o', '-', path], capture_output=True, timeout=10)
                            if res.returncode == 0:
                                data = json.loads(res.stdout)
                                self.fp["localization"][lang].update(data)
                        except: pass

if __name__ == "__main__":
    args = setup_args()
    print(f"Extracting fingerprint from {args.input}...")
    extractor = FingerprintExtractor(args.input)
    fp = extractor.run()
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(fp, f, ensure_ascii=False, indent=2)
    print(f"Extraction complete. Saved to {args.output}")
