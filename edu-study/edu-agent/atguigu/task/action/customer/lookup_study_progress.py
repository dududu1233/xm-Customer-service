# === 文件：atguigu/task/action/customer/lookup_study_progress.py ===
# 角色：自定义 action，查询已报名班次的学习进度。
# 功能：ActionLookupStudyProgress 通过 edu-data 调 /me/cohorts 列表，按班次名模糊匹配后取 /me/cohorts/{id}/progress 拼装成可读文本，写入 updated_slots。
# 入口：被 action/builder 自动发现注册；由 executor 在 study_progress_query flow 中触发。
# 出口：atguigu.domain.messages、atguigu.domain.state、atguigu.infrastructure.http_client、atguigu.task.action.base。
import asyncio
from typing import Any

from atguigu.domain.state import DialogueState
from atguigu.infrastructure import http_client
from atguigu.task.action.base import Action, ActionResult
from atguigu.config.settings import settings


class ActionLookupStudyProgress(Action):
    name = "action_lookup_study_progress"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        """
        职责：按班次名匹配班次后查询学习进度
        Args:
            action_kwargs:
            state:

        Returns:

        """
        cohort_name = (state.active_task.slots.get("cohort_name") or "").strip()

        try:
            # 1. 拉取当前用户的班次列表（X-User-Id 由 http_client 钩子自动注入）
            r1 = await http_client.http_client.get(
                f"{settings.commerce_api_base_url.rstrip('/')}/api/v1/me/cohorts?pageNo=1&pageSize=100"
            )
            data1 = r1.json().get("data") or {}
            my_cohorts = data1.get("list", []) or []
        except Exception:
            my_cohorts = []

        if not my_cohorts:
            return ActionResult(updated_slots={
                "study_progress": "你当前没有任何有效班次，无法查询学习进度。",
            })

        # 2. 本地匹配班次名（cohort_name 或 series_name 包含输入）
        matched = None
        for c in my_cohorts:
            if cohort_name and cohort_name in str(c.get("cohortName", "")):
                matched = c
                break
            if cohort_name and cohort_name in str(c.get("seriesName", "")):
                matched = c
                break
        if matched is None:
            return ActionResult(updated_slots={
                "study_progress": f"没有找到班次「{cohort_name}」，请确认班次名称是否正确。",
            })

        cohort_id = matched["cohortId"]
        try:
            r2 = await http_client.http_client.get(
                f"{settings.commerce_api_base_url.rstrip('/')}/api/v1/me/cohorts/{cohort_id}/progress"
            )
            progress = r2.json().get("data") or {}
        except Exception:
            return ActionResult(updated_slots={
                "study_progress": f"班次「{matched.get('cohortName')}」进度查询失败，请稍后再试。",
            })

        return ActionResult(updated_slots={
            "cohort_name": matched.get("cohortName", ""),
            "study_progress": _format_progress(matched, progress),
        })


def _format_progress(cohort: dict[str, Any], progress: dict[str, Any]) -> str:
    """
    把班次信息与学习进度拼成一段可读中文
    """
    parts: list[str] = []
    name = cohort.get("cohortName") or ""
    series = cohort.get("seriesName") or ""
    if name:
        parts.append(f"班次：{name}")
    if series:
        parts.append(f"所属课程：{series}")
    if cohort.get("enrollStatusCode"):
        parts.append(f"履约状态：{cohort['enrollStatusCode']}")

    att = progress.get("attendance") or {}
    if att:
        parts.append(
            f"出勤：{att.get('presentCount', 0)}/{att.get('totalSessions', 0)} 次"
        )

    video = progress.get("video") or {}
    if video and video.get("totalVideos"):
        parts.append(
            f"视频：已完成 {video.get('completedVideos', 0)}/{video.get('totalVideos', 0)} 个"
        )

    hw = progress.get("homework") or {}
    if hw and hw.get("totalHomeworks"):
        parts.append(
            f"作业：已提交 {hw.get('submittedCount', 0)}/{hw.get('totalHomeworks', 0)} 份，已批改 {hw.get('correctedCount', 0)} 份"
        )

    exam = progress.get("exam") or {}
    if exam and exam.get("totalExams"):
        parts.append(
            f"考试：已参加 {exam.get('submittedCount', 0)}/{exam.get('totalExams', 0)} 场"
        )

    return "。".join(parts) + "。" if parts else "暂无进度信息。"
