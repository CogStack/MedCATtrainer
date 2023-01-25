module.exports = {
  runtimeCompiler: true,
  assetsDir: 'static',
  productionSourceMap: true,
  devServer: {
    proxy: {
      '/api/concepts/*': {
        target: 'http://localhost:8983/solr',
        pathRewrite: {
          '/api/concepts/*': '/'
        }
      },
      '^/api/*': {
        target: 'http://localhost:8001'
      }
    }
  },
  css: {
    loaderOptions: {
      sass: {
        additionalData: `
          @import "@/styles/_variables.scss";
          @import "@/styles/_common.scss";
          @import "@/styles/_tabs.scss";
        `
      }
    }
  }
}
