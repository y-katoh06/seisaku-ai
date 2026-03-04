# ================================================
#  main.py
# -----------------------------------------------
# 役割：
# - FastAPI による制作会社AIのAPIサーバー
#
# エンドポイント：
# - GET /        → 動作確認
# - POST /project → 通常の制作フロー（制作→改善→学習）
# - POST /train   → 自動学習ループ
# - POST /generate → 簡易ワークフロー（制作のみ）
# ================================================

import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse
from agents import run_project, run_workflow
from training_loop import run_training_cycle

app = FastAPI(
    title="制作会社AI API",
    description="AIが依頼生成 → 制作 → フィードバック → 学習を自動で行うAPI",
    version="2.1.0"
)


# -----------------------------------------------
# 動作確認用エンドポイント
# -----------------------------------------------
@app.get("/")
def root():
    return {"message": "制作会社AI API 稼働中"}


# -----------------------------------------------
# 通常の制作フロー（制作 → 改善 → スコア → 学習）
# -----------------------------------------------
@app.post("/project")
async def project(
    request: str,
    company: str,
    client: str,
    background_tasks: BackgroundTasks,
):
    """
    外部から制作依頼を受け取り、run_project をバックグラウンドで実行する。

    run_project は GPT/Claude を複数回呼び出す重い処理のため、
    BackgroundTasks でオフロードしてタイムアウトを防ぐ。
    処理結果は Notion に自動保存される。
    """

    background_tasks.add_task(
        run_project,
        user_request=request,
        company_name=company,
        client_name=client,
    )

    return {
        "status": "accepted",
        "message": "制作を開始しました。完了後 Notion にレポートが保存されます。"
    }


# -----------------------------------------------
# 自動学習ループ
# -----------------------------------------------
@app.post("/train")
async def train(
    background_tasks: BackgroundTasks,
    theme: str = "LP改善",
    count: int = Query(default=3, ge=1, le=10),  # ← 1〜10 の範囲に制限
):
    """
    テーマに沿った依頼をAIが自動生成し、run_project を複数回実行して学習する。
    count は最大10件まで。
    """

    background_tasks.add_task(run_training_cycle, theme, count)

    return {
        "status": "accepted",
        "theme": theme,
        "count": count,
        "message": f"学習ループを開始しました（{count}件）。"
    }


# -----------------------------------------------
# 簡易ワークフロー（制作のみ・同期OK）
# -----------------------------------------------
@app.post("/generate")
async def generate(request: dict):
    """
    統括AI → 設計AI → コーディングAI の簡易版。
    学習・スコア計算なし。呼び出し回数が少ないため同期処理で問題ない。
    """

    user_request = request.get("request", "")
    if not user_request:
        raise HTTPException(status_code=400, detail="request フィールドが空です。")

    result = await asyncio.to_thread(run_workflow, user_request)
    return result
