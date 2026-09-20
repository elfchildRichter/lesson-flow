from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class TierLimits(TypedDict):
    tier_key: str
    name_zh: str
    name_en: str
    daily_credits: int
    enable_web_search: bool
    enable_vlm: bool
    max_upload_mb: int
    allowed_departments: List[str]
    is_unlimited: bool


ACTION_CREDIT_COSTS: Dict[str, int] = {
    "deck": 50,          # 生成教學簡報 (大綱+內容+逐頁講稿)
    "handout": 30,       # 生成 A4 隨堂講義
    "quiz": 20,          # 生成單元試卷評量 (5 題含詳解)
    "refine": 3,         # AI 局部微調 (單頁講稿潤飾 / 單題重新出題)
    "vlm_parse": 30,     # 進階圖表與公式解析 (含圖表與數學公式)
    "parse": 5,          # 標準教材解析 (純文字與章節向量索引)
    "ask": 1,            # 文件問答 / AI 助教提問
    "upload": 0,         # 上傳檔案基礎校驗
}


TIER_CONFIGS: Dict[str, TierLimits] = {
    "teacher_trial": {
        "tier_key": "teacher_trial",
        "name_zh": "教師試用版",
        "name_en": "Teacher Free Trial",
        "daily_credits": 100,
        "enable_web_search": False,
        "enable_vlm": False,
        "max_upload_mb": 10,
        "allowed_departments": ["academic", "marketing", "operations"],
        "is_unlimited": False,
    },
    "teacher_pro": {
        "tier_key": "teacher_pro",
        "name_zh": "教師專業版",
        "name_en": "Teacher Pro",
        "daily_credits": 1000,
        "enable_web_search": True,
        "enable_vlm": True,
        "max_upload_mb": 30,
        "allowed_departments": ["academic", "marketing", "operations"],
        "is_unlimited": False,
    },
    "institution": {
        "tier_key": "institution",
        "name_zh": "機構/學校版",
        "name_en": "Institution",
        "daily_credits": 10000,
        "enable_web_search": True,
        "enable_vlm": True,
        "max_upload_mb": 100,
        "allowed_departments": ["academic", "marketing", "operations"],
        "is_unlimited": False,
    },
    "admin": {
        "tier_key": "admin",
        "name_zh": "管理員無限版",
        "name_en": "Admin Unlimited",
        "daily_credits": -1,
        "enable_web_search": True,
        "enable_vlm": True,
        "max_upload_mb": 500,
        "allowed_departments": ["academic", "marketing", "operations", "devops"],
        "is_unlimited": True,
    },
}


def get_tier_config(tier_key: str | None = None, role: str | None = None) -> TierLimits:
    """Returns tier limits configuration based on user tier_key or role."""
    if role == "admin" or tier_key == "admin":
        return TIER_CONFIGS["admin"]
    if tier_key and tier_key in TIER_CONFIGS:
        return TIER_CONFIGS[tier_key]
    # Default fallback for regular users and guests is teacher_trial
    return TIER_CONFIGS["teacher_trial"]

