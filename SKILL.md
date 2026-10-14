---
name: oura-collection-app
description: Oura Ring のデータ（睡眠・活動・準備度・回復力・心血管年齢・SpO2・ストレス・VO2Max・心拍・睡眠区間・セッション・ワークアウト・タグ）を取得し、Notionの「OuraRing」配下の5つのDBへ記録するアプリケーションスキル。「Ouraのデータを同期して」「Ouraの睡眠データを記録して」「Oura Ringの記録を更新して」のように言われたときや、評価のスキル（diet-process-evaluation-app など）から評価の前の最新化として頼まれたときに使う。Oura API側の判断（トークン・境界日・心拍・生データの要約・データの確定の遅れ・レコードの同一性・タグの2形式）は外部の generic-logic（oura-api-generic-logic）に、Notionの呼び方は notion-cli-generic-logic に委ね、どちらの道具も写さず自分で呼ぶ。切り出した判断はこのスキルに持たず、判断の委任表の判断先の判断ファイルに聞く。記録先のDB・列名・Ouraの項目との対応と手順を持ち、まだ切り出していない判断は references に置く。取得したデータの解釈・評価はしない。
metadata:
  version: "0.2.0"
  repository: "https://github.com/junyatakechi/oura-collection-app"
---

# Ouraのデータの記録

## このスキルが守る一番のこと

**切り出した判断は、このスキルに書かない。下の判断の委任表の判断先の、外部のロジックスキルに委ねる。**
ここにあるのは、OuraのデータをNotionに記録するために、どの判断を外部に委ね、何を実行するかだけ。
まだ切り出していない判断は、このスキルの `references/` に判断ファイルの形で置き、判断の委任表から指す。
Ouraの癖（使い捨てのトークン・境界日の取りこぼし・心拍の範囲指定・数日遅れの確定・タグの2形式）は、どれも oura-api-generic-logic の判断と道具が持つ。ここで写したり、言い換えて書き直したりしない。

もう1つは、**ロジックスキルに無い判断を一般論で埋めない**こと。
判断が無いときは「判断が無い」と書き、本人に聞く。とくに、レスポンスを見て「この項目はたぶん○○」と推測で列を足さない。

## 判断の委任表

記録で必要になる判断について、何を（聞きたい事）、どの判断先に、どんな答えの形で聞くか。**中核の判断（core-logic）・一般的な判断（generic-logic）・まだ切り出していない判断を、別々の表に分けて持つ。** 中核の判断は差し替えて別の人の視点を使うもの、一般的な判断は共有して育てるもの、まだ切り出していない判断は切り出す候補で、差し替え方も見直す時期も違うため。

- **聞きたい事はこのスキルが持つ。** 判断ファイルは問いを持たない。聞きたい事に判断ファイルで答えられないときは、ロジックスキルが「判断が無い」と返す。
- **答えの形はこのスキルが決める。**
- **材料はロジックスキルが求める。** 何を渡すかは、聞いたときにロジックスキルが返す「求める材料」に従う。このスキルは、ロジックスキルの判断ファイルを自分で読まない。
- **聞くときは、聞きたい事・判断先・欲しい答えの形の3つを伝える。**
- 判断先は、スキルのフォルダからの判断ファイルのパスで書く。差し替えるときは、判断先の列と、使用するリポジトリ表の行だけを書き換える。聞きたい事と答えの形は変えない。
- 判断先の版の2桁目が上がったら、手順とスクリプトを合わせてから、使用するリポジトリ表の版を更新する。3桁目だけが上がったときは、このスキルを直さない。
- 差し替える前に、差し替え先の判断ファイルが、聞きたい事に答えられるかを確かめる。

### 中核の判断（core-logic）

無し。記録には、人によって答えが分かれる判断が無い。データの読み方（HRVの落ち込みをどう見るか、など）は、記録を読む側の評価のスキルが core-logic に聞く。

### 一般的な判断（generic-logic）

| 聞きたい事 | 判断先 | 欲しい答えの形 |
|---|---|---|
| Ouraのトークンを、どう取り、どう更新すれば壊さずに済むか | `oura-api-generic-logic/references/auth.md` | トークンの取り方と、守ること（道具の使い方） |
| Ouraの道具を、どの入口から呼ぶか | `oura-api-generic-logic/references/client-usage.md` | 呼ぶ関数の順と、呼び出し側で書かないこと（道具の使い方） |
| 期間をどう指定し、対象日のレコードをどう拾うか | `oura-api-generic-logic/references/date-boundary.md` | 取得範囲の出し方と、対象日のレコードを返す関数（道具の使い方） |
| 心拍を、どう取り、日ごとにどう集計するか | `oura-api-generic-logic/references/heartrate.md` | 取り方と、集計の関数（道具の使い方） |
| 生データを、どう残すか | `oura-api-generic-logic/references/raw-data.md` | 残す形と、要約の有無（道具の使い方） |
| 何日の分を、いつ取り、記録済みの日次をどうするか | `oura-api-generic-logic/references/data-latency.md` | 既定の対象日、日次を上書きするか、空の項目の読み方 |
| 何で重複を判定し、既にあったらどうするか | `oura-api-generic-logic/references/record-identity.md` | エンドポイントごとの一意キーと、既にあったときの扱い |
| タグの2つの形式を、どう記録するか | `oura-api-generic-logic/references/tags.md` | 形をそろえる関数と、終了時刻の扱い（道具の使い方） |
| Notionを読み書きするとき、道具をどう呼ぶか | `notion-cli-generic-logic/references/client-usage.md` | どの入口から呼ぶかと、呼び出し側で書かないこと（道具の使い方） |
| 記録先のDBの列を足す・変えるとき、どう進めるか | `notion-cli-generic-logic/references/schema-change.md` | 進め方と、守ること（道具の使い方） |
| 記録したあと、何を確かめ、崩れていたらどう直すか | `notion-cli-generic-logic/references/write-verification.md` | 確かめることと直し方（道具の使い方） |

- 同期のたびに聞くのは無い。どの判断も `scripts/sync_oura_to_notion.py` を書いたときに聞き、返ってきた道具の使い方どおりに呼んでいる。スクリプトを直すとき・判断先の版が上がったときに聞き直す。
- 列の判断は、列を足す・変えるときだけ聞く。同期が401・400・404で失敗したときは、認証とトークン・APIの呼び方・心拍の判断に聞く。
- 返ってきた道具の使い方に従い、どちらのロジックスキルの道具も写さず、自分で呼ぶ。
- 一般的な判断は差し替えるより、新しく踏んだ落とし穴を判断先のスキルに足して育てる。

### まだ切り出していない判断（このスキル）

| 聞きたい事 | 判断先 | 欲しい答えの形 |
|---|---|---|
| 一部のエンドポイントや日の取得に失敗したとき、続けるか止めるか | `oura-collection-app/references/partial-failure.md` | 続ける範囲と、終了の仕方 |
| 時間を持つ記録を、どの列の形で持つか | `oura-collection-app/references/time-columns.md` | DBごとの列の形 |
| 変わることが少ないデータ（`ring_configuration`・`personal_info`）を、DBに記録するか | `oura-collection-app/references/static-endpoints.md` | 記録する / しない と、要るときの取り方 |

- このスキルの判断ファイルは、このスキルが自分で読んで当てはめる。
- 齟齬が見つかったら、ここが切り出す候補になる。切り出すときは、判断ファイルをロジックスキルへ移し、行を上の表へ移して判断先を書き換える。

## 使用するリポジトリ表

判断の委任表の判断先に出てくるスキルを、どこから取るか。版はこの表だけで持つ。

| スキル名 | リポジトリのURL | 版 |
|---|---|---|
| `oura-api-generic-logic` | https://github.com/junyatakechi/oura-api-generic-logic | 0.1.x |
| `notion-cli-generic-logic` | https://github.com/junyatakechi/notion-cli-generic-logic | 0.2.x |

- 版は、そのスキルの版（`metadata.version`）の先頭2桁に、`.x` を付けた形（例：`0.2.x`）。3桁目はどの版でもよいことを表す。3桁目だけが上がった版は、この表を直さずにそのまま使う。3桁目は、呼び出し側が何も合わせなくてよい変更だけで上がるため。
- 判断先を別の人のスキルに差し替えるときは、この表の行も差し替える。

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

- **何日の分を取るか。** 指定が無ければ前日分。ユーザーや依頼元のスキルが期間を言ったら、その期間を渡す。今日の行（昨夜の睡眠）が要るときは `--date` で今日を明示する。根拠は oura-api-generic-logic のデータが確定する時期の判断。
- 日次サマリーは既にあっても上書きし、区間（睡眠区間・セッション・ワークアウト・タグ）は記録済みの record id を飛ばす。何度実行しても重複しない。
- 一部の取得に失敗したときの扱いは、まだ切り出していない判断（`references/partial-failure.md`）に聞く。
- 何をどの列に書くかは [conventions/notion-db.md](conventions/notion-db.md) にある。列を足す・変えるときは、判断の委任表の列の判断に聞いてから、スクリプトの `COLUMNS`・`build_*` とNotion側を同時に直す。

### 3. 報告する

チャットへは、DBごとの作成・更新・スキップの件数を返す。依頼元のスキルから頼まれたときは、依頼元が欲しい結果を満たしたか確かめられるように、同じ内容を返す。

- `[警告] ○○ の取得に失敗` があれば、どのエンドポイントが取れなかったかを伝える。`daily_resilience`・`daily_cardiovascular_age`・`vo2max` だけなら、認可のスコープ不足（oura-api-generic-logic の認証とトークンの判断）。
- 失敗した日があれば、その日を伝える。同期済みとして扱わない。
- `vo2max`・推奨就寝が直近の日で空なのは、取得漏れではない。
- 実行結果には、聞いたロジックスキルの名前と、実際に使った版（実行時に判断先の `metadata.version` を読んだ3桁）を添えられるようにしておく。どの判断で記録したかを後から辿るため。
