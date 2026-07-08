"""调用 Claude：群聊上下文总结 + 图片理解（生成图片描述）。"""

import base64
import time

import anthropic

MODEL = "claude-sonnet-5"

SUMMARY_SYSTEM = """你是微信群聊总结助手。用户会给你一段群聊记录（每行格式：[时间] 昵称: 内容，
其中 [图片] 开头的行是群友发的图片，后面是图片内容描述）。

请输出一份简洁的中文总结，包含：
📌 主要话题（每个话题一两句话，写清参与的人和结论）
✅ 结论/待办/约定（没有就省略这一节）
💬 金句（值得记录的原话，标注发言人；没有就省略）

要求：口语化、可以直接发回群里，总长度不超过 500 字，不要用 markdown 标题语法。
如果用户在最后附加了具体问题，优先围绕问题回答，再给简短总结。"""

CAPTION_SYSTEM = (
    "用一句话（30 字内）描述这张微信群聊里分享的图片的内容和要点，"
    "如果是表情包请说明它表达的情绪，直接输出描述，不要前缀。"
)

_client = anthropic.Anthropic()  # 读取环境变量 ANTHROPIC_API_KEY


def summarize(messages: list[dict], question: str = "") -> str:
    """把消息列表拼成 transcript 交给模型总结。question 是 @bot 时附带的问题。"""
    lines = []
    for m in messages:
        t = time.strftime("%m-%d %H:%M", time.localtime(m["ts"]))
        prefix = "[图片] " if m["type"] == "image" else ""
        lines.append(f"[{t}] {m['nickname']}: {prefix}{m['content']}")
    transcript = "\n".join(lines)

    user_text = f"以下是群聊记录：\n\n{transcript}"
    if question.strip():
        user_text += f"\n\n用户的问题：{question.strip()}"

    resp = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SUMMARY_SYSTEM,
        messages=[{"role": "user", "content": user_text}],
    )
    return resp.content[0].text.strip()


def caption_image(image_path: str) -> str:
    """让视觉模型给群里的图片生成一句话描述，存入上下文。"""
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode()
    suffix = image_path.rsplit(".", 1)[-1].lower()
    media_type = "image/png" if suffix == "png" else "image/jpeg"

    resp = _client.messages.create(
        model=MODEL,
        max_tokens=128,
        system=CAPTION_SYSTEM,
        messages=[{
            "role": "user",
            "content": [{
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": data},
            }],
        }],
    )
    return resp.content[0].text.strip()
