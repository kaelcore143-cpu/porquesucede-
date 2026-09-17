import os
import re
import json
from datetime import datetime, timezone
import sys

# Directory containing the HTML files
root = os.path.dirname(os.path.abspath(__file__))

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

# Helper to read existing articles info from index.html

def parse_articles_from_index(index_path):
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, index_path):
        raise ValueError(f"Security error: Path {index_path} is outside allowed directory")
    
    data = open(index_path, 'r', encoding='utf8').read()
    # Match entries like {title: "…", keywords: ["a","b"], url: "file.html", category: "Cat"}
    pattern = re.compile(r"\{\s*title:\s*\"(.*?)\",\s*keywords:\s*\[(.*?)\],\s*url:\s*\"(.*?)\",\s*category:\s*\"(.*?)\"\s*\}")
    articles = {}
    for m in pattern.finditer(data):
        title = m.group(1)
        kw_str = m.group(2)
        url = m.group(3)
        cat = m.group(4)
        # split keywords by comma, strip quotes/spaces
        kws = []
        if kw_str.strip():
            for part in kw_str.split(','):
                kw = part.strip().strip('"').strip("'")
                if kw:
                    kws.append(kw)
        articles[url] = {"title": title, "keywords": kws, "category": cat}
    return articles


def update_canonical(path, filename):
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, path):
        raise ValueError(f"Security error: Path {path} is outside allowed directory")
    
    data = open(path, 'r', encoding='utf8').read()
    # Build new canonical link for root file
    url = f"https://porquesucede.com/{filename}"
    newcanon = f'<link rel="canonical" href="{url}">'
    data_new = re.sub(r'<link rel="canonical" href=".*?">', lambda m: newcanon, data)
    # If pattern not found, we may insert after <title>
    if newcanon not in data_new:
        data_new = re.sub(r'(</title>)', lambda m: m.group(1) + "\n  " + newcanon, data)
    open(path, 'w', encoding='utf8').write(data_new)


def extract_title(path):
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, path):
        raise ValueError(f"Security error: Path {path} is outside allowed directory")
    
    data = open(path, 'r', encoding='utf8').read()
    m = re.search(r'<title>(.*?)</title>', data)
    if m:
        t = m.group(1)
        return t.replace(' | PorQuéSucede', '').strip()
    return ''


def extract_category(path):
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, path):
        raise ValueError(f"Security error: Path {path} is outside allowed directory")
    
    data = open(path, 'r', encoding='utf8').read()
    m = re.search(r'<span class="category-tag">(.*?)</span>', data)
    return m.group(1) if m else ''


def extract_description(path):
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, path):
        raise ValueError(f"Security error: Path {path} is outside allowed directory")
    
    data = open(path, 'r', encoding='utf8').read()
    m = re.search(r'<meta name="description" content="(.*?)"', data)
    return m.group(1) if m else ''


def generate_articles_array(entries):
    # entries: list of dict with title, keywords, url, category
    lines = ["  const articles = ["]
    for e in entries:
        kws = ', '.join(f'\"{k}\"' for k in e.get('keywords', []))
        lines.append(f'    {{title: \"{e.get("title")}\", keywords: [{kws}], url: \"{e.get("url")}\", category: \"{e.get("category")}\"}},')
    if lines:
        # remove trailing comma from last
        lines[-1] = lines[-1].rstrip(',')
    lines.append('  ];')
    return '\n'.join(lines)


def update_index_file(index_path, articles_entries):
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, index_path):
        raise ValueError(f"Security error: Path {index_path} is outside allowed directory")
    
    data = open(index_path, 'r', encoding='utf8').read()
    # replace the whole const articles block
    newblock = generate_articles_array(articles_entries)
    data_new = re.sub(r'\s*const articles = \[.*?\];', newblock, data, flags=re.S)
    open(index_path, 'w', encoding='utf8').write(data_new)


def generate_articulos_lista(entries):
    lines = ['    <section class="articulos-lista">']
    for e in entries:
        lines.append(f'      <article class="articulo-card">')
        lines.append(f'        <h2><a href="{e["url"]}">{e["title"]}</a></h2>')
        lines.append(f'        <p>{e["description"]}</p>')
        lines.append(f'      </article>')
    lines.append('      <div class="ad"><!-- Google AdSense --></div>')
    lines.append('    </section>')
    return '\n'.join(lines)


def update_category_file(cat_file, entries):
    path = os.path.join(root, cat_file)
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, path):
        raise ValueError(f"Security error: Path {path} is outside allowed directory")
    if not os.path.exists(path):
        return
    data = open(path, 'r', encoding='utf8').read()
    new_section = generate_articulos_lista(entries)
    data_new = re.sub(r'<section class="articulos-lista">.*?</section>', new_section, data, flags=re.S)
    open(path, 'w', encoding='utf8').write(data_new)


def _json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def _build_meta_tag(attrs):
    ordered = []
    for k in ['name', 'property', 'content']:
        if k in attrs:
            ordered.append((k, attrs[k]))
    for k, v in attrs.items():
        if k not in {'name', 'property', 'content'}:
            ordered.append((k, v))
    return '<meta ' + ' '.join(f'{k}="{v}"' for k, v in ordered) + '>'


def upsert_head_meta(data, tags_to_set):
    # tags_to_set: list of dicts for meta attributes (name/property/content)
    for attrs in tags_to_set:
        if 'name' in attrs:
            key = ('name', attrs['name'])
        elif 'property' in attrs:
            key = ('property', attrs['property'])
        else:
            continue

        meta_re = None
        if key[0] == 'name':
            meta_re = re.compile(r'<meta\s+[^>]*name="' + re.escape(key[1]) + r'"[^>]*>', flags=re.I)
        else:
            meta_re = re.compile(r'<meta\s+[^>]*property="' + re.escape(key[1]) + r'"[^>]*>', flags=re.I)

        new_tag = _build_meta_tag(attrs)
        if meta_re.search(data):
            data = meta_re.sub(new_tag, data, count=1)
        else:
            data = re.sub(r'(</head>)', new_tag + r'\n\1', data, count=1, flags=re.I)
    return data


def upsert_ld_json(data, schema_obj):
    new_script = '<script type="application/ld+json">' + _json_dumps(schema_obj) + '</script>'

    # Replace first existing schema.org JSON-LD, otherwise insert before </head>
    script_re = re.compile(r'<script\s+type="application/ld\+json">.*?</script>', flags=re.S | re.I)
    m = script_re.search(data)
    if m and 'schema.org' in m.group(0):
        data = script_re.sub(new_script, data, count=1)
    else:
        data = re.sub(r'(</head>)', new_script + r'\n\1', data, count=1, flags=re.I)
    return data


def update_seo(path, filename, page_type, title, description, canonical_url, category=None):
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, path):
        raise ValueError(f"Security error: Path {path} is outside allowed directory")
    
    data = open(path, 'r', encoding='utf8').read()

    robots = {'name': 'robots', 'content': 'index,follow'}
    og_type = 'website' if page_type in {'home', 'category'} else 'article' if page_type == 'article' else 'website'
    tags = [
        robots,
        {'property': 'og:site_name', 'content': 'PorQuéSucede'},
        {'property': 'og:locale', 'content': 'es_ES'},
        {'property': 'og:type', 'content': og_type},
        {'property': 'og:title', 'content': title},
        {'property': 'og:description', 'content': description},
        {'property': 'og:url', 'content': canonical_url},
        {'name': 'twitter:card', 'content': 'summary'},
        {'name': 'twitter:title', 'content': title},
        {'name': 'twitter:description', 'content': description},
    ]

    data = upsert_head_meta(data, tags)

    org = {'@type': 'Organization', 'name': 'PorQuéSucede'}

    schema_obj = None
    if page_type == 'home':
        schema_obj = {
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            'name': 'PorQuéSucede',
            'url': canonical_url,
            'inLanguage': 'es'
        }
    elif page_type == 'category':
        schema_obj = {
            '@context': 'https://schema.org',
            '@type': 'CollectionPage',
            'name': title,
            'description': description,
            'url': canonical_url,
            'inLanguage': 'es',
            'publisher': org
        }
    elif page_type == 'legal':
        schema_obj = {
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            'name': title,
            'description': description,
            'url': canonical_url,
            'inLanguage': 'es',
            'publisher': org
        }
    elif page_type == 'article':
        breadcrumb_items = [
            {'@type': 'ListItem', 'position': 1, 'name': 'Inicio', 'item': 'https://porquesucede.com/'},
        ]
        if category:
            cat_slug = {
                'Ciencia': 'ciencia.html',
                'Cuerpo Humano': 'cuerpo.html',
                'Psicología': 'psicologia.html',
                'Animales': 'animales.html',
                'Tecnología': 'tecnologia.html'
            }.get(category)
            if cat_slug:
                breadcrumb_items.append({'@type': 'ListItem', 'position': 2, 'name': category, 'item': f'https://porquesucede.com/{cat_slug}'})
                pos = 3
            else:
                pos = 2
        else:
            pos = 2
        breadcrumb_items.append({'@type': 'ListItem', 'position': pos, 'name': title})

        schema_obj = {
            '@context': 'https://schema.org',
            '@graph': [
                {
                    '@type': 'Article',
                    'headline': title,
                    'description': description,
                    'mainEntityOfPage': canonical_url,
                    'url': canonical_url,
                    'inLanguage': 'es',
                    'publisher': org
                },
                {
                    '@type': 'BreadcrumbList',
                    'itemListElement': breadcrumb_items
                }
            ]
        }

    if schema_obj:
        data = upsert_ld_json(data, schema_obj)

    open(path, 'w', encoding='utf8').write(data)


def _format_lastmod(path):
    ts = os.path.getmtime(path)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime('%Y-%m-%d')


def generate_sitemap(url_entries):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', '']
    for e in url_entries:
        lines.append('  <url>')
        lines.append(f'    <loc>{e["loc"]}</loc>')
        if e.get('lastmod'):
            lines.append(f'    <lastmod>{e["lastmod"]}</lastmod>')
        if e.get('changefreq'):
            lines.append(f'    <changefreq>{e["changefreq"]}</changefreq>')
        if e.get('priority'):
            lines.append(f'    <priority>{e["priority"]}</priority>')
        lines.append('  </url>')
        lines.append('')
    lines.append('</urlset>')
    lines.append('')
    return '\n'.join(lines)


if __name__ == '__main__':
    index_path = os.path.join(root, 'index.html')
    existing = parse_articles_from_index(index_path)

    # gather html files excluding navigation and utility pages
    excluded = {
        'index.html', 'contacto.html', 'politica-cookies.html', 'politica-privacidad.html',
        'sobre-nosotros.html', 'terminos.html', 'ciencia.html', 'cuerpo.html',
        'psicologia.html', 'animales.html', 'tecnologia.html', 'googledaa77f51c5093301.html', 'ads.txt', 'styles.css'
    }

    article_entries = []
    for fname in sorted(os.listdir(root)):
        fname = safe_filename(fname)
        if not fname.lower().endswith('.html') or fname in excluded:
            continue
        if fname.endswith('_1.html'):
            continue
        path = os.path.join(root, fname)
        # Validate path is within root to prevent path traversal
        if not is_safe_path(root, path):
            print(f"Security error: Skipping {path} - outside allowed directory")
            continue
        title = extract_title(path) or existing.get(fname, {}).get('title', fname)
        category = extract_category(path) or existing.get(fname, {}).get('category', '')
        kw = existing.get(fname, {}).get('keywords', [])
        description = extract_description(path)
        # update canonical link
        update_canonical(path, fname)
        canonical_url = f"https://porquesucede.com/{fname}"
        update_seo(path, fname, 'article', title, description, canonical_url, category=category)
        article_entries.append({'title': title, 'keywords': kw, 'url': fname, 'category': category, 'description': description})

    # sort entries by title for predictable ordering
    article_entries.sort(key=lambda x: x['title'])

    # update index.html script
    update_index_file(index_path, article_entries)

    update_canonical(index_path, '')

    index_title = extract_title(index_path) or 'PorQuéSucede'
    index_desc = extract_description(index_path) or ''
    update_seo(index_path, 'index.html', 'home', index_title, index_desc, 'https://porquesucede.com/')

    # group by category
    categories = {}
    for e in article_entries:
        cat = e['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(e)

    # update category files
    category_mapping = {
        "Ciencia": "ciencia.html",
        "Cuerpo Humano": "cuerpo.html",
        "Psicología": "psicologia.html",
        "Animales": "animales.html",
        "Tecnología": "tecnologia.html"
    }
    for cat, file in category_mapping.items():
        if cat in categories:
            update_category_file(file, categories[cat])

    for file in category_mapping.values():
        path = os.path.join(root, file)
        if os.path.exists(path):
            update_canonical(path, file)
            t = extract_title(path) or file
            d = extract_description(path) or ''
            update_seo(path, file, 'category', t, d, f'https://porquesucede.com/{file}')

    for file in ['sobre-nosotros.html', 'contacto.html', 'politica-privacidad.html', 'politica-cookies.html', 'terminos.html']:
        path = os.path.join(root, file)
        if os.path.exists(path):
            update_canonical(path, file)
            t = extract_title(path) or file
            d = extract_description(path) or ''
            update_seo(path, file, 'legal', t, d, f'https://porquesucede.com/{file}')

    sitemap_entries = []
    sitemap_entries.append({
        'loc': 'https://porquesucede.com/',
        'lastmod': _format_lastmod(index_path),
        'changefreq': 'weekly',
        'priority': '1.0'
    })

    for file, priority in [
        ('ciencia.html', '0.9'),
        ('cuerpo.html', '0.9'),
        ('psicologia.html', '0.9'),
        ('animales.html', '0.9'),
        ('tecnologia.html', '0.9'),
    ]:
        path = os.path.join(root, file)
        if os.path.exists(path):
            sitemap_entries.append({
                'loc': f'https://porquesucede.com/{file}',
                'lastmod': _format_lastmod(path),
                'changefreq': 'weekly',
                'priority': priority
            })

    for e in article_entries:
        path = os.path.join(root, e['url'])
        sitemap_entries.append({
            'loc': f'https://porquesucede.com/{e["url"]}',
            'lastmod': _format_lastmod(path),
            'changefreq': 'monthly',
            'priority': '0.8'
        })

    for file, priority in [
        ('sobre-nosotros.html', '0.4'),
        ('contacto.html', '0.4'),
        ('politica-privacidad.html', '0.3'),
        ('politica-cookies.html', '0.3'),
        ('terminos.html', '0.3'),
    ]:
        path = os.path.join(root, file)
        if os.path.exists(path):
            sitemap_entries.append({
                'loc': f'https://porquesucede.com/{file}',
                'lastmod': _format_lastmod(path),
                'changefreq': 'yearly',
                'priority': priority
            })

    sitemap_path = os.path.join(root, 'sitemap.xml')
    # Validate path is within root to prevent path traversal
    if not is_safe_path(root, sitemap_path):
        raise ValueError(f"Security error: Path {sitemap_path} is outside allowed directory")
    open(sitemap_path, 'w', encoding='utf8').write(generate_sitemap(sitemap_entries))

    print(f"Processed {len(article_entries)} articles and updated index.html, canonicals, category pages, and sitemap.xml.")
