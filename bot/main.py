"""群聊总结 bot（内部 demo）— 基于 WeChatFerry hook 微信 PC 客户端。

功能：
  1. bot 小号被拉进群后，自动记录群消息到 SQLite（文本原文；图片先过视觉模型生成描述）
  2. 群里 @bot（可附带问题，如 "@小忆 今天讨论出结论了吗"）→ 取该群最近 N 条上下文 → Claude 总结 → 回复到群并 @提问者

运行环境：Windows + 与 wcferry 版本匹配的微信 PC 客户端（见 bot/README.md）
环境变量：ANTHROPIC_API_KEY
"""

import logging
import os
import re
from queue import Empty
from tempfile import mkdtemp

from wcferry import Wcf, WxMsg

from storage import MessageStore
from summarizer import caption_image, summarize

CONTEXT_SIZE = int(os.environ.get("BOT_CONTEXT_SIZE", "200"))  # 每次总结取多少条上下文
IMG_DIR = mkdtemp(prefix="wxbot-img-")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot")

TYPE_TEXT = 0x01
TYPE_IMAGE = 0x03


def nickname_of(wcf: Wcf, wxid: str, roomid: str) -> str:
    return wcf.get_alias_in_chatroom(wxid, roomid) or wxid


def strip_at(content: str) -> str:
    """去掉消息里的 @xxx 片段，留下真正的问题文本。@后缀是特殊空格  。"""
    return re.sub(r"@[^  ]+[  ]?", "", content).strip()


def handle_group_msg(wcf: Wcf, store: MessageStore, self_wxid: str, msg: WxMsg):
    roomid = msg.roomid
    nickname = nickname_of(wcf, msg.sender, roomid)

    # —— @bot：触发总结 ——
    if msg.type == TYPE_TEXT and msg.is_at(self_wxid):
        question = strip_at(msg.content)
        log.info("群 %s 被 @，问题：%r", roomid, question)
        history = store.recent(roomid, CONTEXT_SIZE)
        if not history:
            wcf.send_text(f"@{nickname} 我刚进群，还没攒到上下文，等大家聊一会儿再 @ 我吧～", roomid, msg.sender)
            return
        try:
            reply = summarize(history, question)
        except Exception:
            log.exception("总结失败")
            wcf.send_text(f"@{nickname} 总结失败了，稍后再试一下", roomid, msg.sender)
            return
        wcf.send_text(f"@{nickname}\n{reply}", roomid, msg.sender)
        return

    # —— 普通文本：入库 ——
    if msg.type == TYPE_TEXT:
        store.add(roomid, msg.sender, nickname, "text", msg.content)
        return

    # —— 图片：下载 → 视觉模型生成描述 → 入库 ——
    if msg.type == TYPE_IMAGE:
        try:
            path = wcf.download_image(msg.id, msg.extra, IMG_DIR)
            caption = caption_image(path) if path else "（图片下载失败）"
        except Exception:
            log.exception("图片处理失败")
            caption = "（图片，内容未识别）"
        store.add(roomid, msg.sender, nickname, "image", caption)
        log.info("图片入库：%s -> %s", nickname, caption)


def main():
    wcf = Wcf()
    self_wxid = wcf.get_self_wxid()
    log.info("bot 已登录，wxid=%s，等待群消息…", self_wxid)

    store = MessageStore(os.environ.get("BOT_DB", "messages.db"))
    wcf.enable_receiving_msg()

    try:
        while wcf.is_receiving_msg():
            try:
                msg = wcf.get_msg()
            except Empty:
                continue
            if not msg.from_group():
                continue  # demo 只处理群聊
            if msg.sender == self_wxid:
                continue  # 忽略自己发的
            try:
                handle_group_msg(wcf, store, self_wxid, msg)
            except Exception:
                log.exception("处理消息失败：%s", msg)
    except KeyboardInterrupt:
        pass
    finally:
        wcf.cleanup()
        log.info("bot 已退出")


if __name__ == "__main__":
    main()
