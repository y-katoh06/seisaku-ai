# ================================================
#  training_loop.py
# -----------------------------------------------
# 役割：
# - 自動学習ループを実行するモジュール
# - シミュレーション依頼AI が模擬依頼を生成し
#   run_project() を複数回まわして学習データを蓄積する
# - シミュレーションFB AI・ログAI による追加学習にも対応
# ================================================

import random
from agents import (
    run_project,
    run_simulation_request,
    run_simulation_feedback,
    run_simulation_log,
)

# シミュレーション依頼AIの性格パターン
PERSONALITY_PATTERNS = [
    "丁寧で論理的",
    "抽象的でふわっとした依頼",
    "厳しく要求が多い",
    "トレンドに敏感",
    "無茶ぶりをする",
]


def run_training_cycle(theme: str, count: int = 3):
    """
    テーマに沿った模擬依頼を自動生成し、run_project を複数回実行する。

    引数：
    - theme: 依頼生成のテーマ
    - count: 何件の依頼を生成して学習するか（最大10件）

    戻り値：
    - 各 run_project の結果 + FB + ログをまとめたリスト

    ※ 企業名・担当者名に "training_" プレフィックスを付与し
       本番データと区別できるようにする。
    """
    count = min(count, 10)
    results = []

    for i in range(count):
        # 性格パターンをランダムに選択
        personality = random.choice(PERSONALITY_PATTERNS)

        # シミュレーション依頼AI が模擬依頼を生成
        request = run_simulation_request(theme=theme, personality=personality)

        # run_project を実行（制作 → 改善 → スコア → 基準進化AI）
        result = run_project(
            user_request=request,
            company_name=f"training_企業{i + 1}",
            client_name=f"training_担当者{i + 1}",
        )

        # シミュレーションFB AI がフィードバックを生成
        feedback = run_simulation_feedback(result)

        # シミュレーションログAI がトレーニングログを生成
        log = run_simulation_log(
            request=request,
            feedback=feedback,
            personality=personality,
        )

        results.append({
            "index": i + 1,
            "personality": personality,
            "request": request,
            "result": result,
            "feedback": feedback,
            "training_log": log,
        })

    return results
