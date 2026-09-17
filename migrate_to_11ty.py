#!/usr/bin/env python3
"""
migrate_to_11ty.py - Script para migrar HTML estático a 11ty Markdown

Convierte todos los archivos HTML del sitio PorQuéSucede al formato Markdown
con frontmatter para 11ty, organizándolos por categorías.

Uso:
    python migrate_to_11ty.py

Requiere:
    - Archivos HTML en el directorio raíz
    - Estructura src/ ya creada por setup_11ty.py
"""

import os
import re
import json
from html import unescape
from pathlib import Path
import sys

# Configuración
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, 'src')
BACKUP_DIR = os.path.join(ROOT, 'backup_html')

def safe_filename(filename):
    """Ensure filename is properly encoded for filesystem operations."""
    if isinstance(filename, bytes):
        filename = filename.decode('utf-8', errors='replace')
    return filename

# Mapeo de categorías a slugs de carpeta
CATEGORY_MAP = {
    'Ciencia': 'ciencia',
    'Cuerpo Humano': 'cuerpo',
    'Psicología': 'psicologia',
    'Animales': 'animales',
    'Tecnología': 'tecnologia'
}

# Archivos a excluir (no son artículos)
EXCLUDED_FILES = {
    'index.html', 'ciencia.html', 'cuerpo.html', 'psicologia.html',
    'animales.html', 'tecnologia.html', 'contacto.html', 'sobre-nosotros.html',
    'politica-privacidad.html', 'politica-cookies.html', 'terminos.html',
    'googledaa77f51c5093301.html', 'sitemap.xml', 'robots.txt'
}


def slugify(text):
    """Convierte un título a slug URL-friendly."""
    text = text.lower()
    text = re.sub(r'[¿?¡!]', '', text)
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text.strip('-')


def extract_title(html_content):
    """Extrae el título del <title>."""
    match = re.search(r'<title>(.*?)\s*\|\s*PorQuéSucede</title>', html_content, re.IGNORECASE)
    if match:
        return unescape(match.group(1)).strip()
    
    # Fallback: buscar h1
    match = re.search(r'<h1>(.*?)</h1>', html_content, re.DOTALL | re.IGNORECASE)
    if match:
        # Limpiar tags HTML internos
        h1_text = re.sub(r'<[^>]+>', '', match.group(1))
        return unescape(h1_text).strip()
    
    return None


def extract_description(html_content):
    """Extrae la meta description."""
    match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html_content, re.IGNORECASE)
    if match:
        return unescape(match.group(1)).strip()
    return ''


def extract_category(html_content):
    """Extrae la categoría del span.category-tag o crumbs."""
    # Intentar con category-tag
    match = re.search(r'<span\s+class="category-tag">([^<]+)</span>', html_content, re.IGNORECASE)
    if match:
        return unescape(match.group(1)).strip()
    
    # Intentar con breadcrumb
    match = re.search(r'Ciencia</a>', html_content, re.IGNORECASE)
    if match:
        return 'Ciencia'
    match = re.search(r'Cuerpo</a>', html_content, re.IGNORECASE)
    if match:
        return 'Cuerpo Humano'
    match = re.search(r'Psicología</a>', html_content, re.IGNORECASE)
    if match:
        return 'Psicología'
    match = re.search(r'Animales</a>', html_content, re.IGNORECASE)
    if match:
        return 'Animales'
    match = re.search(r'Tecnología</a>', html_content, re.IGNORECASE)
    if match:
        return 'Tecnología'
    
    return 'Ciencia'  # Default


def extract_read_time(html_content):
    """Extrae el tiempo de lectura."""
    match = re.search(r'(\d+)\s*min\s+de\s+lectura', html_content, re.IGNORECASE)
    if match:
        return f"{match.group(1)} min"
    return "5 min"


def extract_short_answer(html_content):
    """Extrae la respuesta corta del answer-box."""
    match = re.search(r'<div\s+class="answer-box">(.*?)<strong>Respuesta\s+corta:</strong>(.*?)</div>', 
                      html_content, re.DOTALL | re.IGNORECASE)
    if match:
        answer = match.group(2)
        # Limpiar HTML
        answer = re.sub(r'<[^>]+>', '', answer)
        return unescape(answer).strip()
    return ''


def html_to_markdown(html_content):
    """Convierte HTML simple a Markdown."""
    # Extraer solo el contenido de article-body
    match = re.search(r'<div\s+class="article-body">(.*?)</div>\s*</main>', 
                      html_content, re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r'<div\s+class="article-body">(.*?)</div>\s*</body>', 
                          html_content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        return ''
    
    content = match.group(1)
    
    # Remover answer-box (se maneja separado en frontmatter)
    content = re.sub(r'<div\s+class="answer-box">.*?</div>', '', content, 
                     flags=re.DOTALL | re.IGNORECASE)
    
    # Remover ads
    content = re.sub(r'<div\s+class="ad">.*?</div>', '', content, 
                     flags=re.DOTALL | re.IGNORECASE)
    
    # Remover related-questions
    content = re.sub(r'<div\s+class="related-questions">.*?</div>', '', content, 
                     flags=re.DOTALL | re.IGNORECASE)
    
    # Convertir headers
    content = re.sub(r'<h2>(.*?)</h2>', r'\n## \1\n', content, flags=re.DOTALL)
    content = re.sub(r'<h3>(.*?)</h3>', r'\n### \1\n', content, flags=re.DOTALL)
    
    # Convertir párrafos
    content = re.sub(r'<p>(.*?)</p>', r'\n\1\n', content, flags=re.DOTALL)
    
    # Convertir listas
    content = re.sub(r'<ul>(.*?)</ul>', lambda m: convert_list(m.group(1), 'ul'), 
                     content, flags=re.DOTALL)
    content = re.sub(r'<ol>(.*?)</ol>', lambda m: convert_list(m.group(1), 'ol'), 
                     content, flags=re.DOTALL)
    
    # Convertir bold
    content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
    content = re.sub(r'<b>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
    
    # Convertir italic
    content = re.sub(r'<em>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
    content = re.sub(r'<i>(.*?)</i>', r'*\1*', content, flags=re.DOTALL)
    
    # Limpiar tags HTML restantes
    content = re.sub(r'<[^>]+>', '', content)
    
    # Decodificar entidades HTML
    content = unescape(content)
    
    # Normalizar espacios en blanco
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = content.strip()
    
    return content


def convert_list(list_html, list_type):
    """Convierte una lista HTML a Markdown."""
    items = re.findall(r'<li>(.*?)</li>', list_html, re.DOTALL)
    result = []
    for i, item in enumerate(items, 1):
        # Limpiar HTML interno del item
        item = re.sub(r'<[^>]+>', '', item)
        item = unescape(item).strip()
        if list_type == 'ul':
            result.append(f'- {item}')
        else:
            result.append(f'{i}. {item}')
    return '\n' + '\n'.join(result) + '\n'


def extract_related_articles(html_content):
    """Extrae los artículos relacionados."""
    related = []
    match = re.search(r'<div\s+class="related-questions">.*?<ul>(.*?)</ul>.*?</div>', 
                      html_content, re.DOTALL | re.IGNORECASE)
    if match:
        items = re.findall(r'<li><a\s+href="([^"]+)">([^<]+)</a></li>', match.group(1))
        for url, title in items:
            # Convertir URL vieja a nueva estructura
            new_url = convert_old_url_to_new(url)
            related.append({'title': unescape(title).strip(), 'url': new_url})
    return related


def convert_old_url_to_new(old_url):
    """Convierte una URL vieja (flat) a nueva (/categoria/slug/)."""
    # Remover .html
    slug = old_url.replace('.html', '')
    
    # Determinar categoría por el slug
    category_guess = guess_category_from_slug(slug)
    
    return f'/{category_guess}/{slug}/'


def guess_category_from_slug(slug):
    """Intenta adivinar la categoría basada en palabras clave del slug."""
    keywords = {
        'ciencia': ['cielo', 'agua', 'estrella', 'sol', 'luna', 'tierra', 'fuego', 'hielo', 'mar', 
                    'vulcano', 'rayo', 'truen', 'gravedad', 'arcoiris', 'energia', 'terremoto',
                    'numeros-primos', 'barco', 'flot', 'volcan', 'gas'],
        'cuerpo': ['cerebro', 'corazon', 'ojos', 'pelo', 'diente', 'hueso', 'sangre', 'nariz',
                   'sudor', 'lagrima', 'bostez', 'estornudo', 'hipo', 'escalofrio', 'moreton',
                   'apendice', 'ceja', 'pupila', 'dormir', 'hambre', 'aliento', 'cafe'],
        'psicologia': ['sueno', 'ansiedad', 'enamor', 'olvido', 'memoria', 'miedo', 'procrastin',
                       'intuicion', 'personalidad', 'empatia', 'autoestima', 'efecto-placebo',
                       'nervio', 'reir', 'verguenza', 'solos', 'ansiedad', 'estres', 'depresion'],
        'animales': ['gato', 'perro', 'abeja', 'araña', 'ave', 'delfin', 'elefante', 'pez',
                     'loro', 'serpiente', 'camaleon', 'tiburon', 'estrella-de-mar', 'flor',
                     'planta-carnivora', 'migracion', 'cola', 'ronrone', 'banco', 'miel'],
        'tecnologia': ['internet', 'wifi', 'gps', 'correo', 'reconocimiento-facial', 'inteligencia-artificial',
                       'realidad-virtual', 'imán', 'motor', 'smartphone', 'bateria', 'pantalla',
                       'impresion-3d', 'metaverso', 'ciberseguridad', 'computacion-cuantica',
                       'satelite']
    }
    
    slug_lower = slug.lower()
    for cat, words in keywords.items():
        for word in words:
            if word in slug_lower:
                return cat
    
    return 'ciencia'  # Default


def generate_frontmatter(data):
    """Genera el frontmatter YAML para 11ty."""
    category_slug = CATEGORY_MAP.get(data['category'], 'ciencia')
    article_slug = slugify(data['title'])
    
    related_yaml = ''
    if data.get('related'):
        related_items = []
        for item in data['related'][:3]:  # Max 3
            related_items.append(f'  - title: {item["title"]}\n    url: {item["url"]}')
        related_yaml = '\nrelated_articles:\n' + '\n'.join(related_items)
    
    # Construir JSON-LD
    structured_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": data['title'],
                "description": data['description'],
                "mainEntityOfPage": f"https://porquesucede.com/{category_slug}/{article_slug}/",
                "url": f"https://porquesucede.com/{category_slug}/{article_slug}/",
                "inLanguage": "es",
                "publisher": {"@type": "Organization", "name": "PorQuéSucede"}
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://porquesucede.com/"},
                    {"@type": "ListItem", "position": 2, "name": data['category'], "item": f"https://porquesucede.com/{category_slug}/"},
                    {"@type": "ListItem", "position": 3, "name": data['title']}
                ]
            }
        ]
    }
    
    frontmatter = f'''---
layout: article.njk
title: {data['title']}
description: {data['description']}
category: {data['category']}
tags: [{category_slug}]
keywords: []
read_time: {data['read_time']}
short_answer: {data['short_answer']}
permalink: /{category_slug}/{article_slug}/
breadcrumbs:
  - name: {data['category']}
    url: /{category_slug}/
  - name: {data['title']}
    url: /{category_slug}/{article_slug}/
structured_data: '{json.dumps(structured_data, ensure_ascii=False)}'{related_yaml}
---

'''
    return frontmatter


def migrate_article(html_path):
    """Migra un archivo HTML a Markdown de 11ty."""
    with open(html_path, 'r', encoding='utf8') as f:
        html_content = f.read()
    
    # Extraer datos
    title = extract_title(html_content)
    if not title:
        print(f"  ⚠️  Sin título: {os.path.basename(html_path)}")
        return None
    
    category = extract_category(html_content)
    category_slug = CATEGORY_MAP.get(category, 'ciencia')
    
    data = {
        'title': title,
        'description': extract_description(html_content),
        'category': category,
        'read_time': extract_read_time(html_content),
        'short_answer': extract_short_answer(html_content),
        'related': extract_related_articles(html_content)
    }
    
    # Convertir contenido
    markdown_content = html_to_markdown(html_content)
    
    # Generar frontmatter + contenido
    full_content = generate_frontmatter(data) + markdown_content
    
    # Determinar nombre de archivo
    article_slug = slugify(title)
    output_path = os.path.join(SRC_DIR, category_slug, f'{article_slug}.md')
    
    return {
        'content': full_content,
        'output_path': output_path,
        'category': category,
        'title': title
    }


def main():
    print("=" * 60)
    print("MIGRACIÓN A 11ty")
    print("=" * 60)
    print()
    
    # Verificar estructura
    if not os.path.exists(SRC_DIR):
        print("❌ Error: No existe el directorio src/")
        print("   Ejecuta primero: python setup_11ty.py")
        return
    
    # Contar HTML
    html_files = [safe_filename(f) for f in os.listdir(ROOT) 
                  if f.lower().endswith('.html') and f not in EXCLUDED_FILES and not f.startswith('_')]
    
    print(f"📁 Archivos HTML encontrados: {len(html_files)}")
    print(f"📁 Directorio destino: {SRC_DIR}")
    print()
    
    # Estadísticas
    stats = {cat: 0 for cat in CATEGORY_MAP.keys()}
    stats['sin_categoria'] = 0
    migrated = []
    errors = []
    
    # Migrar cada archivo
    for i, html_file in enumerate(sorted(html_files), 1):
        print(f"[{i}/{len(html_files)}] {html_file}...", end=' ')
        
        html_path = os.path.join(ROOT, html_file)
        
        try:
            result = migrate_article(html_path)
            if result:
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(result['output_path']), exist_ok=True)
                
                # Escribir archivo
                with open(result['output_path'], 'w', encoding='utf8') as f:
                    f.write(result['content'])
                
                category = result['category']
                if category in stats:
                    stats[category] += 1
                else:
                    stats['sin_categoria'] += 1
                
                migrated.append({
                    'old': html_file,
                    'new': result['output_path'].replace(SRC_DIR + '\\', 'src/'),
                    'category': category
                })
                print(f"✅ → {category}")
            else:
                errors.append((html_file, "No se pudo extraer título"))
                print("❌")
                
        except Exception as e:
            errors.append((html_file, str(e)))
            print(f"❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("RESUMEN DE MIGRACIÓN")
    print("=" * 60)
    print()
    
    total_migrated = sum(stats.values()) - stats.get('sin_categoria', 0)
    print(f"✅ Artículos migrados: {total_migrated}")
    print(f"❌ Errores: {len(errors)}")
    print()
    print("Por categoría:")
    for cat, count in stats.items():
        if count > 0:
            print(f"  • {cat}: {count}")
    print()
    
    # Guardar mapeo de URLs para redirecciones
    redirect_map = []
    for m in migrated:
        old_slug = m['old'].replace('.html', '')
        new_path = m['new'].replace('src/', '/').replace('.md', '/')
        category = m['category'].lower().replace(' ', '-')
        redirect_map.append({
            'from': f'/{old_slug}.html',
            'to': new_path
        })
    
    # Guardar archivo de mapeo
    map_path = os.path.join(ROOT, 'redirect_map.json')
    with open(map_path, 'w', encoding='utf8') as f:
        json.dump(redirect_map, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Mapeo de redirecciones guardado: {map_path}")
    print()
    
    if errors:
        print("⚠️  Archivos con errores:")
        for fname, err in errors:
            print(f"  • {fname}: {err}")
        print()
    
    print("=" * 60)
    print("SIGUIENTES PASOS:")
    print("=" * 60)
    print()
    print("1. Instalar dependencias:")
    print("   npm install")
    print()
    print("2. Probar build:")
    print("   npm start")
    print()
    print("3. Generar redirecciones (si es necesario):")
    print("   Revisa redirect_map.json para crear páginas de redirección")
    print()
    print("4. Desplegar:")
    print("   npm run build")
    print("   # Subir contenido de _site/ a tu hosting")
    print()


if __name__ == '__main__':
    main()
