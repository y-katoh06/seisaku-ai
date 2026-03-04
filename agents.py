# ================================================
#  agents.py
# -----------------------------------------------
# 役割：
# - AI制作会社の中核となる「AIパイプライン」を定義する
# - 司令塔AI → 構造化AI → 実装AI → 検証AI の流れを管理
# - プロジェクト実行（run_project）を統合
# - スコア計算、レポート生成、基準進化AIによる学習まで一括処理
# ================================================

import time

from ai_clients import call_gpt, call_claude, run_memory_improvement
from notion_client import save_log_to_notion, load_external_memory
from notion_writer import send_score_to_supabase
from score_sync import save_score_to_notion_score_db

# 検証AIが「問題なし」と判断したときに使う明示的なマーカー
NO_BUG_MARKER = "【問題なし】"


# ================================================
#  バグ数カウント（検証AIの出力解析）
# ================================================
def count_bug_points(debug_text: str) -> int:
    if NO_BUG_MARKER in debug_text:
        return 0
    if "【問題点】" not in debug_text:
        return 0
    section = debug_text.split("【問題点】")[1]
    if "【分類】" in section:
        section = section.split("【分類】")[0]
    lines = section.split("\n")
    return len([l for l in lines if l.strip().startswith("-")])


def _has_no_bugs(debug_text: str) -> bool:
    if NO_BUG_MARKER in debug_text:
        return True
    return count_bug_points(debug_text) == 0


# ================================================
#  司令塔AI（旧：統括AI）
# ================================================
def run_supervisor(user_request: str, company_name: str, client_name: str):
    """
    司令塔AI：
    - 依頼内容を意味で分類し、制作仕様書を生成
    - 案件タイプ × 目的タイプに応じて判断基準を切り替え
    - チェックリストを承認
    """
    memory = load_external_memory()

    prompt = f"""
あなたは制作パイプラインの 司令塔AI です。

────────────────────────
【外部メモリー（Notion）】
────────────────────────
【判断基準】
{memory["judgement"]}

【デザイン基準】
{memory["design"]}

【コーディング基準】
{memory["coding"]}

【品質基準】
{memory["quality"]}

【過去レポート】
{memory["reports"]}

────────────────────────
【依頼内容】
{user_request}

【企業名】
{company_name}

【担当者名】
{client_name}

────────────────────────
【入力チェック】
企業名または担当者名が未入力の場合は、
制作仕様の提示に進まず、以下の形式で返答してください。

- 「企業名が未入力です。入力してください。」
- 「担当者名が未入力です。入力してください。」

────────────────────────
【役割】
- 依頼内容を意味で分類し、制作仕様を簡潔に構造化する
- 推測は（推測）として隔離し、提案扱いで提示する
- リスクは内部管理とし、仕様書には注意点のみ記載する
- 案件タイプ × 目的タイプに応じて判断基準を切り替える

【判断優先順位】
1. 目的（ビジネスゴール）
2. 情報構造の適切さ
3. デザイン品質
4. 実装品質

────────────────────────
【出力形式】
制作仕様書
- 目的：
- 要件：
- 制作範囲：
- 制作物：
- 制作条件：
- 注意点：
- 案件タイプ：
- 目的タイプ：
- 制作方針（根拠つき）：
- 成果物DBに必要な情報：

チェックリスト（司令塔AI承認版）
- 必須要素：
- 構造要件：
- 実装要件：
- 表現要件：
- 注意点：

補足（推測）
- （推測）ターゲット：
- （推測）背景：
- （推測）競合：

GO確認
「この内容で制作を開始してよいですか？」
"""
    return call_gpt(prompt)


# ================================================
#  構造化AI（旧：設計AI）
# ================================================
def run_designer(instruction: str):
    """
    構造化AI：
    - 司令塔AIの仕様書を100%反映した構造案を作成
    - 実装AIが迷わないように作業仕様の草案を生成
    - 判断はしない（判断は司令塔AIのみ）
    """
    memory = load_external_memory()

    prompt = f"""
あなたは制作パイプラインの 構造化AI（中間管理職） です。

────────────────────────
【外部メモリー（Notion）】
────────────────────────
【判断基準】
{memory["judgement"]}

【デザイン基準】
{memory["design"]}

【コーディング基準】
{memory["coding"]}

【品質基準】
{memory["quality"]}

────────────────────────
【最重要ルール】
- 司令塔AIの仕様書を100%反映すること
- 判断はしない（判断は司令塔AIのみ）

────────────────────────
【出力形式】
【構造案】
- 全体構造：
- 各要素の目的と役割：

【作業方針】
- 情報整理方針：
- 表現方針：
- 必要素材：

【チェックリスト草案（司令塔AI確認用）】
- 必須要素（草案）：
- 構造要件（草案）：
- 実装要件（草案）：
- 表現要件（草案）：
- 注意点（草案）：

────────────────────────
司令塔AIの指示：
{instruction}
"""
    return call_gpt(prompt)


# ================================================
#  実装AI（旧：コーディングAI）
# ================================================
def run_coder(design_output: str):
    """
    実装AI：
    - 司令塔AIが承認したチェックリストのみを参照
    - 構造化AIの草案は参照しない
    - 保守性・再現性を最優先に実装
    """
    memory = load_external_memory()

    prompt = f"""
あなたは制作パイプラインの 実装AI です。

────────────────────────
【外部メモリー（Notion）】
────────────────────────
【コーディング基準】
{memory["coding"]}

【デザイン基準】
{memory["design"]}

【品質基準】
{memory["quality"]}

────────────────────────
【最重要ルール】
- 司令塔AIが承認したチェックリストのみを参照する
- 構造化AIの草案は参照しない
- 保守性・再現性を最優先
- 判断はしない

────────────────────────
【出力形式】
【実装結果】
（コード / 文章 / データ処理結果など）

【補足】
- ファイル構造：
- 注意点：

────────────────────────
司令塔AIの承認済みチェックリストを含む構造案：
{design_output}
"""
    return call_claude(prompt)


# ================================================
#  検証AI（旧：デバッグAI）
# ================================================
def run_debugger(code_output: str):
    """
    検証AI：
    - 実装結果の品質検証
    - 問題点の分類・原因分析・修正案・再発防止策を提示

    問題がある場合：【問題点】【分類】【修正案】【再発防止策】
    問題がない場合：【問題なし】
    """
    memory = load_external_memory()

    prompt = f"""
あなたは制作パイプラインの 検証AI です。

────────────────────────
【外部メモリー（Notion）】
────────────────────────
【判断基準】
{memory["judgement"]}

【デザイン基準】
{memory["design"]}

【コーディング基準】
{memory["coding"]}

【品質基準】
{memory["quality"]}

────────────────────────
【役割】
- 実装結果の品質検証
- 問題点の分類
- 原因分析
- 修正案
- 再発防止策

────────────────────────
【出力形式】
問題がある場合：
【問題点】
- （具体的に列挙）
【分類】
構造 / 実装 / 仕様 / 表現
【修正案】
- （具体的に）
【再発防止策】
- （簡潔に）

問題がない場合：
{NO_BUG_MARKER}
（問題がない理由を簡潔に）

────────────────────────
【検証対象の実装結果】
{code_output}
"""
    return call_claude(prompt)


# ================================================
#  基準進化AI（旧：改善AI）
# ================================================
def run_criteria_evolution(
    user_request: str,
    supervisor: str,
    design: str,
    code: str,
    final_code: str,
    loop_history: list,
    score_json: dict,
    next_tips: str,
):
    """
    基準進化AI：
    - 外部メモリを肥大化させず、重複を排除しながら進化させる
    - スコア履歴を分析し、司令塔AIの弱点を指摘
    """
    return run_memory_improvement(
        user_request=user_request,
        supervisor=supervisor,
        design=design,
        code=code,
        final_code=final_code,
        loop_history=loop_history,
        score_json=score_json,
        next_tips=next_tips,
    )


# ================================================
#  シミュレーション依頼AI（旧：疑似クライアントAI）
# ================================================
def run_simulation_request(theme: str, personality: str = "丁寧で論理的") -> str:
    """
    シミュレーション依頼AI：
    - テーマと性格パターンに基づき、模擬依頼を生成する
    - training_loop から呼び出される
    """
    prompt = f"""
あなたは シミュレーション依頼AI です。

【目的】
テーマと件数に基づき、外部環境としての依頼を生成する。
制作パイプラインのトレーニング用の模擬依頼を作る。

【性格パターン】
{personality}

【依頼の特徴】
- 曖昧さを含んでよい
- 外部環境特有の癖を反映してよい
- トレンドを参考にしてよい

【出力形式】
依頼内容：
〜〜〜

────────────────────────
テーマ：{theme}
"""
    return call_gpt(prompt)


# ================================================
#  シミュレーションFB AI（旧：疑似クライアントAIフィードバック）
# ================================================
def run_simulation_feedback(result: dict) -> str:
    """
    シミュレーションFB AI：
    - 制作物に対して外部環境としてのフィードバックを生成
    """
    prompt = f"""
あなたは シミュレーションFB AI です。

【目的】
制作物に対して、外部環境としてのフィードバックを生成する。

【フィードバック傾向】
丁寧で建設的 / 厳しく細かい / 抽象的で曖昧 / トレンドを持ち出す

【出力形式】
【改善要望】
〜〜〜

────────────────────────
制作物の概要：
{result.get("supervisor", "")}

最終コード（抜粋）：
{str(result.get("code", ""))[:500]}
"""
    return call_gpt(prompt)


# ================================================
#  シミュレーションログAI（旧：クライアントログAI）
# ================================================
def run_simulation_log(request: str, feedback: str, personality: str) -> str:
    """
    シミュレーションログAI：
    - 外部環境AIの行動ログをまとめ、軽量トレーニングログを生成
    """
    prompt = f"""
あなたは シミュレーションログAI です。

【目的】
外部環境AIの行動ログをまとめ、学習に使える軽量トレーニングログを生成する。

【出力形式】
シミュレーションAIトレーニングログ
性格パターン：〜〜〜
依頼の傾向：〜〜〜
フィードバックの傾向：〜〜〜
今回の癖：〜〜〜
次回の学習ポイント：〜〜〜（1〜2行）

────────────────────────
性格パターン：{personality}
依頼内容：{request}
フィードバック：{feedback}
"""
    return call_gpt(prompt)


# ================================================
#  プロジェクト実行（制作 → 改善 → スコア → レポート）
# ================================================
def run_project(
    user_request: str,
    company_name: str,
    client_name: str,
):
    start_time = time.time()

    # --- プロジェクト名生成 ---
    project_name = call_gpt(
        f"以下の依頼内容から短いプロジェクト名を生成：\n{user_request}"
    ).strip()

    # --- タグ分類 ---
    tag = call_gpt(
        f"""
以下の依頼内容を分類し、適切なタグを1つだけ出力してください。

候補：
LP制作 / UI改善 / バグ修正 / 新規開発 / デザイン調整 / コード最適化 / サイト改修 / コンテンツ追加 / その他

依頼内容：
{user_request}
"""
    ).strip()
    tag = tag.replace("タグ", "").replace("：", "").strip()
    tags = [tag]

    # --- AIパイプライン実行 ---
    supervisor = run_supervisor(user_request, company_name, client_name)
    design = run_designer(supervisor)
    code = run_coder(design)

    # --- 改善ループ（最大3回） ---
    loop_history = []
    current_code = code
    debug = ""

    for i in range(3):
        debug = run_debugger(current_code)

        history_item = {
            "loop": i + 1,
            "debug": debug,
            "before_code": current_code,
        }

        if _has_no_bugs(debug):
            loop_history.append(history_item)
            break

        fixed_code = run_coder(debug)
        history_item["after_code"] = fixed_code
        loop_history.append(history_item)
        current_code = fixed_code

    final_code = current_code

    # --- 次回改善ポイント ---
    next_tips = call_gpt(
        f"以下の改善履歴から次回気をつける点をまとめて：\n{loop_history}"
    )

    status = "完了"

    # --- スコア計算 ---
    bug_count = count_bug_points(debug)
    trial_count = len(loop_history)
    total_time = round(time.time() - start_time, 2)
    project_id = int(time.time())

    score_json = {
        "project_id": project_id,
        "total_time": total_time,
        "bug_count": bug_count,
        "trial_count": trial_count,
    }

    # --- Supabaseへスコア送信 ---
    send_score_to_supabase(score_json)

    # --- Notionへスコア保存 ---
    meta = {
        "project_name": project_name,
        "tags": tags,
        "company_name": company_name,
        "client_name": client_name,
    }
    save_score_to_notion_score_db(score_json, meta)

    # --- 基準進化AI（学習） ---
    improved_text = run_criteria_evolution(
        user_request=user_request,
        supervisor=supervisor,
        design=design,
        code=code,
        final_code=final_code,
        loop_history=loop_history,
        score_json=score_json,
        next_tips=next_tips,
    )

    # --- プロジェクトレポート生成 ---
    report = f"""
# プロジェクトレポート

## メタ情報
- プロジェクト名：{project_name}
- タグ：{tags}
- ステータス：{status}
- 企業名：{company_name}
- 担当者名：{client_name}

## 依頼
{user_request}

## 司令塔AI
{supervisor}

## 構造化AI
{design}

## 初回実装
{code}

## 改善履歴
{loop_history}

## 最終実装
{final_code}

## 次回気をつける点
{next_tips}

## 基準進化AIログ
{improved_text}
"""

    save_log_to_notion(
        project_name=project_name,
        tags=tags,
        status=status,
        report=report,
    )

    return {
        "project_name": project_name,
        "tags": tags,
        "status": status,
        "supervisor": supervisor,
        "design": design,
        "code": final_code,
        "debug": debug,
        "loop_history": loop_history,
        "next_tips": next_tips,
        "company_name": company_name,
        "client_name": client_name,
    }


# ================================================
#  簡易ワークフロー（依頼 → 制作）
# ================================================
def run_workflow(user_request: str):
    supervisor = run_supervisor(user_request, "不明", "不明")
    design = run_designer(supervisor)
    code = run_coder(design)
    return {"supervisor": supervisor, "design": design, "code": code}
