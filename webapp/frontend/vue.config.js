module.exports = {
  runtimeCompiler: true,
  assetsDir: 'static', // For simple configuration of static files in Flask (the "static_folder='client/dist/static'" part in app.py)
  // needs to change for django-rest to serve up final built files.
  devServer: {
    proxy: 'http://localhost:8001'
  },
  configureWebpack: {
    devtool: 'source-map'
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
