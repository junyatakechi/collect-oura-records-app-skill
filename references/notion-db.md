# 記録先のDB

どのOuraのデータを、どのDBの、どの列に書くか。判断ではなく、この環境での記録の取り決め。
**列名と型の正は `scripts/sync_oura_to_notion.py` の `COLUMNS`、Ouraの項目との対応の正は同じファイルの `build_*`。** この文書は説明で、変えるときはスクリプトとNotion側を同時に直す。

## DB

Notionの「OuraRing」ページ配下の5つ。URLは環境ファイル `~/.claude-skills-env/oura-collection-app.env` にある。

| DB | URLのキー | 1件の単位 | Ouraのエンドポイント | 既にあったら |
|---|---|---|---|---|
| Oura 日次サマリー | `OURA_COLLECTION_DB_DAILY_URL` | 1日 | `daily_sleep`・`daily_activity`・`daily_readiness`・`daily_resilience`・`daily_cardiovascular_age`・`daily_spo2`・`daily_stress`・`vo2max`・`sleep_time`・`heartrate` | `対象日時` が同じページを上書き |
| Oura 睡眠区間 | `OURA_COLLECTION_DB_SLEEP_URL` | 1区間 | `sleep` | 生データに同じ record id があれば飛ばす |
| Oura セッション | `OURA_COLLECTION_DB_SESSION_URL` | 1セッション | `session` | 同上 |
| Oura ワークアウト | `OURA_COLLECTION_DB_WORKOUT_URL` | 1件 | `workout` | 同上 |
| Oura タグ | `OURA_COLLECTION_DB_TAG_URL` | 1件 | `enhanced_tag`・`tag` | 同上 |

- 既にあったときの扱いは、oura-api-generic-logic のレコードの同一性・データが確定する時期の判断に従う。
- `ring_configuration`・`personal_info` はDBを作っていない。変わることが少ないので、要るときに oura-api-generic-logic の `oura_api.py` で取る。

## 列

全DBに共通して、`Name`（title）と `対象日時`（date。Ouraがつけた日付）を持つ。

| DB | 列（型） |
|---|---|
| 日次サマリー | `取得日時`（date）、睡眠のスコア8列（number）、活動・準備度・心血管年齢・SpO2・ストレス・VO2Max・心拍の数値（number）、`回復力レベル`・`ストレス日次サマリ`・`推奨就寝_ステータス`（select）、`推奨就寝_推奨`（rich_text）、`睡眠_生データ`・`活動_生データ`・`準備度_生データ`・`回復力_生データ`（rich_text） |
| 睡眠区間 | `開始時刻`・`終了時刻`（date）、`種別`（select）、`効率`・秒の7列・心拍・HRV・呼吸数（number）、`生データ`（rich_text） |
| セッション | `開始`・`終了`（date）、`種別`・`気分`（select）、`生データ`（rich_text） |
| ワークアウト | `開始`・`終了`（date）、`種目`・`ラベル`（rich_text）、`強度`・`ソース`（select）、`消費カロリー`・`距離_m`（number）、`生データ`（rich_text） |
| タグ | `時刻`（date。開始と終了の期間）、`タグ種別`（multi_select）、`内容`（rich_text）、`形式`（select。`enhanced_tag` か `tag(旧)`）、`生データ`（rich_text） |

- 個別の列が全部そろっているわけではない。個別の列に無い項目は、`生データ` の列（長大な時系列は要約済み）で追う。
- 列の名前に「_秒」が付く列は秒のまま。「睡眠_○○スコア」は0〜100のスコアで、時間ではない。読み方は oura-api-generic-logic の睡眠区間と日次の睡眠の読み方の判断に従う。

## 時間を持つ列の形（2026-08-10決定）

睡眠区間・セッション・ワークアウトは**開始・終了の2列**、タグだけ**date型1列の期間（start+end）**で持つ。

- 前者は必ず期間を持つ活動なので、終了だけでのソート・フィルタが効く2列が自然。
- タグは瞬間タグと期間タグが混在していて、実データでは大半の行が終了を持たない。専用の終了列を作ると大半が空欄になり、「まだ埋めていない」のか「元々終わりが無い」のか区別できなくなる。1列の期間にして「endが無い＝瞬間タグ」と読めるようにした。

## 記録の限界

| 記録の限界 | 扱い |
|---|---|
| タグは `enhanced_tag` と旧 `tag` で二重に記録されることがある | 記録する側では除かない。数える側が除く（oura-api-generic-logic のタグの読み方の判断） |
| 睡眠区間には昼寝が混ざり、`対象日時` はOuraの日付 | 夜の睡眠だけを見る・日付で引く側の扱いは、oura-api-generic-logic の睡眠区間の判断 |
| `脈波伝播速度(PWV)` は常に空の可能性が高い | 取得漏れではない（oura-api-generic-logic の未決） |
