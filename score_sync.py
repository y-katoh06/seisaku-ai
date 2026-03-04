# ================================================
#  score_sync.py
# -----------------------------------------------
# 役割：
# - Supabase に送ったスコアを Notion のスコアDBにも保存する
# - Notion は「履歴・可視化用DB」として利用する
#
# Supabase：高速処理・計算
# Notion：人間が見るレポート・履歴管理
# ================================================

import os
import requests
from datetime import datetime

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_SCORE_DB = os.getenv("NOTION_SCORE_DB")


def save_score_to_notion_score_db(score_json: dict, meta: dict | None = None):
    """
    Notion の「AI制作スコアDB」にスコアを保存する。

    保存内容：
    - プロジェクトID
    - 制作時間（秒）
    - バグ数
    - 改善ループ数
    - 制作日
    - プロジェクト名（meta）
    - タグ（meta）
    - 企業名（meta）
    - 担当者名（meta）
    """

    if not NOTION_SCORE_DB:
        print("NOTION_SCORE_DB が設定されていません。")
        return

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    project_name = (
        meta.get("project_name") if meta
        else f"Project {score_json.get('project_id')}"
    )
    tags         = meta.get("tags", [])         if meta else []
    company_name = meta.get("company_name", "") if meta else ""
    client_name  = meta.get("client_name", "")  if meta else ""

    properties = {
        "プロジェクトID":   {"number": score_json.get("project_id")},
        "制作時間（秒）":   {"number": score_json.get("total_time")},
        "バグ数":           {"number": score_json.get("bug_count")},
        "改善ループ数":     {"number": score_json.get("trial_count")},
        "制作日":           {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
        "プロジェクト名":   {
            "title": [{"type": "text", "text": {"content": project_name}}]
        },
    }

    if tags:
        properties["タグ"] = {"multi_select": [{"name": t} for t in tags]}

    if company_name:
        properties["企業名"] = {
            "rich_text": [{"type": "text", "text": {"content": company_name}}]
        }

    if client_name:
        properties["担当者名"] = {
            "rich_text": [{"type": "text", "text": {"content": client_name}}]
        }

    payload = {
        "parent": {"database_id": NOTION_SCORE_DB},
        "properties": properties,
    }

    try:
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print("Notion Score DB Write Error:", e)
