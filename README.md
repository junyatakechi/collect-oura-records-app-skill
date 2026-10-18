# oura-collection-app

Oura Ring のデータを取得し、Notionの「OuraRing」配下の5つのDB（日次サマリー・睡眠区間・セッション・ワークアウト・タグ）へ記録する、アプリケーションスキル。

Oura API側の判断（トークンの扱い・境界日の取りこぼし・心拍の取り方・数日遅れの確定など）は [oura-api-generic-logic](https://github.com/junyatakechi/oura-api-generic-logic) に、Notionの呼び方は [notion-cli-generic-logic](https://github.com/junyatakechi/notion-cli-generic-logic) に委ね、どちらの道具も部品として呼ぶ。このスキルが持つのは、記録先のDB・列名・Ouraの項目との対応と手順。まだ切り出していない判断は `references/` に置く。

## 中身

- [SKILL.md](SKILL.md): 判断の委任表・使用するリポジトリ表と、設定の確認・同期・報告の手順
- [conventions/notion-db.md](conventions/notion-db.md): 記録先のDBと列（この環境での記録の取り決め）
- [references/](references/): まだ切り出していない判断。1判断1ファイル
- [scripts/sync_oura_to_notion.py](scripts/sync_oura_to_notion.py): Ouraから取り、Notionへ記録する

## 必要なもの

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) と [uv](https://docs.astral.sh/uv/)
- [oura-api-generic-logic](https://github.com/junyatakechi/oura-api-generic-logic)（Ouraの判断と道具）
- [notion-cli-generic-logic](https://github.com/junyatakechi/notion-cli-generic-logic)（Notionの判断と道具）
- 3つのスキルは、同じ `skills/` フォルダに並べて置く（スクリプトが隣のフォルダから道具を読む）
- 記録先のNotionのDB 5つ（列は [conventions/notion-db.md](conventions/notion-db.md)）

## インストール

```bash
git clone https://github.com/junyatakechi/oura-api-generic-logic.git ~/.claude/skills/oura-api-generic-logic
```

```bash
git clone https://github.com/junyatakechi/notion-cli-generic-logic.git ~/.claude/skills/notion-cli-generic-logic
```

```bash
git clone https://github.com/junyatakechi/oura-collection-app.git ~/.claude/skills/oura-collection-app
```

## セットアップ

1. oura-api-generic-logic の README の「セットアップ」で、Ouraの認証情報を用意する。
2. notion-cli-generic-logic の README の「セットアップ」で、Notionのトークンを用意し、記録先の5つのDBにIntegrationを接続する。
3. `.env.example` のキーを、プロジェクトのフォルダ直下（Claude Code を起動するフォルダ）の `.env` に足し、値を埋める。`.env` はプロジェクトのスキルで共有する。

| キー | 中身 |
|---|---|
| `OURA_COLLECTION_DB_DAILY_URL` | 「Oura 日次サマリー」DBのURL |
| `OURA_COLLECTION_DB_SLEEP_URL` | 「Oura 睡眠区間」DBのURL |
| `OURA_COLLECTION_DB_SESSION_URL` | 「Oura セッション」DBのURL |
| `OURA_COLLECTION_DB_WORKOUT_URL` | 「Oura ワークアウト」DBのURL |
| `OURA_COLLECTION_DB_TAG_URL` | 「Oura タグ」DBのURL |

4. 書き込まずに確かめる。

   ```bash
   cd <プロジェクトのフォルダ>   # .env のあるフォルダ
   uv run ~/.claude/skills/oura-collection-app/scripts/sync_oura_to_notion.py --dry-run
   ```

## 使い方

| 頼み方 | Claudeがすること |
|---|---|
| 「Ouraのデータを同期して」「Oura Ringの記録を更新して」 | 前日分を取り、5つのDBに記録する |
| 「7月1日から今日までのOuraを同期して」 | その期間を取り、記録する |
| 「Ouraの睡眠データを記録して」 | 同上。睡眠区間の件数を中心に報告する |

チャットには、DBごとの作成・更新・スキップの件数と、取れなかったエンドポイントがあればそれを返す。

データは翌朝に確定するので、実行するなら起床後（目安は午前7〜10時以降）がよい。
