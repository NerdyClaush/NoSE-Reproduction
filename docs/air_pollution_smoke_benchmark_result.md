# Air Pollution Smoke Benchmark Result

## 1. 實驗定位

本階段目標是先完成一個可執行的 Cassandra smoke benchmark：

```text
synthetic air pollution data
-> denormalized Cassandra tables
-> automated query workload
-> response-time summary
```

這還不是論文等級的 latency benchmark，因為目前使用 `docker compose exec ... cqlsh -e` 執行查詢，量測值包含 Docker exec 與 cqlsh 啟動成本。

## 2. 資料規模

本次跑三組合成資料：

| Rows | Stations | Pollutants | Query iterations |
|---:|---:|---:|---:|
| 2,000 | 20 | 11 | 30 |
| 5,000 | 20 | 11 | 30 |
| 10,000 | 20 | 11 | 30 |

每筆資料代表：

```text
station + pollutant + month -> average_value
```

合成資料額外加入：

```text
region_name
station_type
population_band
season
```

以提高資料多樣性。

## 3. Cassandra Tables

本次建立三張 denormalized tables：

| Table | Query behavior |
|---|---|
| `measurements_by_pollutant` | `PollutantTrend` |
| `measurements_by_station_month` | `StationMonthlySummary` |
| `measurements_by_station_pollutant` | `StationPollutantRange` |

`measurements_by_station_pollutant` 是本階段加入的 physical adaptation：

```text
PRIMARY KEY ((station_id, pollutant_id), month, measurement_id)
```

原因是 Cassandra 2.1 不允許在 `measurements_by_station_month` 中跳過 `measurement_id` 直接限制 `pollutant_id`。這代表 NoSE 的 logical query plan 轉成 Cassandra CQL 時，仍需要依 Cassandra key restriction 調整 physical schema。

## 4. Response-Time Summary

單位：ms。

| Rows | Query | Mean | P50 | P95 | Min | Max |
|---:|---|---:|---:|---:|---:|---:|
| 2,000 | `PollutantTrend` | 371.052 | 366.482 | 404.013 | 348.610 | 405.595 |
| 2,000 | `StationMonthlySummary` | 359.118 | 351.889 | 392.897 | 325.874 | 415.429 |
| 2,000 | `StationPollutantRange` | 355.597 | 353.632 | 397.341 | 328.789 | 399.201 |
| 5,000 | `PollutantTrend` | 393.438 | 389.053 | 425.645 | 364.744 | 430.829 |
| 5,000 | `StationMonthlySummary` | 341.494 | 338.205 | 360.002 | 328.557 | 361.591 |
| 5,000 | `StationPollutantRange` | 348.131 | 346.445 | 383.484 | 323.372 | 388.296 |
| 10,000 | `PollutantTrend` | 402.041 | 391.903 | 453.766 | 372.446 | 477.203 |
| 10,000 | `StationMonthlySummary` | 345.170 | 345.984 | 364.383 | 325.413 | 365.190 |
| 10,000 | `StationPollutantRange` | 343.993 | 339.743 | 378.629 | 320.182 | 380.466 |

## 5. 初步觀察

`PollutantTrend` 隨資料量增加有較明顯上升：

```text
371.052 ms -> 393.438 ms -> 402.041 ms
```

這是合理的，因為 partition key 是 `pollutant_id`，當資料量增加但污染物種類固定為 11 種，每個污染物 partition 會變大。

`StationMonthlySummary` 與 `StationPollutantRange` 反而相對穩定：

```text
StationMonthlySummary: 359.118 ms -> 341.494 ms -> 345.170 ms
StationPollutantRange: 355.597 ms -> 348.131 ms -> 343.993 ms
```

這可能是因為查詢範圍被 `station_id` 或 `(station_id, pollutant_id)` 分散，單次 query 掃到的資料較少；同時目前 cqlsh 啟動成本很高，容易蓋過 Cassandra 內部查詢差異。

這裡不能直接解讀成：

```text
資料量越大，查詢越快
```

比較合理的解釋是：

```text
目前資料量仍偏小，且量測方法的固定成本高於 Cassandra 真正查詢成本。
```

本階段使用 `docker compose exec ... cqlsh -e`，每一次 query 都包含：

```text
Docker exec startup
+ cqlsh process startup
+ cqlsh connection setup
+ Cassandra query execution
```

因此當資料量只有 2,000 到 10,000 rows 時，真正由資料量造成的查詢差異可能被固定開銷、OS 排程、JVM/Cassandra cache、compaction 狀態等因素掩蓋。

此外，`StationMonthlySummary` 與 `StationPollutantRange` 的 partition key 較具選擇性：

```text
StationMonthlySummary: station_id
StationPollutantRange: station_id + pollutant_id
```

資料增加時，資料被分散到多個 station 或 station-pollutant partition 中。若單次查詢命中的 partition 沒有明顯變大，latency 就不一定會隨整體 rows 單調上升。

因此本階段應解讀為：

```text
PollutantTrend 對資料量較敏感；
StationMonthlySummary / StationPollutantRange 在此規模與量測方式下尚未呈現明顯資料量效應。
```

若要確認資料量與 latency 的正相關，需要下一階段使用 long-running client、移除 cqlsh 啟動成本，並提高資料量級。

## 6. P95 是什麼？

`P95 latency` 是第 95 百分位數延遲。

意思是：

```text
將同一類 query 的所有 latency 從小排到大，
取位於 95% 位置附近的數值。
```

例如某 query 跑 100 次，P95 約代表第 95 慢的那次；換句話說，約有 95% 的查詢比這個值快，約 5% 的查詢比這個值慢。

P95 常用來觀察系統的 tail latency，也就是少數較慢請求的狀況。平均值 `mean` 可能被少數極端值拉動，也可能把慢查詢問題稀釋掉；P95 則更適合觀察使用者可能遇到的偏慢體驗。

在本實驗中：

```text
mean latency = 平均反應時間
p50 latency = 中位數反應時間
p95 latency = 偏慢查詢的代表值
```

但因為目前仍是 cqlsh smoke benchmark，P95 也會受到 Docker/cqlsh 啟動成本波動影響，不能直接視為 Cassandra server-side tail latency。

## 7. 圖表

```text
experiments/results/air_pollution_cassandra_benchmark_summary.png
```

## 8. 下一階段

若要往論文等級實驗靠近，需要：

```text
long-running client
-> warmup
-> repeated workload mix
-> larger scale datasets
-> controlled Cassandra cache/restart policy
-> response-time and execution-time separation
```

這樣才能比較接近論文中的執行時間與反應時間分析。
