# PorQuéSucede - Migración a 11ty

## Estructura del Proyecto

```
porquesucede.com/
├── src/                          # Código fuente
│   ├── _layouts/                 # Layouts de 11ty
│   │   ├── base.njk             # Layout base con SEO
│   │   ├── article.njk          # Layout para artículos
│   │   └── category.njk         # Layout para categorías
│   ├── ciencia/                  # Artículos de ciencia
│   │   └── por-que-el-cielo-es-azul.md
│   ├── cuerpo/                   # Artículos de cuerpo humano
│   ├── psicologia/               # Artículos de psicología
│   ├── animales/                 # Artículos de animales
│   ├── tecnologia/               # Artículos de tecnología
│   ├── index.njk                 # Página de inicio
│   ├── ciencia.njk               # Página de categoría
│   ├── cuerpo.njk
│   ├── psicologia.njk
│   ├── animales.njk
│   ├── tecnologia.njk
│   └── styles.css               # CSS optimizado
├── eleventy.config.js           # Configuración de 11ty
├── package.json                 # Dependencias
└── _site/                       # Output (generado)
```

## URLs Nuevas vs Antiguas

| Antigua (flat) | Nueva (11ty) |
|----------------|--------------|
| `/por-que-el-cielo-es-azul.html` | `/ciencia/por-que-el-cielo-es-azul/` |
| `/ciencia.html` | `/ciencia/` |
| `/index.html` | `/` |

## Instalación

```bash
npm install
```

## Comandos

```bash
# Servidor de desarrollo
npm start

# Build para producción
npm run build
```

## Migración de Artículos

### Formato Frontmatter

```yaml
---
layout: article.njk
title: ¿Por qué el cielo es azul?
description: Descubre por qué el cielo es azul...
category: Ciencia
tags: [ciencia, fisica, luz]
keywords: [cielo, azul, luz]
read_time: 5 min
short_answer: El cielo es azul porque...
permalink: /ciencia/por-que-el-cielo-es-azul/
---
```

### Estructura de Contenido

1. Usar `##` para subtítulos (H2)
2. Incluir `<div class="ad"><!-- Google AdSense --></div>` para anuncios
3. Lista de preguntas relacionadas al final

## Compatibilidad Hacia Atrás

### Opción 1: Redirecciones en Hosting
Si tu hosting lo permite (Netlify, Vercel, etc.):

**netlify.toml:**
```toml
[[redirects]]
  from = "/por-que-el-cielo-es-azul.html"
  to = "/ciencia/por-que-el-cielo-es-azul/"
  status = 301
```

### Opción 2: Páginas de Redirección (Static)
Para hosting estático sin redirecciones 301:

```html
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="refresh" content="0; url=/ciencia/por-que-el-cielo-es-azul/">
  <link rel="canonical" href="https://porquesucede.com/ciencia/por-que-el-cielo-es-azul/">
</head>
<body>
  <a href="/ciencia/por-que-el-cielo-es-azul/">Continuar</a>
</body>
</html>
```

## Ventajas de 11ty

1. **Layouts reutilizables**: Un solo cambio aplica a todas las páginas
2. **Colecciones automáticas**: Las categorías se generan dinámicamente
3. **SEO consistente**: Meta tags y JSON-LD en un solo lugar
4. **URLs limpias**: `/ciencia/por-que-el-cielo-es-azul/` vs `.html`
5. **Performance**: Build estático, sin servidor necesario
6. **Escalabilidad**: Fácil agregar 100+ artículos

## Pasos para Completar Migración

1. ✅ Configurar 11ty y crear estructura
2. ✅ Crear layouts base
3. ✅ Migrar artículos de ejemplo
4. ⏳ Migrar todos los artículos existentes (~100)
5. ⏳ Configurar redirecciones o páginas de redirección
6. ⏳ Actualizar sitemap.xml automático
7. ⏳ Testear build y validar URLs
8. ⏳ Desplegar nuevo sitio

## Script de Migración Automática

Usar el script `migrate_to_11ty.py` (crear basado en `update_site.py`) para:
- Parsear HTML existente
- Extraer frontmatter
- Convertir a Markdown
- Generar archivos en /src/
