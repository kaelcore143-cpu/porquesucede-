#!/usr/bin/env python3
"""
fix_yaml_v2.py - Corrige la corrupcion de YAML causada por fix_yaml.py

Corrige 4 patrones de corrupcion:
1. layout: "article.njk  →  layout: article.njk
2. url: /path/"           →  url: /path/
3. related_articles: "- title: ... "---  →  lista YAML proper
4. Valores con ": " sin comillas  →  comillas dobles
"""

import os
import re
import glob
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, 'src')

def safe_filename(filename):
    """Ensure filename is properly encoded for filesystem operations."""
    if isinstance(filename, bytes):
        filename = filename.decode('utf-8', errors='replace')
    return filename

MARKDOWN_FILES = [safe_filename(f) for f in glob.glob(os.path.join(SRC_DIR, '**', '*.md'), recursive=True)]


def fix_corrupted_yaml(content):
    """Fix YAML front matter corrupted by the previous fix_yaml.py script."""

    if not content.startswith('---'):
        return content

    # === PASO 1: Correcciones de string antes de split ===

    # Fix 1: layout: "article.njk → layout: article.njk
    content = content.replace('layout: "article.njk', 'layout: article.njk')

    # Fix 2: related_articles: "- title: → related_articles:\n  - title:
    content = content.replace(
        'related_articles: "- title:',
        'related_articles:\n  - title:'
    )

    # Fix 3: /"--- → /\n---  (comilla antes del closing delimiter)
    content = content.replace('/"---', '/\n---')

    # Fix 4: "---\n al final del front matter → ---\n
    content = re.sub(r'"---\n', '---\n', content)

    # Fix 5: trailing " en URLs de breadcrumbs (url: /path/" al final de linea)
    content = re.sub(
        r'(url: /[^\s"]+)/"(\s*)$',
        r'\1\2',
        content,
        flags=re.MULTILINE
    )

    # === PASO 2: Split front matter / body ===
    parts = content.split('---', 2)
    if len(parts) < 3:
        return content

    front_matter = parts[1]
    body = parts[2]

    # === PASO 3: Quoting correcto linea por linea ===
    lines = front_matter.split('\n')
    fixed_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip lineas vacias
        if not stripped:
            fixed_lines.append(line)
            continue

        # Skip lineas indentadas (items de lista, propiedades anidadas)
        if line.startswith(' ') or line.startswith('\t'):
            fixed_lines.append(line)
            continue

        # Es una linea clave: valor?
        m = re.match(r'^(\w+):\s*(.*)$', line)
        if m:
            key = m.group(1)
            value = m.group(2)

            # Skip si no hay valor (ej: "breadcrumbs:" o "related_articles:")
            if not value:
                fixed_lines.append(line)
                continue

            # Skip si ya tiene comillas dobles
            if value.startswith('"') and value.endswith('"'):
                fixed_lines.append(line)
                continue

            # Skip si ya tiene comillas simples (ej: structured_data)
            if value.startswith("'") and value.endswith("'"):
                fixed_lines.append(line)
                continue

            # Skip si es un array (ej: tags: [ciencia])
            if value.startswith('['):
                fixed_lines.append(line)
                continue

            # Si el valor contiene ": " (colon + espacio), necesita comillas
            if ': ' in value:
                escaped = value.replace('"', '\\"')
                fixed_lines.append(f'{key}: "{escaped}"')
                continue

        fixed_lines.append(line)

    front_matter = '\n'.join(fixed_lines)

    # === PASO 4: Reconstruir ===
    return f'---{front_matter}---{body}'


def fix_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        content = fix_corrupted_yaml(content)

        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Fixed: {os.path.relpath(file_path, ROOT)}")
            return True
        else:
            print(f"  Skip:  {os.path.relpath(file_path, ROOT)}")
            return False
    except Exception as e:
        print(f"  ERROR: {file_path}: {e}")
        return False


def main():
    print("Fixing corrupted YAML front matter (v2)...")
    print(f"Files to process: {len(MARKDOWN_FILES)}\n")

    fixed = 0
    for f in sorted(MARKDOWN_FILES):
        if fix_file(f):
            fixed += 1

    print(f"\nDone: {fixed} files fixed")
    print("Next: run 'npm run build' to verify")


if __name__ == '__main__':
    main()
