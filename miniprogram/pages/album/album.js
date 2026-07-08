// 群相册页：展示从截图中提取、按事件聚类的照片（当前为占位数据）
Page({
  data: {
    clusters: [
      {
        name: '示例 · 周末聚餐',
        photos: [
          { url: '', caption: '老张生日局，大家在等蛋糕上桌' }
        ]
      }
    ]
  },

  previewPhoto(e) {
    const { cluster, index } = e.currentTarget.dataset
    const urls = this.data.clusters[cluster].photos.map((p) => p.url).filter(Boolean)
    if (urls.length) {
      wx.previewImage({ urls, current: urls[index] })
    }
  }
})
