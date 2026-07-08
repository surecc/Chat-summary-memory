// 云函数 summarize：接收截图 fileID 列表，调用多模态大模型重建对话并生成结构化总结
//
// 流程：
//   1. 从云存储下载截图
//   2. 送入视觉大模型（如 Claude），要求重建对话时间线并输出 JSON
//   3. 返回 { topics, todos, quotes, photos } 给小程序端
//
// 部署前：在云函数环境变量中配置 ANTHROPIC_API_KEY

const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

const SYSTEM_PROMPT = `你是一个微信群聊截图分析助手。用户会给你一组按顺序排列的群聊截图。
请：
1. 重建对话：识别每条消息的发言人昵称、内容和大致时间，注意截图之间可能有重叠，需去重。
2. 理解截图中出现的照片和表情包在聊天语境中的含义。
3. 输出严格的 JSON（不要包含其他文字），结构如下：
{
  "topics": [{ "title": "话题标题", "detail": "一段话总结，含参与者与结论" }],
  "todos": ["群里达成的约定、待办、接龙结果"],
  "quotes": [{ "text": "值得记录的原话", "speaker": "发言人昵称" }],
  "photos": [{ "index": 截图序号, "caption": "结合聊天语境的一句话描述" }]
}`

exports.main = async (event) => {
  const { fileIDs = [] } = event
  if (fileIDs.length === 0) {
    return { error: '未收到截图' }
  }

  // 1. 下载截图并转 base64
  const images = await Promise.all(
    fileIDs.map(async (fileID) => {
      const res = await cloud.downloadFile({ fileID })
      return res.fileContent.toString('base64')
    })
  )

  // 2. 调用多模态大模型
  const content = images.map((data) => ({
    type: 'image',
    source: { type: 'base64', media_type: 'image/jpeg', data }
  }))
  content.push({ type: 'text', text: '请分析以上群聊截图并按要求输出 JSON。' })

  const resp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': process.env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-sonnet-5',
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content }]
    })
  })

  if (!resp.ok) {
    const detail = await resp.text()
    console.error('模型调用失败', resp.status, detail)
    return { error: '模型调用失败' }
  }

  const data = await resp.json()
  const text = data.content[0].text

  try {
    return JSON.parse(text)
  } catch (e) {
    console.error('模型输出不是合法 JSON', text)
    return { error: '解析失败' }
  }
}
