# ================================================
#  notion_writer.py
# -----------------------------------------------
# 役割：
# - Supabase Edge Function（save-score）へ制作スコアを送信する
#
# ※ Supabase は「高速処理・スコア計算用DB」として利用する
# ================================================

import os
import json
import requests

# --- Supabase Edge Function の環境変数 ---
SUPABASE_SCORE_URL = os.getenv("SUPABASE_SCORE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def send_score_to_supabase(score_json: dict):
    """
    Supabase Edge Function（save-score）に制作スコアを送信する。

    送信内容：
    - project_id
    - total_time
    - bug_count
    - trial_count

    ※ Supabase 側でスコアDBに保存する。

    ※ 旧名: send_score_to_notion（誤解を招く名前だったため変更）
    """

    if not SUPABASE_SCORE_URL or not SUPABASE_SERVICE_KEY:
        return {
            "status": "error",
            "message": "Supabase の環境変数が設定されていません。"
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }

    try:
        response = requests.post(
            SUPABASE_SCORE_URL,
            headers=headers,
            data=json.dumps(score_json)
        )
        return {
            "status": response.status_code,
            "response": response.text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# 後方互換のためのエイリアス（既存コードが壊れないように）
send_score_to_notion = send_score_to_supabase
