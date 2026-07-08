// 回忆页：周回忆卡片 / 月度记忆册 / 年度群报告 入口（当前为占位）
Page({
  data: {
    entries: [
      { key: 'weekly', title: '本周群回忆卡片', desc: '高光时刻 + 最佳照片 + 金句，一张长图分享回群', ready: false },
      { key: 'monthly', title: '月度群记忆册', desc: 'H5 翻页相册，AI 撰写的叙事小结', ready: false },
      { key: 'yearly', title: '年度群报告', desc: '群聊数据 + 年度金句 + 年度合照', ready: false }
    ]
  },

  openEntry(e) {
    const key = e.currentTarget.dataset.key
    const entry = this.data.entries.find((it) => it.key === key)
    if (!entry.ready) {
      wx.showToast({ title: '多上传几次截图，回忆就攒起来了', icon: 'none' })
    }
  }
})
