#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""oura-collection-app: Oura Ring → Notion「OuraRing」配下5DBの同期。

使い方:
  uv run scripts/sync_oura_to_notion.py                      # 前日分を同期
  uv run scripts/sync_oura_to_notion.py --date 2026-05-16     # 指定日のみ同期
  uv run scripts/sync_oura_to_notion.py --start-date 2026-05-01 --end-date 2026-05-16
  uv run scripts/sync_oura_to_notion.py --dry-run             # Notionには書き込まず件数だけ表示
  uv run scripts/sync_oura_to_notion.py --env-file <path>     # Oura認証情報ファイルを指定

**判断はこのスキルに持たない。** Oura API側の事情(トークン・境界日・心拍・要約・
確定の遅れ・同一性・タグの2形式)は oura-api-generic-logic の判断と道具に、
Notionの呼び方は notion-cli-generic-logic の判断と道具に従う。どちらの道具も写さず、
importして呼ぶ。このスキルが持つのは、導入先の環境(記録先のDB・列名・Ouraの項目との対応)と手順だけ。
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta

_SKILLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(_SKILLS, "oura-api-generic-logic", "scripts"))
sys.path.insert(0, os.path.join(_SKILLS, "notion-cli-generic-logic", "scripts"))
import oura_records as R  # noqa: E402
from oura_api import fetch_many  # noqa: E402
from oura_auth import OuraAuthError, ensure_access_token  # noqa: E402
from notion_client import (  # noqa: E402
    EnvDataSources, NotionAuthError, NotionError, create_page, query_data_source, update_page,
)
from notion_props import (  # noqa: E402
    date_prop, multi_select_prop, number_prop, rich_text_prop, select_prop, title_prop,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- 記録先(導入先の環境)
# DBのURLは ~/.claude-skills-env/oura-collection-app.env の OURA_COLLECTION_DB_<KEY>_URL。
DS = EnvDataSources("oura-collection-app", "OURA_COLLECTION",
                    ("daily", "sleep", "session", "workout", "tag"))

DATE_COLUMN = "対象日時"

# 記録先の列名と型。conventions/notion-db.md が説明で、ここが正。
# 列を変えたらNotion側と同時にここを直す(notion-cli-generic-logic のスキーマの変更の判断)。
COLUMNS = {
    "daily": {
        "Name": "title", "対象日時": "date", "取得日時": "date",
        "睡眠スコア": "number", "睡眠_合計睡眠スコア": "number", "睡眠_深い睡眠スコア": "number",
        "睡眠_REMスコア": "number", "睡眠_restfulnessスコア": "number",
        "睡眠_タイミングスコア": "number", "睡眠_入眠潜時スコア": "number",
        "睡眠_効率スコア": "number", "睡眠_生データ": "rich_text",
        "活動スコア": "number", "歩数": "number", "アクティブカロリー": "number",
        "総消費カロリー": "number", "高強度活動時間_秒": "number",
        "中強度活動時間_秒": "number", "低強度活動時間_秒": "number",
        "座位時間_秒": "number", "活動_生データ": "rich_text",
        "準備度スコア": "number", "体温偏差": "number", "準備度_生データ": "rich_text",
        "回復力レベル": "select", "回復力_生データ": "rich_text",
        "心血管年齢": "number", "脈波伝播速度(PWV)": "number",
        "SpO2平均": "number", "呼吸障害指数(BDI)": "number",
        "ストレス日次サマリ": "select", "ストレスHigh時間_秒": "number",
        "回復High時間_秒": "number", "VO2Max": "number",
        "心拍_最低": "number", "心拍_平均": "number",
        "推奨就寝_ステータス": "select", "推奨就寝_推奨": "rich_text",
    },
    "sleep": {
        "Name": "title", "対象日時": "date", "開始時刻": "date", "終了時刻": "date",
        "種別": "select", "効率": "number", "就寝時間_秒": "number", "睡眠時間_秒": "number",
        "浅い睡眠_秒": "number", "深い睡眠_秒": "number", "レム睡眠_秒": "number",
        "入眠潜時_秒": "number", "覚醒時間_秒": "number", "平均心拍": "number",
        "最低心拍": "number", "平均HRV": "number", "平均呼吸数": "number",
        "生データ": "rich_text",
    },
    "session": {
        "Name": "title", "対象日時": "date", "開始": "date", "終了": "date",
        "種別": "select", "気分": "select", "生データ": "rich_text",
    },
    "workout": {
        "Name": "title", "対象日時": "date", "開始": "date", "終了": "date",
        "種目": "rich_text", "強度": "select", "消費カロリー": "number",
        "距離_m": "number", "ソース": "select", "ラベル": "rich_text",
        "生データ": "rich_text",
    },
    "tag": {
        "Name": "title", "対象日時": "date", "時刻": "date",
        "タグ種別": "multi_select", "内容": "rich_text", "形式": "select",
        "生データ": "rich_text",
    },
}

_WRAPPERS = {
    "title": title_prop, "rich_text": rich_text_prop, "number": number_prop,
    "select": select_prop, "multi_select": multi_select_prop,
}

DAILY_ENDPOINTS = [
    "daily_sleep", "daily_activity", "daily_readiness", "daily_resilience",
    "daily_cardiovascular_age", "daily_spo2", "daily_stress", "vo2max",
    "sleep_time", "heartrate",
]
INTERVAL_ENDPOINTS = ["sleep", "session", "workout", "enhanced_tag", "tag"]

DB_LABELS = {
    "daily": "Oura 日次サマリー",
    "sleep": "Oura 睡眠区間",
    "session": "Oura セッション",
    "workout": "Oura ワークアウト",
    "tag": "Oura タグ",
}


def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def _raw(record):
    return json.dumps(record, ensure_ascii=False)


def _now_iso():
    return datetime.now(R.JST).isoformat()


# ---------------------------------------------------------------- Oura → 列(材料の変換)

def build_daily(day, endpoints):
    """1日分の「Oura 日次サマリー」。取れなかったエンドポイントの項目は空のまま。"""
    f = lambda key: R.find_by_day(endpoints.get(key), key, day)  # noqa: E731
    daily_sleep, activity, readiness = f("daily_sleep"), f("daily_activity"), f("daily_readiness")
    resilience, cvage, spo2 = f("daily_resilience"), f("daily_cardiovascular_age"), f("daily_spo2")
    stress, vo2max, sleep_time = f("daily_stress"), f("vo2max"), f("sleep_time")
    hr_min, hr_avg = R.heart_rate_min_avg(endpoints.get("heartrate"), day)
    g = R.g
    return {
        "Name": day, "対象日時": day, "取得日時": _now_iso(),
        # 睡眠: contributors はスコア(0-100)であって時間ではない(oura-api-generic-logic の睡眠の判断)
        "睡眠スコア": g(daily_sleep, "score"),
        "睡眠_合計睡眠スコア": g(daily_sleep, "contributors", "total_sleep"),
        "睡眠_深い睡眠スコア": g(daily_sleep, "contributors", "deep_sleep"),
        "睡眠_REMスコア": g(daily_sleep, "contributors", "rem_sleep"),
        "睡眠_restfulnessスコア": g(daily_sleep, "contributors", "restfulness"),
        "睡眠_タイミングスコア": g(daily_sleep, "contributors", "timing"),
        "睡眠_入眠潜時スコア": g(daily_sleep, "contributors", "latency"),
        "睡眠_効率スコア": g(daily_sleep, "contributors", "efficiency"),
        "睡眠_生データ": _raw(daily_sleep),
        # 活動
        "活動スコア": g(activity, "score"),
        "歩数": g(activity, "steps"),
        "アクティブカロリー": g(activity, "active_calories"),
        "総消費カロリー": g(activity, "total_calories"),
        "高強度活動時間_秒": g(activity, "high_activity_time"),
        "中強度活動時間_秒": g(activity, "medium_activity_time"),
        "低強度活動時間_秒": g(activity, "low_activity_time"),
        "座位時間_秒": g(activity, "sedentary_time"),
        "活動_生データ": _raw(activity),
        # 準備度
        "準備度スコア": g(readiness, "score"),
        "体温偏差": g(readiness, "temperature_deviation"),
        "準備度_生データ": _raw(readiness),
        # 回復力
        "回復力レベル": g(resilience, "level"),
        "回復力_生データ": _raw(resilience),
        # 心血管年齢(PWVは実データで入るか未確認。oura-api-generic-logic の確定の判断)
        "心血管年齢": g(cvage, "vascular_age"),
        "脈波伝播速度(PWV)": g(cvage, "pulse_wave_velocity"),
        # SpO2
        "SpO2平均": g(spo2, "spo2_percentage", "average"),
        "呼吸障害指数(BDI)": g(spo2, "breathing_disturbance_index"),
        # ストレス
        "ストレス日次サマリ": g(stress, "day_summary"),
        "ストレスHigh時間_秒": g(stress, "stress_high"),
        "回復High時間_秒": g(stress, "recovery_high"),
        # VO2Max・推奨就寝は数日遅れで確定し、直近では空のことがある
        "VO2Max": g(vo2max, "vo2_max"),
        "心拍_最低": hr_min,
        "心拍_平均": hr_avg,
        "推奨就寝_ステータス": g(sleep_time, "status"),
        "推奨就寝_推奨": g(sleep_time, "recommendation", default=""),
    }


def build_sleep(record):
    day, kind = record.get("day"), record.get("type")
    return {
        "Name": f"{day} {kind}", "対象日時": day,
        "開始時刻": record.get("bedtime_start"), "終了時刻": record.get("bedtime_end"),
        "種別": kind, "効率": record.get("efficiency"),
        "就寝時間_秒": record.get("time_in_bed"),
        "睡眠時間_秒": record.get("total_sleep_duration"),
        "浅い睡眠_秒": record.get("light_sleep_duration"),
        "深い睡眠_秒": record.get("deep_sleep_duration"),
        "レム睡眠_秒": record.get("rem_sleep_duration"),
        "入眠潜時_秒": record.get("latency"),
        "覚醒時間_秒": record.get("awake_time"),
        "平均心拍": record.get("average_heart_rate"),
        "最低心拍": record.get("lowest_heart_rate"),
        "平均HRV": record.get("average_hrv"),
        "平均呼吸数": record.get("average_breath"),
        "生データ": _raw(record),
    }


def build_session(record):
    day, kind = record.get("day"), record.get("type")
    return {
        "Name": f"{day} {kind}", "対象日時": day,
        "開始": record.get("start_datetime"), "終了": record.get("end_datetime"),
        "種別": kind, "気分": record.get("mood"), "生データ": _raw(record),
    }


def build_workout(record):
    day, activity = record.get("day"), record.get("activity")
    return {
        "Name": f"{day} {activity}", "対象日時": day,
        "開始": record.get("start_datetime"), "終了": record.get("end_datetime"),
        "種目": activity, "強度": record.get("intensity"),
        "消費カロリー": record.get("calories"), "距離_m": record.get("distance"),
        "ソース": record.get("source"), "ラベル": record.get("label"),
        "生データ": _raw(record),
    }


def build_tag(record, kind):
    """「時刻」はdate型1列の期間(start+end)。理由は references/time-columns.md。"""
    t = R.normalize_tag(record, kind)
    label = "enhanced_tag" if kind == "enhanced_tag" else "tag(旧)"
    title_text = t["content"] or (t["codes"][0] if t["codes"] else label)
    return {
        "Name": f"{t['day']} {title_text}"[:200], "対象日時": t["day"],
        "時刻": [t["start"], t["end"]], "タグ種別": t["codes"],
        "内容": t["content"], "形式": label, "生データ": _raw(record),
    }


def to_properties(entity, record):
    """列名をキーにした素の値 → Notionプロパティ。

    **知らない列が来たら落とす。** 黙って捨てると「入れたつもりで入っていない」という
    最も気づきにくい壊れ方をするため、書けないものは書けないと即座に言う。
    """
    spec = COLUMNS[entity]
    out = {}
    for key, value in record.items():
        kind = spec.get(key)
        if kind is None:
            raise ValueError(f"{entity} に '{key}' という列は無い。"
                             "列を増やしたならNotion側とCOLUMNSの両方を直すこと")
        if kind == "date":
            start, end = value if isinstance(value, (list, tuple)) else (value, None)
            out[key] = date_prop(start, end)
        else:
            out[key] = _WRAPPERS[kind](value)
    return out


# ---------------------------------------------------------------- 記録先の読み書き

def _day_pages(entity, day):
    return query_data_source(DS[entity], {"filter": {"and": [
        {"property": DATE_COLUMN, "date": {"on_or_after": day}},
        {"property": DATE_COLUMN, "date": {"on_or_before": day}},
    ]}})


def _text(prop):
    if not prop or prop.get("type") not in ("rich_text", "title"):
        return ""
    return "".join(x["plain_text"] for x in prop[prop["type"]])


class RecordedIds:
    """対象日に記録済みのOura record idを、(DB, 日)ごとに1回だけ引いて持つ。

    区間のレコードは同じ日に複数ありうるので、record id で重複を判定する
    (oura-api-generic-logic のレコードの同一性の判断)。idは「生データ」列のJSONに入っている。
    """

    def __init__(self):
        self._raw = {}

    def contains(self, entity, day, record_id):
        if not record_id:
            return False
        key = (entity, day)
        if key not in self._raw:
            self._raw[key] = [
                _text(v) for p in _day_pages(entity, day)
                for k, v in p["properties"].items() if "生データ" in k
            ]
        return any(record_id in text for text in self._raw[key])


def sync_one_day(day, daily_data, interval_data, dry_run, counters, recorded):
    log(f"=== {day} ===")

    # 日次サマリー: 数日遅れで確定する項目があるので、既にあっても上書きする
    # (oura-api-generic-logic のデータが確定する時期の判断)。
    existing = _day_pages("daily", day)
    props = to_properties("daily", build_daily(day, daily_data))
    if existing:
        if not dry_run:
            update_page(existing[0]["id"], {"properties": props})
        log(f"  {'[dry-run] ' if dry_run else ''}日次サマリーを更新")
        counters["daily_update"] += 1
    else:
        if not dry_run:
            create_page({"parent": {"data_source_id": DS["daily"]}, "properties": props})
        log(f"  {'[dry-run] ' if dry_run else ''}日次サマリーを作成")
        counters["daily_create"] += 1

    # 区間: record id が記録済みなら飛ばす
    plans = [
        ("sleep", "sleep", build_sleep),
        ("session", "session", build_session),
        ("workout", "workout", build_workout),
        ("tag", "enhanced_tag", lambda r: build_tag(r, "enhanced_tag")),
        ("tag", "tag", lambda r: build_tag(r, "tag")),
    ]
    for entity, endpoint, build in plans:
        for record in R.records_on_day(interval_data.get(endpoint), endpoint, day):
            if recorded.contains(entity, day, record.get("id")):
                counters[f"{entity}_skip"] += 1
                continue
            props = to_properties(entity, build(record))
            if not dry_run:
                create_page({"parent": {"data_source_id": DS[entity]}, "properties": props})
            counters[f"{entity}_create"] += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD (単日)")
    parser.add_argument("--start-date", help="YYYY-MM-DD")
    parser.add_argument("--end-date", help="YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Notionには書き込まず件数のみ表示")
    parser.add_argument("--env-file", help="Oura認証情報ファイル(既定は oura-api-generic-logic の環境ファイル)")
    args = parser.parse_args()

    if args.date:
        start = end = date.fromisoformat(args.date)
    elif args.start_date and args.end_date:
        start, end = date.fromisoformat(args.start_date), date.fromisoformat(args.end_date)
    else:
        # 既定: 前日分(データは翌朝に確定する。oura-api-generic-logic のデータが確定する時期の判断)
        start = end = date.today() - timedelta(days=1)

    counters = {f"{k}_{s}": 0 for k in DB_LABELS for s in ("create", "skip")}
    counters["daily_update"] = 0

    # 期間全体を1回で取り、日ごとの振り分けはメモリ上で行う。境界日を取りこぼさないよう
    # 前後1日を足す(oura-api-generic-logic のAPIの呼び方・境界日の取りこぼしの判断)。
    token = ensure_access_token(args.env_file)
    fetch_start, fetch_end = R.padded_range(start, end)
    log(f"Oura APIから {fetch_start}〜{fetch_end} のデータを一括取得中...")
    warn = lambda key, e: log(f"  [警告] {key} の取得に失敗: {e}")  # noqa: E731
    daily_data = fetch_many(DAILY_ENDPOINTS, token, fetch_start, fetch_end, on_error=warn)
    interval_data = fetch_many(INTERVAL_ENDPOINTS, token, fetch_start, fetch_end, on_error=warn)
    log("一括取得完了。日別の同期を開始します。")

    recorded = RecordedIds()
    failed_days = []
    d = start
    while d <= end:
        try:
            sync_one_day(d.isoformat(), daily_data, interval_data, args.dry_run, counters, recorded)
        except NotionAuthError:
            # トークン未設定・失効は日を変えても直らない。残り全日を試さず即中断する。
            raise
        except Exception as e:  # 1日分の失敗で全体を止めない
            log(f"  [エラー] {d.isoformat()} の同期に失敗: {e}")
            failed_days.append(d.isoformat())
        d += timedelta(days=1)

    log("=== 完了 ===" + ("(dry-run のため実際には書き込んでいません)" if args.dry_run else ""))
    for key, label in DB_LABELS.items():
        if key == "daily":
            log(f"{label}: 新規作成 {counters['daily_create']}件 / 更新 {counters['daily_update']}件")
        else:
            log(f"{label}: 作成 {counters[f'{key}_create']}件 / スキップ(重複) {counters[f'{key}_skip']}件")

    # 失敗を「完了」に紛れ込ませない。終了コードが0だと、呼び出し側が同期済みと
    # 誤認したまま古いデータで評価してしまう。
    if failed_days:
        sys.exit(f"同期に失敗した日が {len(failed_days)}件 あります: {', '.join(failed_days)}")


if __name__ == "__main__":
    try:
        main()
    except (NotionError, OuraAuthError) as e:
        sys.exit(f"Error: {e}")
