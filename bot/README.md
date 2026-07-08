# 群聊总结 bot（内部 demo）

把一个微信**小号**登录在 Windows 电脑上，通过 [WeChatFerry](https://github.com/lich0821/WeChatFerry) hook 微信 PC 客户端实现：

- bot 被拉进群后，**自动记录群消息**（文本存原文；图片先送 Claude 视觉模型生成一句话描述再入库）
- 群里 **@bot** → 取该群最近 200 条上下文 → Claude 生成总结 → 回复到群里并 @ 提问者
- @bot 时可以带问题，例如「@小忆 周六聚餐最后定在哪了？」，会优先回答问题再给简短总结

## ⚠️ 使用前必读

微信**没有官方 bot API**，本方案通过 hook PC 客户端实现，**违反微信用户协议，存在封号风险**：

- 只用**小号**登录，不要用主力微信
- 只拉进自己的测试群/内部群
- 不要高频、大量发消息
- 仅限内部 demo，**不可作为对外产品上线**（对外请走仓库根 README 里的合规形态）

## 环境要求

- Windows 10/11（wcferry 只支持 Windows）
- 微信 PC 客户端：**版本必须与 wcferry 匹配**，安装前先看 [WeChatFerry README](https://github.com/lich0821/WeChatFerry) 顶部标注的支持版本（一般是指定的 3.9.x），去它的 release 页下载对应安装包，并关闭微信自动更新
- Python 3.10+
- Anthropic API Key

## 跑起来

```powershell
cd bot
pip install -r requirements.txt

# 配置 API Key
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# 1. 先用小号登录微信 PC 客户端
# 2. 启动 bot（首次会注入 dll，微信若弹更新提示选择忽略）
python main.py
```

看到 `bot 已登录，wxid=...` 后：

1. 用另一个微信把小号拉进测试群
2. 群里正常聊天、发图片 —— bot 会静默记录
3. 群里 @小号昵称，等几秒即可收到总结

## 可调参数（环境变量）

| 变量 | 默认 | 说明 |
|------|------|------|
| `ANTHROPIC_API_KEY` | — | 必填 |
| `BOT_CONTEXT_SIZE` | 200 | 每次总结取最近多少条消息 |
| `BOT_DB` | messages.db | SQLite 存储路径 |

## 代码结构

```
bot/
├── main.py        # 消息循环：收群消息、@触发总结、图片下载
├── storage.py     # SQLite 消息存储（按群、按时间）
├── summarizer.py  # Claude 调用：上下文总结 + 图片描述
└── requirements.txt
```

## 常见问题

- **启动报版本不匹配**：微信 PC 版本和 wcferry 不配套，按 wcferry README 装指定版本
- **收不到消息**：确认微信在同一台机器上已登录，且 `main.py` 在微信启动后运行
- **图片总结不出现**：图片是异步下载 + 识图的，刚发的图过几秒才会入库
- **备选方案**：如果 hook 方案在你的环境跑不通，可换 [wechaty](https://wechaty.js.org/) + puppet-xp（Node 生态，同为 Windows hook 原理）
