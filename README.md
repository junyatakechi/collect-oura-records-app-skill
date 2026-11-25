# collect-oura-records-app-skill

Oura Ring のデータを取得し、Notionの「OuraRing」配下の4つのDB（日次サマリー・睡眠区間・ワークアウト・タグ）へ記録するアプリケーションスキル。

## 必要なもの

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) か [Codex](https://developers.openai.com/codex)
- [uv](https://docs.astral.sh/uv/)
- Oura Ring のアカウント
- Notion のワークスペースと、記録先のDB 4つ（列は [conventions/notion-db.md](conventions/notion-db.md)）
- `SKILL.md` の frontmatter の `metadata.dependencies` に書いてある依存するスキル

## インストール

Claude Code では、次のようにクローンする。

```bash
git clone https://github.com/junyatakechi/collect-oura-records-app-skill.git ~/.claude/skills/collect-oura-records-app-skill
```

Codex では、`~/.claude/skills/` を `~/.agents/skills/` に替えてクローンする。

特定のプロジェクトだけで使うなら、`<プロジェクト>/.claude/skills/`（Codex は `<プロジェクト>/.agents/skills/`）の中でクローンする。

## セットアップ

1. 依存するスキルを、このスキルと同じ `skills/` フォルダに並べて置く。スクリプトが隣のフォルダから道具を読む。
2. 依存するスキルの README の「セットアップ」を、先に済ませる。
3. 記録先の4つのDBに、Notion の Integration を接続する。
4. `.env.example` のキーを、プロジェクトのフォルダ直下（AIエージェントを起動するフォルダ）の `.env` に足し、値を埋める。キーの中身は `.env.example` のコメントにある。`.env` はプロジェクトのスキルで共有する。
5. 書き込まずに確かめる。Codex では、`~/.claude/skills/` を `~/.agents/skills/` に替える。

   ```bash
   cd <プロジェクトのフォルダ>   # .env のあるフォルダ
   uv run ~/.claude/skills/collect-oura-records-app-skill/scripts/sync_oura_to_notion.py --dry-run
   ```

## 使い方

スキル名だけを指定して呼ぶ。指名しないと、このスキルは読み込まれない。Codex では、例の `/` を `$` に替えて指名する。

```
/collect-oura-records-app-skill
```
