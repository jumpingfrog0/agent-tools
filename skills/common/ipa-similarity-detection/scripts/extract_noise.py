#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import argparse
import re
from datetime import datetime

def setup_args():
    parser = argparse.ArgumentParser(description="Generate noise library from Pods directory")
    parser.add_argument("--pods-dir", required=True, help="Path to the Pods/ directory")
    parser.add_argument("--include", required=False, help="Comma-separated list of SDKs to include (e.g., AFNetworking,SDWebImage)")
    parser.add_argument("--output", required=True, help="Path to output noise_strings.json")
    return parser.parse_args()

def normalize_token(token):
    token = token.strip()
    token = token.replace('\\n', '').replace('\\r', '').replace('\\t', '')
    return token

def token_valid(token):
    if not token:
        return False
    if len(token) < 3 or len(token) > 160:
        return False
    if token.startswith(("http://", "https://")) and token in {"http://", "https://"}:
        return False
    if token.count(':') > 0 and not re.match(r'^[A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z0-9_]*)*:?$', token):
        return False
    if re.match(r'^[\@\^\{\}\(\)\[\]<>=\?\-+*/%&,;!|~"\'\\0-9\.]+$', token):
        return False
    return True

def collect_tokens(tokens, values):
    for value in values:
        token = normalize_token(value)
        if token_valid(token):
            tokens.add(token)

def extract_from_file(filepath):
    strings = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

            str_matches = re.findall(r'@?"([^"\\]*(?:\\.[^"\\]*)*)"', content)
            collect_tokens(strings, str_matches)

            class_matches = re.findall(r'@(?:interface|implementation)\s+([A-Za-z0-9_]+)', content)
            collect_tokens(strings, class_matches)

            selector_matches = re.findall(
                r'[-+]\s*\([^)]+\)\s*([A-Za-z_][A-Za-z0-9_]*(?::\s*\([^)]+\)\s*[A-Za-z_][A-Za-z0-9_]*)*)',
                content
            )
            selector_tokens = []
            for raw_selector in selector_matches:
                selector = re.sub(r'\s*\([^)]+\)\s*[A-Za-z_][A-Za-z0-9_]*', ':', raw_selector)
                selector = selector.replace(' ', '')
                if ':' in selector and not selector.endswith(':'):
                    selector += ':'
                selector_tokens.append(selector)
            collect_tokens(strings, selector_tokens)

            method_matches = re.findall(r'[-+]\s*\([^)]+\)\s*([A-Za-z0-9_]+)', content)
            collect_tokens(strings, method_matches)

            swift_matches = re.findall(r'(?:class|struct|enum|protocol)\s+([A-Za-z0-9_]+)', content)
            collect_tokens(strings, swift_matches)

            func_matches = re.findall(r'func\s+([A-Za-z0-9_]+)', content)
            collect_tokens(strings, func_matches)

            identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{4,}\b', content)
            collect_tokens(strings, identifiers)

    except Exception:
        pass
    return strings

def build_noise_library(pods_dir, include_list=None):
    noise_data = {}
    pods = []
    
    try:
        all_pods = [d for d in os.listdir(pods_dir) if os.path.isdir(os.path.join(pods_dir, d)) and not d.startswith('.')]
        if include_list:
            pods = [p for p in all_pods if p in include_list]
            missed = set(include_list) - set(pods)
            if missed:
                print(f"Warning: The following requested Pods were not found in {pods_dir}: {', '.join(missed)}")
        else:
            pods = all_pods
    except Exception as e:
        print(f"Error reading Pods directory: {e}")
        return noise_data, []

    print(f"Found {len(pods)} pod directories to scan.")
    
    for pod in pods:
        pod_path = os.path.join(pods_dir, pod)
        pod_strings = set()
        
        # Walk through all source files in this pod
        for root, _, files in os.walk(pod_path):
            for file in files:
                if file.endswith(('.h', '.m', '.mm', '.swift', '.c', '.cpp')):
                    filepath = os.path.join(root, file)
                    pod_strings.update(extract_from_file(filepath))
        
        if pod_strings:
            noise_data[pod] = sorted(list(pod_strings))
            print(f"Extracted {len(pod_strings)} tokens from {pod}")
            
    return noise_data, pods

if __name__ == "__main__":
    args = setup_args()
    
    print(f"Scanning Pods directory: {args.pods_dir}")
    include_list = [p.strip() for p in args.include.split(',')] if args.include else None
    if include_list:
        print(f"Only including specified SDKs: {', '.join(include_list)}")
        
    noise_data, scanned_pods = build_noise_library(args.pods_dir, include_list)
    
    final_output = {
        "_meta": {
            "generated_at": datetime.now().isoformat(),
            "pods_scanned": sorted(scanned_pods)
        }
    }
    final_output.update(noise_data)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated noise library with {sum(len(v) for k,v in final_output.items() if k != '_meta')} total strings.")
    print(f"Saved to {args.output}")
