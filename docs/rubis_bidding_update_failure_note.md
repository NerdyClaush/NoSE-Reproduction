# RUBiS Bidding Update Failure Note

## 1. 目標

本階段原本目標是針對 RUBiS `bidding` mix 測試：

```text
Average Response Time
Weighted Average Response Time
```

測試對象：

```text
rubis_baseline
rubis_expert
rubis_nose_bidding
```

其中 `rubis_nose_bidding` 是透過：

```text
bundle exec nose search rubis --format=json --mix=bidding
```

產生的 NoSE schema recommendation。

## 2. 已成功的部分

以下步驟已成功：

```text
MySQL RUBiS schema initialization
RUBiS small source data generation
Cassandra keyspace reset
rubis_baseline create/load
rubis_expert create/load
rubis_nose_bidding search/create/load
```

其中 NoSE bidding schema search 成功產生：

```text
experiments/results/rubis_nose_bidding.json
```

這代表 NoSE advisor 可以處理 RUBiS bidding workload。

## 3. 失敗的部分

三組 schema 在執行 `bidding` mix 的 runtime benchmark 時都失敗，且 CSV output 為 0 bytes：

```text
experiments/results/rubis_baseline_bidding_100.csv
experiments/results/rubis_expert_bidding_100.csv
experiments/results/rubis_nose_bidding_100.csv
```

因此目前不能計算 bidding mix 的 average response time 與 weighted average response time。

## 4. 錯誤類型

### 4.1 rubis_baseline

錯誤：

```text
expecting exactly 6 bind parameters, 5 given
```

發生位置：

```text
nose_cli/execute.rb: bench_update
nose/backend/cassandra.rb: process
cassandra-driver prepared statement bind
```

### 4.2 rubis_expert

錯誤：

```text
expecting exactly 8 bind parameters, 7 given
```

同樣發生在 update execution path。

### 4.3 rubis_nose_bidding

錯誤：

```text
argument for "items_name" must be text,
2025-08-17 02:41:21 +0000 given
```

這表示 prepared statement 綁定時，某個 timestamp value 被送到 `items_name` 這類 text 欄位，疑似 update/support-query 結果與 insert/update parameter ordering 不一致。

## 5. 初步判斷

這不是 Cassandra 或 Docker 未啟動造成的錯誤，也不是資料完全無法載入。

比較合理的判斷是：

```text
NoSE advisor/search 可以處理 bidding workload；
Cassandra create/load 可以完成；
但 nose-cli runtime benchmark 在處理 updates 時，prepared statement parameter binding 出現不一致。
```

也就是問題集中在：

```text
update execution engine
support query result binding
manual plan / generated plan 的 runtime parameter ordering
```

## 6. 對復刻的影響

這個失敗很重要，因為論文 Fig. 17 / Fig. 18 的核心價值之一，正是 read/write 混合 workload 下的 schema trade-off。

目前我們已可復刻：

```text
browsing/read-only pipeline
NoSE browsing schema search/create/load/benchmark
baseline/expert browsing execute
```

但尚未復刻：

```text
bidding/update workload runtime benchmark
```

因此，在修復 update execution 前，不能宣稱已完整復刻 Fig. 17 / Fig. 18。

## 7. 下一步

建議下一步不是直接放大資料量，而是先處理小型 bidding update pipeline：

```text
1. 逐一以 --group 執行 bidding groups，找出第一個失敗的 request group。
2. 對照 rubis_baseline.rb / rubis_expert.rb / generated JSON 的 update plan。
3. 檢查 nose_cli/execute.rb 中 bench_update 的 parameter generation。
4. 檢查 nose/backend/cassandra.rb 中 prepared statement 欄位順序。
5. 修復或繞過 update execution 後，再重新計算 bidding weighted average。
```

在這之前，大規模 dataset 只會放大相同錯誤，無法得到有效的 Fig. 17 / Fig. 18 對照結果。
