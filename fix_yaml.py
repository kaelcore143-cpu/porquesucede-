#!/usr/bin/env python3
"""
fix_yaml.py - Script para arreglar problemas de YAML en front matter

Escapa automáticamente los valores que contienen dos puntos (:) en el front matter
de todos los archivos Markdown para evitar errores de parsing YAML.
"""

import os
import re
import glob
from pathlib import Path
import sys

# Configuración
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, 'src')

def is_safe_path(base_path, target_path):
    """Validate that target_path is within base_path to prevent path traversal."""
    base = os.path.abspath(base_path)
    target = os.path.abspath(target_path)
    return target.startswith(base)

def safe_filename(filename):
    """Ensure filename is properly encoded for filesystem operations."""
    if isinstance(filename, bytes):
        filename = filename.decode('utf-8', errors='replace')
    return filename

MARKDOWN_FILES = []
for file_path in glob.glob(os.path.join(SRC_DIR, '**', '*.md'), recursive=True):
    file_path = safe_filename(file_path)
    if is_safe_path(SRC_DIR, file_path):
        MARKDOWN_FILES.append(file_path)

def fix_front_matter(content):
    """Fix YAML front matter by quoting values with colons."""
    
    # Separar front matter del contenido
    if not content.startswith('---'):
        return content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return content
    
    front_matter = parts[1]
    main_content = parts[2]
    
    # Patrón para encontrar líneas con clave: valor
    # que contienen dos puntos en el valor pero no están entre comillas
    pattern = re.compile(r'^(\s*)(\w+):\s*([^"]*:[^"]*)$', re.MULTILINE)
    
    def fix_line(match):
        indent = match.group(1)
        key = match.group(2)
        value = match.group(3).strip()
        
        # Si el valor ya tiene comillas, no cambiar
        if value.startswith('"') and value.endswith('"'):
            return match.group(0)
        
        # Si el valor ya tiene comillas simples, no cambiar
        if value.startswith("'") and value.endswith("'"):
            return match.group(0)
        
        # Escapar comillas dobles en el valor
        value = value.replace('"', '\\"')
        
        # Poner el valor entre comillas dobles
        return f"{indent}{key}: \"{value}\""
    
    # Aplicar la corrección al front matter
    fixed_front_matter = pattern.sub(fix_line, front_matter)
    
    # Reconstruir el contenido
    return f"---{fixed_front_matter}---{main_content}"

def fix_file(file_path):
    """Fix YAML front matter in a single Markdown file."""
    try:
        # Validate path is within SRC_DIR to prevent path traversal
        if not is_safe_path(SRC_DIR, file_path):
            print(f"✗ Security error: Path {file_path} is outside allowed directory")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = fix_front_matter(content)
        
        # Solo escribir si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed: {os.path.relpath(file_path, ROOT)}")
            return True
        else:
            print(f"- No changes needed: {os.path.relpath(file_path, ROOT)}")
            return False
            
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all Markdown files."""
    print("🔧 Fixing YAML front matter in Markdown files...")
    print(f"Found {len(MARKDOWN_FILES)} Markdown files to process")
    print()
    
    fixed_count = 0
    
    for file_path in sorted(MARKDOWN_FILES):
        if fix_file(file_path):
            fixed_count += 1
    
    print()
    print(f"✅ Completed! Fixed {fixed_count} files")
    print()
    print("Next steps:")
    print("1. Run 'npm run build' to test the fixes")
    print("2. Check for any remaining YAML errors")

if __name__ == '__main__':
    main()
