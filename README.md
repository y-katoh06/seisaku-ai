# 制作会社AI API

AIが依頼生成 → 制作 → フィードバック → 学習を自動で行うAPIサーバー。

## AIパイプライン構成

| AI | 役割 |
|---|---|
| 司令塔AI | 依頼を構造化し、制作仕様書・チェックリストを生成 |
| 構造化AI | 仕様書をもとに構造案・作業方針を作成 |
| 実装AI | 承認済みチェックリストをもとにコードを生成 |
| 検証AI | 実装結果の品質検証・修正案・再発防止策を提示 |
| 基準進化AI | 外部メモリを進化させ、AIを継続的に改善 |
| シミュレーション依頼AI | 模擬依頼を自動生成（学習用） |
| シミュレーションFB AI | 制作物へのフィードバックを自動生成 |
| シミュレーションログAI | トレーニングログを生成 |

---

## Railway へのデプロイ手順

### 1. GitHubにリポジトリを作成してpush

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git push -u origin main
```

### 2. Railwayでプロジェクトを作成

1. [railway.app](https://railway.app) にアクセスしてログイン
2. 「New Project」→「Deploy from GitHub repo」を選択
3. 先ほど作ったリポジトリを選択

### 3. 環境変数を設定

Railwayのプロジェクト画面で「Variables」タブを開き、
`.env.example` に記載されている変数をすべて入力する。

| 変数名 | 説明 |
|---|---|
| `OPENAI_API_KEY` | OpenAI APIキー |
| `ANTHROPIC_API_KEY` | Anthropic APIキー |
| `NOTION_API_KEY` | Notion インテグレーションキー |
| `NOTION_EXTERNAL_MEMORY_DB` | 外部メモリDBのID |
| `NOTION_PROJECT_REPORT_DB` | プロジェクトレポートDBのID |
| `NOTION_SCORE_DB` | スコアDBのID |
| `SUPABASE_SCORE_URL` | Supabase Edge FunctionのURL |
| `SUPABASE_SERVICE_KEY` | Supabase サービスキー |

### 4. デプロイ確認

Railwayが自動でビルド＆デプロイを開始する。
完了後、発行されたURLにアクセスして確認：

```
GET https://あなたのURL.railway.app/
→ {"message": "制作会社AI API 稼働中"}
```

### 5. GitHubにpushするたびに自動デプロイ

以降は `git push` するだけで Railway が自動でデプロイする。

---

## APIエンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/` | 動作確認 |
| POST | `/project` | 制作依頼（制作→改善→学習） |
| POST | `/train` | 自動学習ループ |
| POST | `/generate` | 簡易ワークフロー（制作のみ） |

### /project の使い方

```bash
curl -X POST "https://あなたのURL.railway.app/project?request=LPを作って&company=株式会社XX&client=田中"
```

### /train の使い方

```bash
curl -X POST "https://あなたのURL.railway.app/train?theme=LP改善&count=3"
```
