# ================================================
#  ai_clients.py
# -----------------------------------------------
# 役割：
# - Claude API の呼び出しを一元管理する
# - call_gpt    → Claude claude-opus に委譲（司令塔・構造化・タグ分類など）
# - call_claude → Claude claude-sonnet に委譲（実装・検証など）
# - run_memory_improvement → 基準進化AIの外部メモリ改善
# ================================================

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 用途別モデル
GPT_MODEL    = "claude-opus-4-6"     # 司令塔・構造化・分類など思考系
CLAUDE_MODEL = "claude-sonnet-4-6"   # 実装・検証など生成系


def call_gpt(prompt: str) -> str:
    """
    司令塔AI・構造化AI・タグ分類など「思考・判断」系の呼び出し。
    ※ 関数名は既存コードとの互換性のため call_gpt のまま。
    """
    message = client.messages.create(
        model=GPT_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_claude(prompt: str) -> str:
    """
    実装AI・検証AIなど「生成・検証」系の呼び出し。
    """
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def run_memory_improvement(
    user_request: str,
    supervisor: str,
    design: str,
    code: str,
    final_code: str,
    loop_history: list,
    score_json: dict,
    next_tips: str,
) -> str:
    """
    基準進化AI：外部メモリを改善・進化させる。
    重複排除・案件最適化・スコア傾向分析を行う。
    """
    prompt = f"""
あなたは制作パイプラインの 基準進化AI です。

【目的】
外部メモリを肥大化させず、重複を排除し、長期的に進化させる。

【改善方針】
- 重複している基準を統合・削除する
- 案件タイプに最適化した基準に更新する
- スコア傾向から弱点を分析し、司令塔AIへフィードバックする

【参照情報】
■ 依頼内容：
{user_request}

■ 司令塔AI出力：
{supervisor}

■ 構造化AI出力：
{design}

■ 初回実装：
{code}

■ 最終実装：
{final_code}

■ 改善履歴：
{loop_history}

■ スコア：
{score_json}

■ 次回改善ポイント：
{next_tips}

【出力形式】
改善後の基準データ：
重複削除ログ：
案件タイプ最適化ログ：
スコア傾向ログ：
司令塔AIへのフィードバック：
基準進化AI自身の学習ログ：
"""
    return call_gpt(prompt)
