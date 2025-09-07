#!/usr/bin/env python3
"""
File Integrity Monitor (FIM)
Упрощенная версия для Windows
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'

def calculate_file_hash(file_path):
    try:
        hash_func = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        print(f"{Colors.RED}Ошибка чтения файла {file_path}: {e}{Colors.END}")
        return None

def scan_directory(directory_path):
    file_hashes = {}
    dir_path = Path(directory_path)
    
    if not dir_path.exists():
        print(f"{Colors.RED}Директория {directory_path} не существует!{Colors.END}")
        return None
    
    print(f"{Colors.BLUE}Сканирование директории: {dir_path.absolute()}{Colors.END}")
    
    try:
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                file_hash = calculate_file_hash(file_path)
                if file_hash:
                    rel_path = str(file_path.relative_to(dir_path))
                    file_hashes[rel_path] = {
                        'hash': file_hash,
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    }
        return file_hashes
    except Exception as e:
        print(f"{Colors.RED}Ошибка сканирования: {e}{Colors.END}")
        return None

def save_baseline(data, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"{Colors.GREEN}Baseline сохранен в {output_file}{Colors.END}")
        return True
    except Exception as e:
        print(f"{Colors.RED}Ошибка сохранения: {e}{Colors.END}")
        return False

def load_baseline(baseline_file):
    try:
        with open(baseline_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}Ошибка загрузки baseline: {e}{Colors.END}")
        return None

def compare_baselines(current, baseline):
    changes = {
        'new': [],      
        'deleted': [],    
        'modified': []  
    }
    
    current_files = set(current.keys())
    baseline_files = set(baseline.keys())
    
    changes['new'] = list(current_files - baseline_files)
    
    changes['deleted'] = list(baseline_files - current_files)
    
    for file in current_files.intersection(baseline_files):
        if (current[file]['hash'] != baseline[file]['hash'] or
            current[file]['size'] != baseline[file]['size']):
            changes['modified'].append(file)
    
    return changes

def print_changes(changes):
    print(f"\n{Colors.BLUE}=== РЕЗУЛЬТАТЫ ПРОВЕРКИ ==={Colors.END}")
    
    if not any(changes.values()):
        print(f"{Colors.GREEN}✓ Изменений не обнаружено!{Colors.END}")
        return
    
    if changes['new']:
        print(f"\n{Colors.GREEN}НОВЫЕ ФАЙЛЫ:{Colors.END}")
        for file in changes['new']:
            print(f"  + {file}")
    
    if changes['deleted']:
        print(f"\n{Colors.RED}УДАЛЕННЫЕ ФАЙЛЫ:{Colors.END}")
        for file in changes['deleted']:
            print(f"  - {file}")
    
    if changes['modified']:
        print(f"\n{Colors.YELLOW}ИЗМЕНЕННЫЕ ФАЙЛЫ:{Colors.END}")
        for file in changes['modified']:
            print(f"  ! {file}")

def main():
    parser = argparse.ArgumentParser(description='File Integrity Monitor')
    parser.add_argument('directory', help='Директория для мониторинга')
    parser.add_argument('--output', help='Файл для сохранения baseline')
    parser.add_argument('--with', dest='baseline_file', help='Файл baseline для сравнения')
    parser.add_argument('-b', '--baseline', action='store_true', help='Создать baseline')
    parser.add_argument('-c', '--check', action='store_true', help='Проверить изменения')
    
    args = parser.parse_args()
    
    directory = os.path.normpath(args.directory)
    
    if args.baseline:
        if not args.output:
            print(f"{Colors.RED}Укажите файл для сохранения: --output filename.json{Colors.END}")
            return
        
        print(f"Создание baseline для: {directory}")
        data = scan_directory(directory)
        if data:
            save_baseline(data, args.output)
    
    elif args.check:
        if not args.baseline_file:
            print(f"{Colors.RED}Укажите файл baseline: --with baseline.json{Colors.END}")
            return
        
        print(f"Проверка директории: {directory}")
        current_data = scan_directory(directory)
        baseline_data = load_baseline(args.baseline_file)
        
        if current_data and baseline_data:
            changes = compare_baselines(current_data, baseline_data)
            print_changes(changes)
    
    else:
        parser.print_help()

if __name__ == "__main__":

    main()
