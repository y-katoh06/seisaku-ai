# ================================================
#  ai_clients.py
# -----------------------------------------------
# 役割：
# - OpenAI / Anthropic の呼び出しを一元管理する
#
# モデル割り当て：
# - 司令塔AI    → Claude Sonnet（判断・構造化）
# - 構造化AI    → GPT-4o（設計・整理）
# - 実装AI      → Claude Sonnet（コード生成）
# - 検証AI      → Claude Opus（精度重視のバグ検出）
# - 基準進化AI  → GPT-4o（分析・改善）
# - シミュレーション系 → GPT-4o mini（軽量・文章生成）
# ================================================

import os
from anthropic import Anthropic
from openai import OpenAI

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client    = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- モデル定義 ---
CLAUDE_SONNET = "claude-sonnet-4-6"   # 司令塔AI・実装AI
CLAUDE_OPUS   = "claude-opus-4-6"     # 検証AI（精度重視）
GPT4O         = "gpt-4o"              # 構造化AI・基準進化AI
GPT4O_MINI    = "gpt-4o-mini"         # シミュレーション系（軽量）


def _call_anthropic(prompt: str, model: str, max_tokens: int = 8192) -> str:
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_openai(prompt: str, model: str, max_tokens: int = 4096) -> str:
    response = openai_client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def call_supervisor(prompt: str) -> str:
    """司令塔AI：Claude Sonnet（判断・構造化）"""
    return _call_anthropic(prompt, CLAUDE_SONNET)


def call_gpt(prompt: str) -> str:
    """
    構造化AI・基準進化AI・タグ分類など：GPT-4o
    ※ 関数名は既存コードとの互換性のため call_gpt のまま。
    """
    return _call_openai(prompt, GPT4O)


def call_claude(prompt: str) -> str:
    """実装AI：Claude Sonnet（コード生成）"""
    return _call_anthropic(prompt, CLAUDE_SONNET)


def call_debugger(prompt: str) -> str:
    """検証AI：Claude Opus（精度重視のバグ検出）"""
    return _call_anthropic(prompt, CLAUDE_OPUS)


def call_simulation(prompt: str) -> str:
    """シミュレーション系AI：GPT-4o mini（軽量・文章生成）"""
    return _call_openai(prompt, GPT4O_MINI)


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
    """基準進化AI：GPT-4o（分析・改善）"""
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
    return _call_openai(prompt, GPT4O)
