module.exports = {
  runtimeCompiler: true,
  assetsDir: 'static',
  devServer: {
    proxy: 'http://localhost:8001'
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
