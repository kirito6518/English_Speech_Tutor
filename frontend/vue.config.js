module.exports = {
  devServer: {
    host: '0.0.0.0',  // 可访问任何外部 IP
    port: 8080,
    allowedHosts: 'all', // 替代disableHostCheck
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
    compress: false,  // 禁用压缩
    client: {
      webSocketURL: 'ws://localhost:8080/ws'  // 更新为有效的 WebSocket URL
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // 后端 API 地址
        changeOrigin: true,
        secure: false,
      },
      '/api/external': {
        target: 'https://se-project-2024winter.oss-cn-shanghai.aliyuncs.com',  // 外部资源地址
        changeOrigin: true,
        pathRewrite: { '^/api/external': '' },
      },
    },
  },
  chainWebpack: config => {
    config.module
      .rule('glb')
      .test(/\.glb$/)
      .use('file-loader')
      .loader('file-loader')
      .options({
        name: 'models/[name].[hash:8].[ext]',
      });
  },
};
