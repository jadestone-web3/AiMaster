"""
AiMaster AI 服务 - 集成 MiniMax API
"""
import json
import re
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from .config import settings
from .models import Task, TaskStatus


class AIService:
    """AI 改写服务"""

    def __init__(self):
        self.api_key = settings.MINIMAX_API_KEY
        self.base_url = settings.MINIMAX_BASE_URL
        self.model = settings.MINIMAX_MODEL
        self.mock_mode = settings.AI_MOCK_MODE

    async def rewrite_article(self, task_id: str, db: Session):
        """
        异步处理文章改写

        Args:
            task_id: 任务ID
            db: 数据库会话
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        try:
            # 更新状态为改写中
            task.status = TaskStatus.REWRITING
            task.progress = 10
            db.commit()

            # 获取原始文章内容
            original_title = task.original_title or ""
            original_content = task.original_content or ""

            if self.mock_mode:
                # 模拟模式
                await self._mock_rewrite(task, db)
            else:
                # 真实 API 调用
                await self._real_rewrite(task, db, original_title, original_content)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.progress = 0
            db.commit()
            print(f"❌ 任务 {task_id} 失败: {e}")

    async def _mock_rewrite(self, task: Task, db: Session):
        """模拟改写"""
        import asyncio
        await asyncio.sleep(1)
        task.progress = 30
        db.commit()

        await asyncio.sleep(1)
        task.progress = 60
        db.commit()

        await asyncio.sleep(1)

        # 模拟改写：添加前缀
        task.rewritten_title = f"【AI改写】{task.original_title}"
        task.rewritten_content = f"以下是经过AI改写的内容：\n\n{task.original_content}"
        if task.original_images:
            task.rewritten_content += "\n\n[图片已保留]"

        task.status = TaskStatus.REWRITTEN
        task.progress = 100
        db.commit()
        print(f"✅ 任务 {task.id} 模拟改写完成")

    async def _real_rewrite(self, task: Task, db: Session, title: str, content: str):
        """调用 MiniMax API 进行真实改写"""
        import httpx
        import asyncio

        await asyncio.sleep(1)
        task.progress = 30
        db.commit()

        # 构建提示词
        prompt = self._build_rewrite_prompt(title, content)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 4096,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }
                )

                await asyncio.sleep(0.5)
                task.progress = 80
                db.commit()

                if response.status_code == 200:
                    result = response.json()
                    text = result["content"][0]["text"]

                    # 解析返回内容
                    rewritten_title, rewritten_content = self._parse_rewrite_result(text, title)

                    task.rewritten_title = rewritten_title
                    task.rewritten_content = rewritten_content
                    task.ai_model = self.model
                    task.ai_tokens_used = result.get("usage", {}).get("output_tokens", 0)
                    task.status = TaskStatus.REWRITTEN
                    task.progress = 100
                    db.commit()
                    print(f"✅ 任务 {task.id} 真实改写完成，消耗 {task.ai_tokens_used} tokens")
                else:
                    raise Exception(f"API 返回错误: {response.status_code} - {response.text}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.progress = 0
            db.commit()
            raise e

    def _build_rewrite_prompt(self, title: str, content: str) -> str:
        """构建改写提示词"""
        return f"""请帮我改写以下文章，要求：
1. 保持文章的核心意思不变
2. 优化表达方式，提升可读性
3. 适当调整文章结构
4. 改写后的内容要通顺流畅

原文标题：{title}

原文内容：
{content}

请直接返回改写后的标题和内容，格式如下：
标题：<改写后的标题>
内容：
<改写后的内容>"""

    def _parse_rewrite_result(self, text: str, original_title: str) -> tuple:
        """解析改写结果"""
        lines = text.strip().split("\n")

        rewritten_title = original_title
        rewritten_content = text

        # 尝试提取标题
        for line in lines:
            if line.startswith("标题：") or line.startswith("标题:"):
                rewritten_title = line.split("：", 1)[-1].split(":", 1)[-1].strip()
                break

        # 尝试提取内容
        content_start = text.find("内容：")
        if content_start == -1:
            content_start = text.find("内容:")
        if content_start != -1:
            rewritten_content = text[content_start + len("内容："):].strip()
        else:
            # 如果找不到分隔符，整个文本作为内容
            rewritten_content = text

        return rewritten_title, rewritten_content


# 全局单例
ai_service = AIService()
