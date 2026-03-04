# ================================================
#  notion_client.py
#  Notion連携モジュール
# -----------------------------------------------
# 役割：
# - 外部メモリ（判断基準・デザイン基準など）の読み込み
# - プロジェクトレポートの保存
# - スコア履歴の読み込み
#
# Notion は「基礎DB」として利用し、
# AIが参照する基準データやレポートを管理する。
# ================================================

import os
import time
import requests

# --- Notion API の環境変数 ---
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_EXTERNAL_MEMORY_DB = os.getenv("NOTION_EXTERNAL_MEMORY_DB")
NOTION_PROJECT_REPORT_DB = os.getenv("NOTION_PROJECT_REPORT_DB")
NOTION_SCORE_DB = os.getenv("NOTION_SCORE_DB")

# --- 外部メモリのキャッシュ ---
_cache = None
_cache_time = 0
CACHE_EXPIRE_SECONDS = 600  # 10分キャッシュ


# ================================================
#  外部メモリ読み込み
# ================================================
def load_external_memory():
    """
    Notion の「AI外部メモリー」DBから基準データを読み込む。
    現状は1行目の以下の項目を取得する：
    - 判断基準
    - デザイン基準
    - コーディング基準
    - 品質基準
    - 過去レポート

    ※ キャッシュを使い、10分以内の再読み込みを防ぐ。
    """

    global _cache, _cache_time

    # --- キャッシュが有効ならそのまま返す ---
    if _cache and (time.time() - _cache_time < CACHE_EXPIRE_SECONDS):
        return _cache

    # --- Notion DB へクエリ ---
    url = f"https://api.notion.com/v1/databases/{NOTION_EXTERNAL_MEMORY_DB}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    _empty = {
        "judgement": "",
        "design": "",
        "coding": "",
        "quality": "",
        "reports": "",
    }

    try:
        response = requests.post(url, headers=headers, json={})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Notion API Error:", e)
        return _empty

    # --- データが存在しない場合のフォールバック ---
    if not data.get("results"):
        return _empty

    # --- 1行目のプロパティを取得 ---
    row = data["results"][0]["properties"]

    def get_text(field):
        texts = row.get(field, {}).get("rich_text", [])
        return texts[0]["plain_text"] if texts else ""

    memory = {
        "judgement": get_text("判断基準"),
        "design":    get_text("デザイン基準"),
        "coding":    get_text("コーディング基準"),
        "quality":   get_text("品質基準"),
        "reports":   get_text("過去レポート"),
    }

    # --- キャッシュ保存 ---
    _cache = memory
    _cache_time = time.time()

    return memory


# ================================================
#  プロジェクトレポート保存
# ================================================
def save_log_to_notion(project_name: str, tags: list, status: str, report: str):
    """
    Notion の「プロジェクトレポート」DBに制作レポートを保存する。

    保存内容：
    - プロジェクト名
    - タグ（分類）
    - ステータス
    - レポート本文（children として保存）
    """

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Notion の paragraph ブロックは2000文字制限があるため分割する
    MAX_BLOCK_LENGTH = 1900
    children = []
    for i in range(0, len(report), MAX_BLOCK_LENGTH):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": report[i:i + MAX_BLOCK_LENGTH]}}
                ]
            }
        })

    payload = {
        "parent": {"database_id": NOTION_PROJECT_REPORT_DB},
        "properties": {
            "プロジェクト名": {
                "title": [
                    {"type": "text", "text": {"content": project_name}}
                ]
            },
            "タグ": {
                "multi_select": [{"name": tag} for tag in tags]
            },
            "ステータス": {
                "select": {"name": status}
            },
        },
        "children": children,
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code, response.text
    except Exception as e:
        return 500, f"[Notion Error] {str(e)}"


# ================================================
#  スコア履歴読み込み
# ================================================
def load_score_history(limit: int = 10):
    """
    Notion の「スコアDB」から直近のスコア履歴を取得する。
    - 制作時間
    - バグ数
    - 改善ループ数

    ※ 傾向分析用の軽量データとして返す。
    """

    if not NOTION_SCORE_DB:
        return []

    url = f"https://api.notion.com/v1/databases/{NOTION_SCORE_DB}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    payload = {
        "page_size": limit,
        "sorts": [
            {
                "property": "制作日",
                "direction": "descending"
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("スコア履歴取得エラー:", e)
        return []

    results = []

    for row in data.get("results", []):
        props = row["properties"]
        item = {
            "total_time":  props.get("制作時間（秒）", {}).get("number"),
            "bug_count":   props.get("バグ数", {}).get("number"),
            "trial_count": props.get("改善ループ数", {}).get("number"),
            "tag": None,
        }
        results.append(item)

    return results
