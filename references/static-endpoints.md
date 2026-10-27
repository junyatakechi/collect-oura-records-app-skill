# 変わることが少ないデータの記録

## 扱うこと

変わることが少ないデータ（`ring_configuration`・`personal_info`）を、DBに記録するか

## 答え方と理由

### 0. 判断全体

なし

### 1. DBに記録しない

`ring_configuration`・`personal_info` は、DBに記録しない。DBを作って記録しない。

1. （根拠）変わることが少ない。（決定日：記録なし）

### 2. 要るときに取る

要るときに、oura-api-generic-logic-skill の `oura_api.py` で取る。

1. 記録なし

## 判断定数

なし

## 未決

なし

## 求める材料

なし

## 計算

なし

## 道具

答え方2：oura-api-generic-logic-skill の `oura_api.py`。呼び方は、oura-api-generic-logic-skill の道具の呼び方の判断に従う。
