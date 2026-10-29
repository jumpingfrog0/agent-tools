#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import argparse
import os
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

SYSTEM_API_PREFIXES = (
    "NS", "UI", "CF", "CG", "CA", "AV", "AS", "OS_", "dispatch_", "GPB",
    "URLSession", "URLProtocol", "application:", "tableView:", "collectionView:",
    "navigationController:", "webView:", "setNeeds", "layoutSubviews"
)

LOW_SIGNAL_LIBRARY_MARKERS = (
    "MessageSetExtension", "CodedOutputStream", "CodedInputStream", "GPBUnknownField",
    "Protobuf", "protobuf", "yy_model", "zipArchive", "sd_setImage", "TBXML"
)

def setup_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", required=True, help="Fingerprint A json")
    parser.add_argument("--b", required=True, help="Fingerprint B json")
    parser.add_argument("--noise", required=False, help="Noise library json")
    parser.add_argument("--output", required=True, help="Filtered common json")
    return parser.parse_args()

def load_json(path):
    if not path or not os.path.exists(path): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def hamming_distance(h1, h2):
    if not h1 or not h2 or len(h1) != len(h2): return 999
    return bin(int(h1, 16) ^ int(h2, 16)).count("1")

def cos_sim(d1, d2):
    if not d1 or not d2: return 0.0
    keys = set(d1.keys()) | set(d2.keys())
    dot = sum(d1.get(k, 0) * d2.get(k, 0) for k in keys)
    n1 = sum(v*v for v in d1.values())**0.5
    n2 = sum(v*v for v in d2.values())**0.5
    return dot / (n1 * n2) if n1*n2 > 0 else 0.0

def build_flat_noise_set(noise_data):
    s = set()
    for v in noise_data.values():
        if isinstance(v, list): s.update(v)
    return s

def normalize_url(url):
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ""
    host = parsed.netloc.lower()
    path = parsed.path or ""
    if path == "/":
        path = ""
    elif path.endswith('/') and len(path) > 1:
        path = path[:-1]
    normalized = f"{parsed.scheme}://{host}{path}"
    if parsed.query:
        normalized = f"{normalized}?{parsed.query}"
    return normalized

def meaningful_url(url):
    if not url:
        return False
    if url in {"http://", "https://"}:
        return False
    parsed = urlparse(url)
    if not parsed.netloc:
        return False
    if parsed.netloc in {"%@", "%@:%@"}:
        return False
    if "%@" in parsed.netloc:
        return False
    return True

def is_type_encoding_noise(s):
    if not isinstance(s, str):
        return True
    if len(s) < 4:
        return True
    if re.search(r'@\d+@0:8', s):
        return True
    if s.startswith(('T@', 'T{', '^{', '@"', '#')):
        return True
    if s.startswith(('T', 'B', 'v', 'q', 'Q', 'i')) and ',V_' in s and ',' in s:
        return True
    if s.startswith(("T@", "T{", "^{", "v", "B", "q", "Q", "i")) and re.search(r'@\d+|:\d+|\{.*=.*\}', s):
        return True
    if re.match(r'^[\@\^\{\}\(\)\[\]=:";,\?\-+*/%&<>\w\d\.]+$', s) and re.search(r'[_\{\}\^=@"]', s) and re.search(r'\d', s):
        return True
    if re.search(r'^{?[A-Za-z0-9_]+=\{?[A-Za-z0-9_=]+\}?}$', s):
        return True
    return False

def normalize_text(s):
    if not isinstance(s, str):
        return ""
    return " ".join(s.strip().split())

def canonicalize_permission_text(s):
    text = normalize_text(s).lower()
    if not text:
        return ""
    text = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '', text)
    return text

def permission_similarity(a, b):
    ta = canonicalize_permission_text(a)
    tb = canonicalize_permission_text(b)
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0
    ratio = SequenceMatcher(None, ta, tb).ratio()
    if ta in tb or tb in ta:
        contain = min(len(ta), len(tb)) / max(len(ta), len(tb))
        return max(ratio, contain)
    return ratio

def is_system_api_like(s):
    if not isinstance(s, str):
        return False
    if s.startswith(SYSTEM_API_PREFIXES):
        return True
    return any(marker in s for marker in LOW_SIGNAL_LIBRARY_MARKERS)

def is_meaningful_common_string(s):
    if not isinstance(s, str):
        return False
    text = s.strip()
    if not text:
        return False
    if len(text) < 4:
        return False
    alnum_count = sum(1 for c in text if c.isalnum())
    if alnum_count / len(text) < 0.45:
        return False
    if text.lower() in {"void", "id", "class", "sel", "imp", "bool", "char", "int", "float", "double", "array", "dictionary", "self"}:
        return False
    if is_type_encoding_noise(text):
        return False
    return True

def get_origin_map(fp):
    m = {}
    for s in set(fp.get("binary", {}).get("strings", [])):
        m.setdefault(s, set()).add("MainBinary")
        
    for fw in fp.get("private_frameworks", []):
        name = fw.get("name", "UnknownFW").replace('.framework', '')
        for s in set(fw.get("strings", [])):
            m.setdefault(s, set()).add(f"FW:{name}")
            
    for ext in fp.get("extensions", []):
        name = ext.get("name", "UnknownExt").replace('.appex', '')
        for s in set(ext.get("strings", [])):
            m.setdefault(s, set()).add(f"Ext:{name}")
            
    return m

def compare(fa, fb, noise_set):
    res = {
        "high_risk": {},
        "medium_risk": {},
        "pending_ai_review": {},
        "meta": {"app_a": fa.get("meta", {}).get("app_name", "A"), "app_b": fb.get("meta", {}).get("app_name", "B")}
    }

    # High Risk
    try:
        t_a = fa.get("metadata", {}).get("entitlements", {}).get("team_id")
        t_b = fb.get("metadata", {}).get("entitlements", {}).get("team_id")
        res["high_risk"]["same_team_id"] = bool(t_a and t_b and t_a == t_b)

        cred_a = set(k for k,v in fa.get("metadata", {}).get("sdk_credentials", {}).items() if v)
        cred_b = set(k for k,v in fb.get("metadata", {}).get("sdk_credentials", {}).items() if v)
        shared_cred = []
        for k in (cred_a & cred_b):
            if fa["metadata"]["sdk_credentials"][k] == fb["metadata"]["sdk_credentials"][k]:
                shared_cred.append(k)
        res["high_risk"]["shared_sdk_credentials"] = shared_cred

        # URLs and Long Strings
        u_a = set(filter(meaningful_url, (normalize_url(u) for u in fa.get("binary", {}).get("urls", []))))
        u_b = set(filter(meaningful_url, (normalize_url(u) for u in fb.get("binary", {}).get("urls", []))))
        res["high_risk"]["common_urls"] = sorted(list(u_a & u_b))

        ls_a = set(fa.get("binary", {}).get("long_strings", []))
        ls_b = set(fb.get("binary", {}).get("long_strings", []))
        common_ls = ls_a & ls_b
        filtered_ls = [s for s in (common_ls - noise_set) if is_meaningful_common_string(s)]
        business_ls = [s for s in filtered_ls if not is_system_api_like(s)]
        system_ls = [s for s in filtered_ls if is_system_api_like(s)]
        res["high_risk"]["common_long_strings"] = sorted(business_ls)
        res["medium_risk"]["system_common_long_strings"] = sorted(system_ls)

        # Icon
        icon_a = fa.get("resources", {}).get("app_icon_dhash")
        icon_b = fb.get("resources", {}).get("app_icon_dhash")
        dist = hamming_distance(icon_a, icon_b)
        res["high_risk"]["similar_app_icon"] = dist <= 10
        res["high_risk"]["icon_hamming_distance"] = dist

        # Entitlements App Groups & Keychain Groups
        ag_a = set(fa.get("metadata", {}).get("entitlements", {}).get("app_groups", []))
        ag_b = set(fb.get("metadata", {}).get("entitlements", {}).get("app_groups", []))
        res["high_risk"]["shared_app_groups"] = list(ag_a & ag_b)

        kg_a = set(fa.get("metadata", {}).get("entitlements", {}).get("keychain_groups", []))
        kg_b = set(fb.get("metadata", {}).get("entitlements", {}).get("keychain_groups", []))
        res["high_risk"]["shared_keychain_groups"] = list(kg_a & kg_b)

        # Info.plist URL Schemes & Permissions
        us_a = set(fa.get("metadata", {}).get("info_plist", {}).get("url_schemes", []))
        us_b = set(fb.get("metadata", {}).get("info_plist", {}).get("url_schemes", []))
        res["high_risk"]["common_url_schemes"] = list(us_a & us_b)

        perm_map_a = fa.get("metadata", {}).get("info_plist", {}).get("permissions", {})
        perm_map_b = fb.get("metadata", {}).get("info_plist", {}).get("permissions", {})
        perm_a = set(perm_map_a.keys())
        perm_b = set(perm_map_b.keys())
        common_perm_keys = sorted(list(perm_a & perm_b))
        res["high_risk"]["common_permission_keys"] = common_perm_keys
        shared_permission_descriptions = []
        similar_permission_descriptions = []
        for k in common_perm_keys:
            va = normalize_text(perm_map_a.get(k, ""))
            vb = normalize_text(perm_map_b.get(k, ""))
            if va and va == vb:
                shared_permission_descriptions.append({"key": k, "value": va})
                continue
            sim = permission_similarity(va, vb)
            if sim >= 0.92:
                similar_permission_descriptions.append({
                    "key": k,
                    "value_a": va,
                    "value_b": vb,
                    "similarity": round(sim, 4)
                })
        res["high_risk"]["shared_permission_descriptions"] = shared_permission_descriptions
        res["high_risk"]["similar_permission_descriptions"] = similar_permission_descriptions
        
        # Swift Types
        sw_a = set(fa.get("binary", {}).get("swift_types", []))
        sw_b = set(fb.get("binary", {}).get("swift_types", []))
        if sw_a and sw_b:
             res["high_risk"]["common_swift_types"] = list(sw_a & sw_b)

    except Exception as e: pass

    # Medium Risk
    try:
        sym_a = set(fa.get("binary", {}).get("symbols", []))
        sym_b = set(fb.get("binary", {}).get("symbols", []))
        res["medium_risk"]["common_symbols"] = list(sym_a & sym_b)

        car_a = set(fa.get("resources", {}).get("assets_car_names", []))
        car_b = set(fb.get("resources", {}).get("assets_car_names", []))
        res["medium_risk"]["common_assets_car_names"] = list(car_a & car_b)

        op_a = fa.get("binary", {}).get("opcode_histogram", {})
        op_b = fb.get("binary", {}).get("opcode_histogram", {})
        res["medium_risk"]["opcode_similarity"] = cos_sim(op_a, op_b)
        
        # Audio / Lottie
        lottie_a = set(item["md5"] for item in fa.get("resources", {}).get("lottie_files", []))
        lottie_b = set(item["md5"] for item in fb.get("resources", {}).get("lottie_files", []))
        res["medium_risk"]["common_lottie_md5s"] = list(lottie_a & lottie_b)
        
        audio_a = set(item["md5"] for item in fa.get("resources", {}).get("audio_files", []))
        audio_b = set(item["md5"] for item in fb.get("resources", {}).get("audio_files", []))
        res["medium_risk"]["common_audio_md5s"] = list(audio_a & audio_b)

        # Frameworks Overlap
        fw_a = set(fa.get("binary", {}).get("frameworks", []))
        fw_b = set(fb.get("binary", {}).get("frameworks", []))
        common_fws = fw_a & fw_b
        union_fws = fw_a | fw_b
        fw_sim = len(common_fws) / len(union_fws) if union_fws else 0.0
        res["medium_risk"]["framework_overlap"] = {
             "similarity_percentage": round(fw_sim * 100, 2),
             "shared_frameworks": list(common_fws)
        }
        
        # Localization Keys
        loc_keys_a = set()
        for k, v in fa.get("localization", {}).items():
             loc_keys_a.update(v.keys())
        loc_keys_b = set()
        for k, v in fb.get("localization", {}).items():
             loc_keys_b.update(v.keys())
        res["medium_risk"]["common_localization_keys"] = list(loc_keys_a & loc_keys_b)
        
        # Loose Images
        li_a = fa.get("resources", {}).get("loose_images", [])
        li_b = fb.get("resources", {}).get("loose_images", [])
        shared_li = []
        for img_a in li_a:
             for img_b in li_b:
                  if hamming_distance(img_a.get("dhash", ""), img_b.get("dhash", "")) <= 10:
                       shared_li.append({"a": img_a.get("path"), "b": img_b.get("path")})
                       break
        res["medium_risk"]["similar_loose_images"] = shared_li
        
        # Assets.car Images (if extracted via cartool)
        aci_a = fa.get("resources", {}).get("assets_car_images", [])
        aci_b = fb.get("resources", {}).get("assets_car_images", [])
        shared_aci = []
        for img_a in aci_a:
             for img_b in aci_b:
                  if hamming_distance(img_a.get("dhash", ""), img_b.get("dhash", "")) <= 10:
                       shared_aci.append({"a": img_a.get("name"), "b": img_b.get("name")})
                       break
        res["medium_risk"]["similar_assets_car_images"] = shared_aci

    except Exception as e: pass

    # AI Review (Filtered Strings)
    map_a = get_origin_map(fa)
    map_b = get_origin_map(fb)
    
    str_a = set(map_a.keys())
    str_b = set(map_b.keys())

    common_raw = str_a & str_b
    common_after_noise = common_raw - noise_set
    final_strings = []
    
    for s in common_after_noise:
        if not is_meaningful_common_string(s):
            continue
        final_strings.append({
            "string": s,
            "sources_a": sorted(list(map_a[s])),
            "sources_b": sorted(list(map_b[s]))
        })

    # Sort primarily by length (descending) so AI can easily pick the longest 100
    final_strings.sort(key=lambda x: len(x["string"]), reverse=True)

    res["pending_ai_review"]["common_strings"] = final_strings
    res["pending_ai_review"]["count"] = len(final_strings)

    res["meta"]["total_common_strings_before_filter"] = len(common_raw)
    res["meta"]["noise_filtered_count"] = len(common_raw) - len(common_after_noise)
    res["meta"]["heuristic_filtered_count"] = len(common_after_noise) - len(final_strings)
    res["meta"]["total_filtered_count"] = len(common_raw) - len(final_strings)

    return res

if __name__ == "__main__":
    args = setup_args()
    fa = load_json(args.a)
    fb = load_json(args.b)
    noise = load_json(args.noise) if args.noise else {}
    
    noise_set = build_flat_noise_set(noise)
    print(f"Loaded {len(noise_set)} noise strings")
    
    res = compare(fa, fb, noise_set)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"Comparison complete. Output: {args.output}")
    print(f"Pending AI string review: {res['pending_ai_review']['count']} items")
