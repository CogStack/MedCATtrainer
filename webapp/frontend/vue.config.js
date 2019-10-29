module.exports = {
  runtimeCompiler: true,
  assetsDir: 'static', // For simple configuration of static files in Flask (the "static_folder='client/dist/static'" part in app.py)
  // needs to change for django-rest to serve up final built files.
  devServer: {
    proxy: 'http://10.200.104.228:8001' // hardcoded to a rosalind ip right now. Config up later.
  },
  configureWebpack: {
    devtool: 'source-map'
  },
  css: {
    loaderOptions: {
      sass: {
        data: `
          @import "@/styles/_variables.scss";
          @import "@/styles/_common.scss";
        `
      }
    }
  }
}
