// 首页：上传群聊截图 → 调用云函数解析 → 跳转总结页
Page({
  data: {
    images: [],       // 已选截图的本地临时路径
    maxCount: 20,
    parsing: false
  },

  chooseScreenshots() {
    const remain = this.data.maxCount - this.data.images.length
    if (remain <= 0) {
      wx.showToast({ title: '最多 20 张', icon: 'none' })
      return
    }
    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        const paths = res.tempFiles.map((f) => f.tempFilePath)
        this.setData({ images: this.data.images.concat(paths) })
      }
    })
  },

  removeImage(e) {
    const idx = e.currentTarget.dataset.index
    const images = this.data.images.slice()
    images.splice(idx, 1)
    this.setData({ images })
  },

  async startParse() {
    if (this.data.images.length === 0 || this.data.parsing) return
    this.setData({ parsing: true })
    wx.showLoading({ title: 'AI 解析中…', mask: true })
    try {
      // 1. 截图先上传到云存储
      const fileIDs = await Promise.all(
        this.data.images.map((path, i) =>
          wx.cloud
            .uploadFile({
              cloudPath: `screenshots/${Date.now()}-${i}.jpg`,
              filePath: path
            })
            .then((r) => r.fileID)
        )
      )
      // 2. 调用云函数做对话重建 + 总结
      const res = await wx.cloud.callFunction({
        name: 'summarize',
        data: { fileIDs }
      })
      getApp().globalData.lastSummary = res.result
      wx.hideLoading()
      wx.navigateTo({ url: '/pages/summary/summary' })
    } catch (err) {
      wx.hideLoading()
      console.error('解析失败', err)
      wx.showToast({ title: '解析失败，请重试', icon: 'none' })
    } finally {
      this.setData({ parsing: false })
    }
  }
})
