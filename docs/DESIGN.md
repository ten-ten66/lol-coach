# LoL Coach — 設計ドキュメント

> 作成日: 2026-05-15
> ステータス: ドラフト v0.1

## 1. プロジェクト概要

### 目的
League of Legends プレイヤー（まず自分自身）を支援する 2 系統のツールを、共通バックエンドの上に段階的に構築する。

### 最終的に作るもの
1. **ドラフト相性 Web ツール** — チーム構成の入力に対し、マッチアップ/シナジー統計から推奨ピックを提示
2. **ライブゲーム支援デスクトップオーバーレイ** — クライアント連携でチャンピオンセレクト中・試合中に情報表示

### スコープ外（明示）
- 公開サービス化・課金（個人利用前提でスタート）
- 「最適手」を断定するレコメンド（規約のグレーゾーン回避のため、統計提示に留める）
- プロ試合予測
- ランクブースト等の不正利用に直結する機能

### 成功条件
- Phase 1: 自分の直近 20 試合の成績を CLI 1 コマンドで確認できる
- Phase 2: 任意の 5v5 構成を入力すると、欠けロールの推奨チャンピオン Top 5 が出る
- Phase 3: クライアント起動 → チャンピオンセレクト画面でオーバーレイに相手 5 人の統計が自動表示される

---

## 2. システムアーキテクチャ

```
┌──────────────────────────────────────────────────────────────────┐
│                  Riot Public APIs (外部)                          │
│  - Riot API (api.riotgames.com)                                   │
│  - Data Dragon (ddragon.leagueoflegends.com)                      │
│  - Community Dragon (補助)                                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │ HTTPS (rate-limited)
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI, Python 3.12)                   │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐│
│  │ API レイヤー    │  │ サービス層      │  │ Riot クライアント    ││
│  │ /summoner/...  │  │ - 集計          │  │ - レート制限管理    ││
│  │ /draft/...     │  │ - 推薦ロジック  │  │ - リトライ           ││
│  │ /champions/... │  │ - キャッシュ     │  │ - キャッシング       ││
│  └────────┬───────┘  └────────┬───────┘  └─────────┬───────────┘│
│           │                   │                     │            │
│           └───────────┬───────┴─────────────────────┘            │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │   バックグラウンドワーカー（ARQ）                           │  │
│  │   - 高ランク試合サンプリング                                │  │
│  │   - マッチ詳細フェッチ → 永続化                             │  │
│  │   - マッチアップ集計の定期再計算                            │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
       ┌───────────────┐                  ┌────────────────┐
       │  PostgreSQL   │                  │     Redis      │
       │  - matches    │                  │ - rate limit   │
       │  - participants│                  │ - キャッシュ    │
       │  - aggregates │                  │ - ジョブキュー  │
       └───────────────┘                  └────────────────┘

         ┌──────────────────────┐   ┌────────────────────────┐
         │   Web フロント        │   │  デスクトップオーバーレイ │
         │   (Phase 2)          │   │  (Phase 3)             │
         │   Next.js + Tailwind │   │  Electron + React      │
         │   - ドラフト入力 UI  │   │  - LCU 連携             │
         │   - 個人成績         │   │  - 透明ウィンドウ       │
         └──────────┬───────────┘   └──────────┬─────────────┘
                    │                          │
                    └──────────┬───────────────┘
                               │ REST / WebSocket
                               ▼
                       backend に接続
```

### コンポーネント分担
| レイヤー | 役割 | 技術 |
|---------|------|------|
| API | クライアントからのリクエスト処理 | FastAPI |
| サービス層 | ビジネスロジック・集計・キャッシュ戦略 | Python |
| Riot クライアント | 外部 API への通信、レート制限、リトライ | httpx + 自作 wrapper |
| ワーカー | バックグラウンド収集・集計 | ARQ (Redis ベース) |
| 永続化 | 試合データ・集計結果 | PostgreSQL 16 |
| キャッシュ | レスポンス・レート制限 | Redis 7 |

---

## 3. 技術スタック

### バックエンド
- **Python 3.12**
- **uv** — パッケージ/プロジェクト管理（pip より高速、lockfile 管理）
- **FastAPI** — Web フレームワーク
- **SQLAlchemy 2.x (async)** — ORM
- **Alembic** — マイグレーション
- **Pydantic v2** — バリデーション/設定
- **httpx** — HTTP クライアント（async）
- **ARQ** — バックグラウンドジョブ
- **structlog** — 構造化ログ

### データストア
- **PostgreSQL 16** — メインDB
- **Redis 7** — キャッシュ + ジョブキュー + レート制限カウンタ

### 静的データ
- **Data Dragon** — チャンピオン・アイテム・スペル定義（パッチごとに取得）

### Phase 2 フロント
- **Next.js 15** (App Router) + **TypeScript**
- **Tailwind CSS** + **shadcn/ui**
- **TanStack Query** — サーバーステート

### Phase 3 デスクトップ
- **Electron** + **React** （フロントと共通化可）
- 代替案: **Tauri**（バイナリが軽い、Rust 経験ありなら）

### 開発ツール
- **Docker Compose** — Postgres/Redis をローカルで一発起動
- **pytest** + **pytest-asyncio** — テスト
- **ruff** — Linter/Formatter
- **mypy** — 型チェック
- **just** — タスクランナー（Makefile より読みやすい）

### 候補から外した理由
- **Cassiopeia / Pulsefire** (既存 Riot ラッパー): 学習目的なので自前で薄く書く。レート制限/リトライの理解を深めるため。
- **Celery**: ARQ で十分。Celery は重い。
- **Tauri (確定)**: Electron の方が情報量多くハマりにくい。サイズは妥協。

---

## 4. プロジェクト構成

```
/opt/lol-coach/
├── README.md
├── docker-compose.yml
├── .env.example
├── justfile
├── docs/
│   ├── DESIGN.md              # 本書
│   ├── riot-api-notes.md      # API 仕様メモ
│   ├── lcu-notes.md           # LCU 仕様メモ (Phase 3)
│   └── decisions/             # ADR (Architecture Decision Records)
│
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── src/
│   │   └── lol_coach/
│   │       ├── __init__.py
│   │       ├── main.py             # FastAPI entrypoint
│   │       ├── config.py           # Pydantic Settings
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── deps.py         # DI
│   │       │   ├── summoner.py
│   │       │   ├── matches.py
│   │       │   ├── draft.py
│   │       │   └── champions.py
│   │       ├── riot/
│   │       │   ├── __init__.py
│   │       │   ├── client.py       # httpx async wrapper
│   │       │   ├── rate_limiter.py # Redis-backed leaky bucket
│   │       │   ├── endpoints.py    # 各エンドポイントラッパー
│   │       │   └── ddragon.py      # 静的データ取得
│   │       ├── models/             # SQLAlchemy
│   │       │   ├── __init__.py
│   │       │   ├── match.py
│   │       │   ├── participant.py
│   │       │   ├── summoner.py
│   │       │   └── aggregates.py
│   │       ├── schemas/            # Pydantic
│   │       │   ├── match.py
│   │       │   ├── draft.py
│   │       │   └── champion.py
│   │       ├── services/
│   │       │   ├── ingest.py       # データ収集
│   │       │   ├── aggregation.py  # 集計
│   │       │   ├── recommendation.py # ドラフト推薦
│   │       │   └── summoner.py     # 個人成績
│   │       ├── workers/
│   │       │   ├── __init__.py
│   │       │   ├── sampler.py      # 高ランクサンプリング
│   │       │   └── aggregator.py   # 定期集計
│   │       └── db/
│   │           ├── session.py
│   │           └── base.py
│   └── tests/
│       ├── conftest.py
│       ├── test_riot_client.py
│       ├── test_aggregation.py
│       └── test_recommendation.py
│
├── frontend/                    # Phase 2 で追加
│   └── (Next.js プロジェクト)
│
└── overlay/                     # Phase 3 で追加
    └── (Electron プロジェクト)
```

---

## 5. データモデル

### 命名規則
- テーブル名: snake_case 複数形
- カラム: snake_case
- PK は基本的に `id BIGSERIAL` 、ただし Riot 由来の自然キーがある場合はそれを採用

### スキーマ

#### `patches`
ゲームパッチ管理。集計は必ずパッチを跨がない。
```sql
CREATE TABLE patches (
  version VARCHAR(16) PRIMARY KEY,    -- "14.10"
  major INT NOT NULL,
  minor INT NOT NULL,
  released_at DATE,
  is_current BOOLEAN NOT NULL DEFAULT FALSE
);
```

#### `champions`
Data Dragon から同期。
```sql
CREATE TABLE champions (
  id INT PRIMARY KEY,                  -- Riot Champion ID
  key VARCHAR(64) NOT NULL UNIQUE,     -- "Aatrox"
  name VARCHAR(64) NOT NULL,
  title VARCHAR(128),
  tags VARCHAR(128),                   -- "Fighter,Tank" カンマ区切り
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `summoners`
取得した召喚士の最小情報。
```sql
CREATE TABLE summoners (
  puuid VARCHAR(78) PRIMARY KEY,
  region VARCHAR(8) NOT NULL,          -- "kr", "jp1", etc.
  game_name VARCHAR(64),               -- Riot ID
  tag_line VARCHAR(16),
  current_tier VARCHAR(16),            -- "CHALLENGER" etc.
  current_rank VARCHAR(8),
  last_synced_at TIMESTAMPTZ
);
CREATE INDEX idx_summoners_region_tier ON summoners(region, current_tier);
```

#### `matches`
試合のメタ情報。
```sql
CREATE TABLE matches (
  match_id VARCHAR(32) PRIMARY KEY,    -- "KR_1234567890"
  region VARCHAR(8) NOT NULL,
  queue_id INT NOT NULL,               -- 420=ranked solo
  patch VARCHAR(16) NOT NULL REFERENCES patches(version),
  game_start_at TIMESTAMPTZ NOT NULL,
  game_duration_sec INT NOT NULL,
  winning_team SMALLINT,               -- 100 or 200
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_matches_patch_queue ON matches(patch, queue_id);
CREATE INDEX idx_matches_game_start ON matches(game_start_at DESC);
```

#### `participants`
試合参加者。マッチアップ集計の元データ。
```sql
CREATE TABLE participants (
  match_id VARCHAR(32) NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
  puuid VARCHAR(78) NOT NULL,
  team_id SMALLINT NOT NULL,           -- 100/200
  champion_id INT NOT NULL REFERENCES champions(id),
  team_position VARCHAR(8),            -- "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"
  win BOOLEAN NOT NULL,
  kills SMALLINT NOT NULL,
  deaths SMALLINT NOT NULL,
  assists SMALLINT NOT NULL,
  cs INT NOT NULL,
  gold_earned INT NOT NULL,
  PRIMARY KEY (match_id, puuid)
);
CREATE INDEX idx_participants_puuid ON participants(puuid);
CREATE INDEX idx_participants_champion ON participants(champion_id);
```

#### `champion_matchups_agg`
対面マッチアップの集計（事前計算）。
```sql
CREATE TABLE champion_matchups_agg (
  champion_a INT NOT NULL REFERENCES champions(id),
  champion_b INT NOT NULL REFERENCES champions(id),
  role VARCHAR(8) NOT NULL,
  patch VARCHAR(16) NOT NULL REFERENCES patches(version),
  tier_band VARCHAR(16) NOT NULL,      -- "MASTER_PLUS", "DIAMOND", "ALL"
  games INT NOT NULL,
  wins INT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (champion_a, champion_b, role, patch, tier_band),
  CHECK (champion_a < champion_b)      -- 重複防止: 対称関係は片側のみ保持
);
```

#### `champion_synergy_agg`
同チームでのシナジー集計。
```sql
CREATE TABLE champion_synergy_agg (
  champion_a INT NOT NULL REFERENCES champions(id),
  champion_b INT NOT NULL REFERENCES champions(id),
  patch VARCHAR(16) NOT NULL REFERENCES patches(version),
  tier_band VARCHAR(16) NOT NULL,
  games INT NOT NULL,
  wins INT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (champion_a, champion_b, patch, tier_band),
  CHECK (champion_a < champion_b)
);
```

#### `ingestion_jobs`
収集ジョブの状態管理。
```sql
CREATE TABLE ingestion_jobs (
  id BIGSERIAL PRIMARY KEY,
  job_type VARCHAR(32) NOT NULL,       -- "sample_high_rank", "fetch_match"
  payload JSONB NOT NULL,
  status VARCHAR(16) NOT NULL,         -- "pending", "running", "done", "failed"
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ
);
```

### 集計戦略
- `participants` は raw データとして残す（再集計可能）
- 集計テーブルはパッチ x ティアバンド x ロール の組み合わせで持つ
- 1 パッチごとに数百万試合になるので、定期的に古いパッチを別テーブルへ移行（コールドストレージ）

---

## 6. API 設計

ベース URL: `http://localhost:8000/api/v1`

### Phase 1 で実装
| Method | Path | 説明 |
|--------|------|------|
| GET | `/summoner/{region}/{game_name}/{tag_line}/profile` | 召喚士プロファイル |
| GET | `/summoner/{region}/{game_name}/{tag_line}/recent?limit=20` | 直近試合の概要 |
| GET | `/summoner/{region}/{game_name}/{tag_line}/champions` | チャンピオン別成績 |
| GET | `/matches/{match_id}` | 試合詳細 |
| GET | `/champions` | チャンピオン一覧 |
| GET | `/health` | ヘルスチェック |

### Phase 2 で追加
| Method | Path | 説明 |
|--------|------|------|
| GET | `/champions/{id}/matchups?role=TOP&patch=14.10` | 対面相性表 |
| GET | `/champions/{id}/synergies?patch=14.10` | シナジー表 |
| POST | `/draft/recommend` | ドラフト推薦 |

### Phase 3 で追加
| Method | Path | 説明 |
|--------|------|------|
| POST | `/live/champ-select/analyze` | チャンピオンセレクト状態の分析 |
| WS | `/live/ws` | デスクトップ向けライブ更新 |

### スキーマ例: `/draft/recommend`
```json
// Request
{
  "patch": "14.10",
  "tier_band": "MASTER_PLUS",
  "ally_champions": [{"id": 266, "role": "TOP"}, {"id": 64, "role": "JUNGLE"}],
  "enemy_champions": [{"id": 86, "role": "TOP"}],
  "missing_role": "MIDDLE",
  "top_n": 5
}

// Response
{
  "recommendations": [
    {
      "champion": {"id": 103, "key": "Ahri", "name": "Ahri"},
      "score": 0.612,
      "win_rate": 0.534,
      "sample_size": 12480,
      "breakdown": {
        "vs_enemies": {"win_rate": 0.55, "samples": 3200},
        "synergy_with_allies": {"win_rate": 0.51, "samples": 8900}
      }
    }
  ],
  "meta": {"patch": "14.10", "tier_band": "MASTER_PLUS", "generated_at": "2026-05-15T..."}
}
```

### 推薦スコアの算出
シンプル版（Phase 2 開始時）:
```
score(c) = α * win_rate_vs_enemies(c)
        + β * win_rate_synergy_with_allies(c)
        + γ * overall_win_rate(c)
       - λ * low_sample_penalty(c)
```
- α=0.4, β=0.4, γ=0.2 を初期値、勝率正規化済み
- サンプル数 < 100 のものは除外、< 500 はペナルティ

---

## 7. Riot API 統合戦略

### キー
- 開発キー: 24 時間ごとに失効、20 req/s, 100 req/2min
- パーソナル キー: 申請で取得、レート制限緩和
- プロダクション キー: 公開アプリ向け、申請

**当面は開発キー想定。自動更新せず、起動時に `.env` から読む。**

### エンドポイント分類

| ライン | 用途 | リージョン |
|--------|------|----------|
| `account-v1` | Riot ID → puuid | regional ルート (`asia`, `americas`, `europe`) |
| `summoner-v4` | puuid → summoner | platform (`kr`, `jp1`, etc.) |
| `league-v4` | ランク情報、Challenger/GM 一覧 | platform |
| `match-v5` | 試合 ID/詳細 | regional |
| `spectator-v5` | 現在進行中の試合 | platform |

### レート制限実装
```python
# Redis ベースの leaky bucket
# - app rate limit (20/1s, 100/120s) を全プロセスで共有
# - method rate limit は per-method の Redis key
# - 429 を受けたら Retry-After ヘッダで sleep
```

### キャッシュ
| データ種別 | TTL | 理由 |
|-----------|-----|------|
| マッチ詳細 | 永続 (DB) | 試合結果は不変 |
| サモナー情報 | 1 時間 | ランクが上下する |
| Challenger/GM リスト | 6 時間 | 入れ替わる |
| Data Dragon | パッチ単位 | パッチごとに更新 |

### サンプリング戦略 (Phase 1 後半〜)
1. 各リージョンの Challenger/GM/Master プレイヤー一覧を 6 時間ごとに取得
2. ランダムサンプリングしたプレイヤーの直近 N 試合 ID を取得
3. 未取得の試合 ID をキューに入れ、ワーカーが詳細フェッチ
4. レート制限を 50% 以下に抑え、API キー上限の半分を残す（個人用クエリ用に余裕を持たせる）

---

## 8. LCU / Live Client API 統合 (Phase 3)

### LCU (League Client API)
クライアント起動中に localhost で立つ非公式 API。

**接続情報の取得**
- ロックファイル位置:
  - Windows: `C:\Riot Games\League of Legends\lockfile`
  - macOS: `/Applications/League of Legends.app/Contents/LoL/lockfile`
- フォーマット: `LeagueClient:PID:PORT:PASSWORD:PROTOCOL`
- 認証: HTTP Basic, ユーザー名 `riot`, パスワードはロックファイル
- TLS: 自己署名証明書 → 検証無効化

**監視する主要エンドポイント**
| Path | 用途 |
|------|------|
| `/lol-summoner/v1/current-summoner` | 自分の puuid |
| `/lol-gameflow/v1/gameflow-phase` | ChampSelect / InProgress 等の状態 |
| `/lol-champ-select/v1/session` | ピックバン進行状態 |

**WebSocket イベント**
- 同ポートに `wss://` で接続、`[5, "OnJsonApiEvent"]` を購読
- ピックバン状態変化を push で受け取れる

### Live Client Data API
試合中のみ稼働、`https://127.0.0.1:2999/liveclientdata/...`

| Path | 用途 |
|------|------|
| `/allgameddata` | 全データ一括 |
| `/activeplayer` | 自分の状態（gold, level） |
| `/playerlist` | 全プレイヤーアイテム/スコア |
| `/eventdata` | キル/ドラゴン等のイベント |

### 規約上の制約
- **能動的な妨害は禁止**: 相手プレイヤーへのアクション自動化はBAN対象
- **クールダウン表示は灰色**: 公式のアンチチート対象になりやすい
- **ピックバン推薦は問題なし**: 統計提示の範疇

### オーバーレイ実装
- Electron で frame-less, always-on-top, transparent ウィンドウ
- LCU の WebSocket を Python ブリッジで購読 → backend で分析 → Electron に push
- ゲーム中は手前に出ないよう、クライアント画面のみに表示する

---

## 9. 段階的開発計画

### Phase 0: 環境構築 (1〜2 日)
- [ ] Riot Developer Portal で API キー取得
- [ ] uv で backend プロジェクト初期化
- [ ] docker-compose.yml で Postgres/Redis を起動
- [ ] FastAPI hello-world エンドポイント
- [ ] `.env` 管理、設定ロード

**完了条件**: `just dev` で API が立ち上がり `/health` が 200 を返す

### Phase 1: コア API + 個人成績 (1〜2 週間)
- [ ] Riot API クライアント実装 (httpx + リトライ)
- [ ] Redis レート制限ミドルウェア
- [ ] Data Dragon 同期スクリプト
- [ ] SQLAlchemy モデル + Alembic マイグレーション
- [ ] `/summoner/.../profile`, `/recent`, `/champions` エンドポイント
- [ ] CLI ツール `lol-coach stats <name>` (Click で薄く)
- [ ] テスト: Riot API モック、集計ロジック

**完了条件**: `lol-coach stats Hide on bush#KR1` で直近 20 試合と Champ 別勝率が出る

### Phase 2: ドラフト Web ツール (2〜3 週間)
- [ ] 高ランクサンプリングワーカー実装
- [ ] マッチ詳細ワーカー + 集計テーブル更新
- [ ] `/draft/recommend` 実装、スコアロジック
- [ ] Next.js フロント雛形
- [ ] ドラフト入力 UI (チャンピオン検索、5v5 グリッド)
- [ ] 推薦結果表示
- [ ] パッチ/ティアフィルター

**完了条件**: ブラウザで 5v5 入力 → 自陣残りロールの Top 5 推奨が 1 秒以内に出る

### Phase 3: ライブオーバーレイ (3〜4 週間)
- [ ] LCU クライアント (Python)
- [ ] ロックファイル監視 + WebSocket 接続
- [ ] チャンピオンセレクト状態 → backend 連携
- [ ] Electron 雛形 (transparent / always-on-top)
- [ ] フロント (Next.js コンポーネント再利用)
- [ ] バックエンドからの push 受信表示
- [ ] In-Game オーバーレイ（任意、Live Client Data 連携）

**完了条件**: クライアント起動 → チャンピオンセレクトに入ると、自動でオーバーレイに 10 人分の統計が出る

### Phase 4 以降のアイデア (やるなら)
- 召喚士の試合履歴を時系列で可視化（成長グラフ）
- パッチ間のメタ変動を可視化
- 友達と一緒にプレイした試合のパフォーマンス比較
- 試合タイムラインの分析（ゴールド差グラフ、オブジェクト取得タイミング）

---

## 10. リスク・注意事項

### 規約系
| リスク | 対策 |
|-------|------|
| Riot API ToS 違反 | 静的データは Data Dragon 経由のみ。試合データの大量再配布をしない |
| Production Key 未取得で公開 | 個人利用に留める。公開時は申請 |
| LCU 自動操作で BAN | 読み取り専用に徹する。ボタンを押すような行為は実装しない |
| オーバーレイがアンチチート対象になる | 公式のオーバーレイガイドライン準拠 (フレームレス + 統計のみ) |

### 技術系
| リスク | 対策 |
|-------|------|
| 開発キーが24時間で失効 | `.env` 更新を簡単にする。長時間ワーカーは Production 申請後に |
| レート制限超過 | Redis ベースの集中管理。アプリ全体で 20req/s を超えない |
| Riot API スキーマ変更 | エンドポイントごとに薄いラッパー。Pydantic で型を強制 |
| LCU API のバージョン差異 | 開発時のクライアントバージョンを記録、変更に追随 |
| ディスク逼迫（試合データ） | パッチ単位でアーカイブ、3 パッチ古いものは別ストレージ |

### プロセス系
| リスク | 対策 |
|-------|------|
| Phase 1 で挫折 | スコープを「自分の試合だけ」に絞る。集計は後 |
| Phase 2 でデータ不足 | 友達のアカウントもサンプル元に追加。少数派バンドは "ALL" にフォールバック |
| Phase 3 で UI 沼 | まず CLI で結果を出す → Electron は最後に被せる |

---

## 11. 開発環境構築手順 (Phase 0)

```bash
# 前提: Python 3.12, Docker, uv, just インストール済み

cd /opt/lol-coach

# backend セットアップ
mkdir backend && cd backend
uv init --package lol-coach
uv add fastapi[standard] httpx sqlalchemy[asyncio] asyncpg \
       alembic pydantic-settings structlog arq redis click
uv add --dev pytest pytest-asyncio ruff mypy

# Postgres/Redis 起動
cd .. && cat > docker-compose.yml <<'YAML'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: lol
      POSTGRES_PASSWORD: lol
      POSTGRES_DB: lol_coach
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
volumes:
  pgdata:
YAML

docker compose up -d

# .env 作成
cat > .env <<'ENV'
RIOT_API_KEY=RGAPI-xxxxxxxxxxxxxx
DATABASE_URL=postgresql+asyncpg://lol:lol@localhost:5432/lol_coach
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
DEFAULT_REGION=jp1
ENV
```

---

## 12. 参考資料

### Riot 公式
- [Developer Portal](https://developer.riotgames.com/)
- [API Reference](https://developer.riotgames.com/apis)
- [Data Dragon](https://developer.riotgames.com/docs/lol)

### コミュニティ
- [LCU Documentation (非公式)](https://lcu.vivide.re/)
- [Riot API Libraries](https://riot-api-libraries.readthedocs.io/)
- [r/LeagueAPI](https://www.reddit.com/r/LeagueOfLegendsMeta/)

### 既存ツール（参考にする / しない）
- OP.GG, U.GG — マッチアップ統計表示の UX 参考
- Mobalytics — ドラフトツールの先行例
- Blitz.gg — オーバーレイの先行例（規約遵守の参考）

---

## 13. 未確定事項（Open Questions）

決めずに進めて、後で確定すべきもの:

1. **対象リージョン**: 最初は `jp1` 単独？ それとも `kr` も含める？
   → 自分の試合を見るなら自分のサーバー。データ量なら KR
2. **対象キュー**: ランクソロ (420) のみ？ フレックスやノーマルは？
   → 最初は 420 のみ。データの質が安定するため
3. **対象ティア帯**: Master+ のみ？
   → 最初は Master+ (`MASTER_PLUS`)。サンプル数と質のバランス
4. **フロントの認証**: Phase 2 で自分専用ならなし、誰かに見せるなら？
   → 当面なし。公開するなら別途
5. **オーバーレイの透明度・配置**: ユーザー設定にする？
   → Phase 3 設計時に決定
