---
name: oura-collection-app
description: Oura Ring のデータ（睡眠・活動・準備度・回復力・心血管年齢・SpO2・ストレス・VO2Max・心拍・睡眠区間・セッション・ワークアウト・タグ）を取得し、Notionの「OuraRing」配下の5つのDBへ記録するアプリケーションスキル。「Ouraのデータを同期して」「Ouraの睡眠データを記録して」「Oura Ringの記録を更新して」のように言われたときや、評価のスキル（diet-process-evaluation-app など）から評価の前の最新化として呼ばれたときに使う。Oura API側の判断（トークン・境界日・心拍・生データの要約・データの確定の遅れ・レコードの同一性・タグの2形式）は外部の generic-logic（oura-api-generic-logic）に、Notionの呼び方は notion-cli-generic-logic に委ね、どちらの道具も写さず自分で呼ぶ。このスキルが持つのは、聞きたい事・判断先・欲しい答えの形と、記録先のDB・列名・Ouraの項目との対応・手順だけ。取得したデータの解釈・評価はしない。
metadata:
  version: "0.1.0"
  repository: "https://github.com/junyatakechi/oura-collection-app"
  dependencies: "github:junyatakechi/oura-api-generic-logic/oura-api-generic-logic@^0.1.0, github:junyatakechi/notion-cli-generic-logic/notion-cli-generic-logic@^0.1.0"
---

# Ouraのデータの記録

## このスキルが守る一番のこと

**切り出した判断は、このスキルに書かない。下の判断の委任表の判断先の、外部のロジックスキルに委ねる。**
ここにあるのは、OuraのデータをNotionに記録するために、どの判断を外部に委ね、何を実行するかだけ。
Ouraの癖（使い捨てのトークン・境界日の取りこぼし・心拍の範囲指定・数日遅れの確定・タグの2形式）は、どれも oura-api-generic-logic の判断と道具が持つ。ここで写したり、言い換えて書き直したりしない。

もう1つは、**ロジックスキルに無い判断を一般論で埋めない**こと。
判断が無いときは「判断が無い」と書き、本人に聞く。とくに、レスポンスを見て「この項目はたぶん○○」と推測で列を足さない。

## 判断の委任表

記録で必要になる判断について、何を（聞きたい事）、どの判断先に、どんな答えの形で聞くか。

- **聞きたい事はこのスキルが持つ。** 判断ファイルは問いを持たない。聞きたい事に判断ファイルで答えられないときは、ロジックスキルが「判断が無い」と返す。
- **答えの形はこのスキルが決める。材料はロジックスキルが求める。** 何を渡すかは、聞いたときにロジックスキルが返す「求める材料」に従う。
- **聞くときは、聞きたい事・判断先・欲しい答えの形の3つを伝える。** 版は伝えず、実行結果に残すために使う。
- 版は、判断先のロジックスキルの `metadata.version`。判断先の判断ファイルが変わったら、手順とスクリプトを合わせてから版を更新する。

### 中核の判断（core-logic）

無し。記録には、人によって答えが分かれる判断が無い。データの読み方（HRVの落ち込みをどう見るか、など）は、記録を読む側の評価のスキルが core-logic に聞く。

### 一般的な判断（generic-logic）

| 聞きたい事 | 判断先 | 版 | 欲しい答えの形 |
|---|---|---|---|
| Ouraのトークンを、どう取り、どう更新すれば壊さずに済むか | `oura-api-generic-logic/references/auth.md` | 0.1.0 | トークンの取り方と、守ること（道具の使い方） |
| Ouraの道具を、どの入口から呼ぶか | `oura-api-generic-logic/references/client-usage.md` | 0.1.0 | 呼ぶ関数の順と、呼び出し側で書かないこと（道具の使い方） |
| 期間をどう指定し、対象日のレコードをどう拾うか | `oura-api-generic-logic/references/date-boundary.md` | 0.1.0 | 取得範囲の出し方と、対象日のレコードを返す関数（道具の使い方） |
| 心拍を、どう取り、日ごとにどう集計するか | `oura-api-generic-logic/references/heartrate.md` | 0.1.0 | 取り方と、集計の関数（道具の使い方） |
| 生データを、どう残すか | `oura-api-generic-logic/references/raw-data.md` | 0.1.0 | 残す形と、要約の有無（道具の使い方） |
| 何日の分を、いつ取り、記録済みの日次をどうするか | `oura-api-generic-logic/references/data-latency.md` | 0.1.0 | 既定の対象日、日次を上書きするか、空の項目の読み方 |
| 何で重複を判定し、既にあったらどうするか | `oura-api-generic-logic/references/record-identity.md` | 0.1.0 | エンドポイントごとの一意キーと、既にあったときの扱い |
| タグの2つの形式を、どう記録するか | `oura-api-generic-logic/references/tags.md` | 0.1.0 | 形をそろえる関数と、終了時刻の扱い（道具の使い方） |
| Notionを読み書きするとき、道具をどう呼ぶか | `notion-cli-generic-logic/references/client-usage.md` | 0.1.2 | どの入口から呼ぶかと、呼び出し側で書かないこと（道具の使い方） |
| 記録先のDBの列を足す・変えるとき、どう進めるか | `notion-cli-generic-logic/references/schema-change.md` | 0.1.2 | 進め方と、守ること（道具の使い方） |

- 同期のたびに聞くのは無い。どの判断も `scripts/sync_oura_to_notion.py` を書いたときに聞き、返ってきた道具の使い方どおりに呼んでいる。スクリプトを直すとき・判断先の版が上がったときに聞き直す。
- 列の判断は、列を足す・変えるときだけ聞く。同期が401・400・404で失敗したときは、認証とトークン・APIの呼び方・心拍の判断に聞く。
- 返ってきた道具の使い方に従い、どちらのロジックスキルの道具も写さず、自分で呼ぶ。
- 一般的な判断は差し替えるより、新しく踏んだ落とし穴を判断先のスキルに足して育てる。

## 手順

1. 設定を確かめる
2. 同期する
3. 報告する

### 1. 設定を確かめる

次の3つが要る。どれかが無いと、スクリプトがエラーで止まる。止まったら先へ進まず、README の「セットアップ」を案内する。

| 合図 | 足りないもの |
|---|---|
| `~/.claude-skills-env/oura-collection-app.env に OURA_COLLECTION_DB_..._URL が無い` | 記録先のDBのURL |
| `client_id/client_secret is missing`・`refresh_token is missing`・`Oura token endpoint error` | Ouraの認証情報（oura-api-generic-logic の認証とトークンの判断に聞く） |
| `Notion token file not found`・`NOTION_TOKEN is not set`・記録先のDBで404 | Notionのトークン、または記録先のDBへのIntegrationの接続 |

### 2. 同期する

```bash
cd <skill-dir>
uv run scripts/sync_oura_to_notion.py                      # 前日分を同期
uv run scripts/sync_oura_to_notion.py --date 2026-05-16     # 指定日のみ
uv run scripts/sync_oura_to_notion.py --start-date 2026-05-01 --end-date 2026-05-16
uv run scripts/sync_oura_to_notion.py --dry-run             # 書き込まず件数だけ
```

- **何日の分を取るか。** 指定が無ければ前日分。ユーザーや評価のスキルが期間を言ったら、その期間を渡す。今日の行（昨夜の睡眠）が要るときは `--date` で今日を明示する。根拠は oura-api-generic-logic のデータが確定する時期の判断。
- 日次サマリーは既にあっても上書きし、区間（睡眠区間・セッション・ワークアウト・タグ）は記録済みの record id を飛ばす。何度実行しても重複しない。
- 1つのエンドポイントが取れなくても、警告を出して残りを記録する。1日分の記録に失敗しても、残りの日は続ける。失敗した日があれば、終わりに0以外で終了する。
- 何をどの列に書くかは [references/notion-db.md](references/notion-db.md) にある。列を足す・変えるときは、判断の委任表の列の判断に聞いてから、スクリプトの `COLUMNS`・`build_*` とNotion側を同時に直す。

### 3. 報告する

チャットへは、DBごとの作成・更新・スキップの件数を返す。

- `[警告] ○○ の取得に失敗` があれば、どのエンドポイントが取れなかったかを伝える。`daily_resilience`・`daily_cardiovascular_age`・`vo2max` だけなら、認可のスコープ不足（oura-api-generic-logic の認証とトークンの判断）。
- 失敗した日があれば、その日を伝える。同期済みとして扱わない。
- `vo2max`・推奨就寝が直近の日で空なのは、取得漏れではない。
- 実行結果には、聞いたロジックスキルの名前と版（判断の委任表の版）を添えられるようにしておく。どの判断で記録したかを後から辿るため。

## 実行環境の癖（Windows / Git Bash）

- `python` で直接叩かず、`uv run` で起動する。
- `TZ=Asia/Tokyo` は使わない（ゾーン名の解決に失敗し、黙ってUTCになる）。スクリプトはJSTを `+09:00` の固定オフセットで持っている。
- 一時ファイルは `/tmp` ではなくスクラッチパッドの絶対パスを使う（Windows版の `python` は `/tmp/foo` を `C:\tmp\foo` と解釈する）。

## 他のスキルとの分担

| スキル | 担当 |
|---|---|
| oura-api-generic-logic | Oura API v2 を扱うときの一般的な判断と、APIを呼ぶ道具・認証情報 |
| notion-cli-generic-logic | Notionを扱うときの一般的な判断と、Notion REST APIを呼ぶ道具・トークン |
| 評価のスキル（diet-process-evaluation-app など） | 記録されたデータを読み、意味づけする。このスキルを評価の前に呼ぶ |
| このスキル | 何を記録するために、どの判断を聞き、何を実行するか。記録先のDB・列名・Ouraの項目との対応 |
