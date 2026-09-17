const { DateTime } = require("luxon");
require("dotenv").config();

module.exports = function(eleventyConfig) {
  // Copiar archivos estáticos
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy({"src/styles.css": "styles.css"});
  eleventyConfig.addPassthroughCopy("src/js");
  eleventyConfig.addPassthroughCopy("src/ads.txt");
  eleventyConfig.addPassthroughCopy("robots.txt");
  eleventyConfig.addPassthroughCopy("favicon.ico");
  
  // Colecciones por categoría
  eleventyConfig.addCollection("ciencia", function(collectionApi) {
    return collectionApi.getFilteredByTag("ciencia").sort((a, b) => {
      return a.data.title.localeCompare(b.data.title);
    });
  });
  
  eleventyConfig.addCollection("cuerpo", function(collectionApi) {
    return collectionApi.getFilteredByTag("cuerpo").sort((a, b) => {
      return a.data.title.localeCompare(b.data.title);
    });
  });
  
  eleventyConfig.addCollection("psicologia", function(collectionApi) {
    return collectionApi.getFilteredByTag("psicologia").sort((a, b) => {
      return a.data.title.localeCompare(b.data.title);
    });
  });
  
  eleventyConfig.addCollection("animales", function(collectionApi) {
    return collectionApi.getFilteredByTag("animales").sort((a, b) => {
      return a.data.title.localeCompare(b.data.title);
    });
  });
  
  eleventyConfig.addCollection("tecnologia", function(collectionApi) {
    return collectionApi.getFilteredByTag("tecnologia").sort((a, b) => {
      return a.data.title.localeCompare(b.data.title);
    });
  });

  // Filtro para fecha
  eleventyConfig.addFilter("readableDate", (dateObj) => {
    return DateTime.fromJSDate(dateObj).toFormat("dd LLL yyyy");
  });

  // Filtro para año actual
  eleventyConfig.addFilter("year", () => {
    return new Date().getFullYear();
  });

  // Make environment variables available in templates
  eleventyConfig.addGlobalData("adsenseId", process.env.ADSENSE_ID || "");

  // Configuración de directorios
  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      layouts: "_layouts",
      data: "_data"
    },
    templateFormats: ["html", "njk", "md"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    passthroughFileCopy: true
  };
};
