# oura-collection-app-skill

Oura Ring のデータを取得し、Notionの「OuraRing」配下の5つのDB（日次サマリー・睡眠区間・セッション・ワークアウト・タグ）へ記録するアプリケーションスキル。

## 必要なもの

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) と [uv](https://docs.astral.sh/uv/)
- Oura Ring のアカウント
- Notion のワークスペースと、記録先のDB 5つ（列は [conventions/notion-db.md](conventions/notion-db.md)）
- `SKILL.md` の frontmatter の `metadata.dependencies` に書いてある依存するスキル

## インストール

```bash
git clone https://github.com/junyatakechi/oura-collection-app-skill.git ~/.claude/skills/oura-collection-app-skill
```

特定のプロジェクトだけで使うなら、`<プロジェクト>/.claude/skills/` の中でクローンする。

## セットアップ

1. 依存するスキルを、このスキルと同じ `skills/` フォルダに並べて置く。スクリプトが隣のフォルダから道具を読む。
2. 依存するスキルの README の「セットアップ」を、先に済ませる。
3. 記録先の5つのDBに、Notion の Integration を接続する。
4. `.env.example` のキーを、プロジェクトのフォルダ直下（Claude Code を起動するフォルダ）の `.env` に足し、値を埋める。キーの中身は `.env.example` のコメントにある。`.env` はプロジェクトのスキルで共有する。
5. 書き込まずに確かめる。

   ```bash
   cd <プロジェクトのフォルダ>   # .env のあるフォルダ
   uv run ~/.claude/skills/oura-collection-app-skill/scripts/sync_oura_to_notion.py --dry-run
   ```

## 使い方

スキル名だけを指定して呼ぶ。指名しないと、このスキルは読み込まれない。

```
/oura-collection-app-skill
```
