App({
  globalData: {
    // 最近一次解析出的总结结果，供 summary 页读取
    lastSummary: null
  },

  onLaunch() {
    if (wx.cloud) {
      wx.cloud.init({
        // TODO: 替换为你的云开发环境 ID
        env: 'YOUR_CLOUD_ENV_ID',
        traceUser: true
      })
    }
  }
})
