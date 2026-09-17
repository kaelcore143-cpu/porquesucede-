class SitemapTemplate {
  data() {
    return {
      permalink: "/sitemap.xml",
      eleventyExcludeFromCollections: true,
    };
  }

  render(data) {
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

    const collections = data.collections;
    if (collections && collections.all) {
      for (const page of collections.all) {
        if (!page.url || page.url === "/sitemap.xml") continue;

        const date = page.date ? new Date(page.date).toISOString().split("T")[0] : new Date().toISOString().split("T")[0];
        const isHome = page.url === "/";
        const isArticle = page.data && page.data.category;
        const changefreq = isHome ? "weekly" : isArticle ? "monthly" : "yearly";
        const priority = isHome ? "1.0" : isArticle ? "0.8" : "0.4";

        xml += "  <url>\n";
        xml += `    <loc>https://porquesucede.com${page.url}</loc>\n`;
        xml += `    <lastmod>${date}</lastmod>\n`;
        xml += `    <changefreq>${changefreq}</changefreq>\n`;
        xml += `    <priority>${priority}</priority>\n`;
        xml += "  </url>\n";
      }
    }

    xml += "</urlset>\n";
    return xml;
  }
}

module.exports = SitemapTemplate;
