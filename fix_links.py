#!/usr/bin/env python3
"""
fix_links.py - Script para convertir enlaces relativos a absolutos

Convierte todos los enlaces href="archivo.html" a href="/archivo.html"
en los archivos HTML del sitio PorQuéSucede para asegurar consistencia
con la estructura 11ty.

Configuration:
- URL mappings are loaded from config.json (or URL_MAPPING_JSON env var)
- See config.example.json for the configuration template
- config.json is gitignored for security (copy config.example.json to config.json)
"""

import os
import re
import glob
import json
from pathlib import Path
import sys

# Configuración
ROOT = os.path.dirname(os.path.abspath(__file__))

def safe_filename(filename):
    """Ensure filename is properly encoded for filesystem operations."""
    if isinstance(filename, bytes):
        filename = filename.decode('utf-8', errors='replace')
    return filename

def load_config():
    """Load configuration from config.json file.
    
    Configuration can also be loaded from environment variables.
    To use environment variables instead, set URL_MAPPING_JSON
    to a JSON string containing the url_mapping object.
    """
    # First check for environment variable
    env_config = os.environ.get('URL_MAPPING_JSON')
    if env_config:
        try:
            return json.loads(env_config)
        except json.JSONDecodeError as e:
            print(f"Error parsing URL_MAPPING_JSON environment variable: {e}")
    
    # Fall back to config.json file
    config_path = os.path.join(ROOT, 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Warning: config.json not found at {config_path}")
        return {'url_mapping': {}}
    except json.JSONDecodeError as e:
        print(f"Error parsing config.json: {e}")
        return {'url_mapping': {}}

def is_safe_path(base_path, target_path):
    """Validate that target_path is within base_path to prevent path traversal."""
    base = os.path.abspath(base_path)
    target = os.path.abspath(target_path)
    return target.startswith(base)

HTML_FILES = []
for file_path in glob.glob(os.path.join(ROOT, '*.html')):
    file_path = safe_filename(file_path)
    if is_safe_path(ROOT, file_path):
        HTML_FILES.append(file_path)

# Load configuration from config.json
config = load_config()
URL_MAPPING = config.get('url_mapping', {})

# Archivos de artículos que deben mantener su extensión .html
# (estos serán eventualmente reemplazados por la estructura 11ty)
ARTICLE_FILES = set()

def convert_relative_links(content):
    """Convierte enlaces relativos a absolutos en el contenido HTML."""
    
    # Patrón para encontrar href="archivo.html"
    pattern = re.compile(r'href="([^"]+\.html)"')
    
    def replace_link(match):
        relative_url = match.group(1)
        
        # Si ya es absoluto, no cambiar
        if relative_url.startswith('/'):
            return match.group(0)
        
        # Si es una URL externa, no cambiar
        if relative_url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
            return match.group(0)
        
        # Convertir a URL absoluta
        if relative_url in URL_MAPPING:
            absolute_url = URL_MAPPING[relative_url]
            return f'href="{absolute_url}"'
        else:
            # Para otros archivos .html, añadir solo el slash inicial
            return f'href="/{relative_url}"'
    
    # Reemplazar todos los enlaces
    content = pattern.sub(replace_link, content)
    
    # También reemplazar src="archivo.html" por si acaso
    src_pattern = re.compile(r'src="([^"]+\.html)"')
    
    def replace_src(match):
        src_url = match.group(1)
        
        if src_url.startswith('/'):
            return match.group(0)
        
        if src_url.startswith(('http://', 'https://')):
            return match.group(0)
        
        return f'src="/{src_url}"'
    
    content = src_pattern.sub(replace_src, content)
    
    return content

def fix_file(file_path):
    """Fix links in a single HTML file."""
    try:
        # Validate path is within ROOT to prevent path traversal
        if not is_safe_path(ROOT, file_path):
            print(f"✗ Security error: Path {file_path} is outside allowed directory")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content = convert_relative_links(content)
        
        # Solo escribir si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed: {os.path.basename(file_path)}")
            return True
        else:
            print(f"- No changes needed: {os.path.basename(file_path)}")
            return False
            
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all HTML files."""
    print("🔧 Fixing relative links to absolute links...")
    print(f"Found {len(HTML_FILES)} HTML files to process")
    print()
    
    fixed_count = 0
    
    for file_path in sorted(HTML_FILES):
        if fix_file(file_path):
            fixed_count += 1
    
    print()
    print(f"✅ Completed! Fixed {fixed_count} files")
    print()
    print("Next steps:")
    print("1. Test the site locally to ensure all links work")
    print("2. Run 'npm run build' to generate the 11ty site")
    print("3. Check for any remaining broken links")

if __name__ == '__main__':
    main()
