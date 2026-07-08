// 总结结果页：展示话题、待办、金句
Page({
  data: {
    summary: null
  },

  onLoad() {
    const summary = getApp().globalData.lastSummary
    this.setData({ summary })
  },

  onShareAppMessage() {
    return {
      title: '我们群今天聊了这些，快来看看',
      path: '/pages/index/index'
    }
  }
})
