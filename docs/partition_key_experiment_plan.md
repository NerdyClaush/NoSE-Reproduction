# Partition Key Experiment Plan

## 1. 為什麼要做這個實驗？

目前的 smoke benchmark 已經顯示：

```text
PollutantTrend latency 明顯隨資料量上升
StationMonthlySummary latency 相對穩定
StationPollutantRange latency 緩慢上升
```

這個現象不只和總資料量有關，更可能和 partition key 的資料分散程度有關。

因此下一步應該測：

```text
資料量固定時，改變 partition key cardinality，latency 是否改變？
```

這比單純增加 rows 更能說明 NoSQL schema design 的核心問題。

## 2. 核心假設

### Hypothesis A: partition 越粗，latency 越高

`PollutantTrend` 使用：

```text
PRIMARY KEY ((pollutant_id), month, measurement_id)
```

因為污染物只有 11 種，所以資料會集中在少數 partition。

若總資料量為 1,000,000 rows：

```text
1,000,000 / 11 ~= 90,909 rows per pollutant partition
```

這會造成 large partition，查詢趨勢時 latency 明顯上升。

### Hypothesis B: partition 越細，單次查詢越穩定

`StationPollutantRange` 使用：

```text
PRIMARY KEY ((station_id, pollutant_id), month, measurement_id)
```

若有 20 stations 與 11 pollutants：

```text
20 * 11 = 220 partitions
1,000,000 / 220 ~= 4,545 rows per partition
```

所以它比 `PollutantTrend` 穩定。

## 3. 建議實驗組

### Experiment 1: 固定 rows，改變 stations

固定：

```text
rows = 1,000,000
pollutants = 11
```

變動：

```text
stations = 20, 100, 500
```

預期：

| Query | 預期結果 |
|---|---|
| `PollutantTrend` | 幾乎不受 stations 影響，因為 partition key 只有 `pollutant_id` |
| `StationMonthlySummary` | stations 越多，單 station partition 越小，latency 可能更穩定 |
| `StationPollutantRange` | stations 越多，`station_id + pollutant_id` partition 越小，latency 可能下降 |

這組實驗最能證明：

```text
不是總資料量本身決定 latency，而是 access pattern 命中的 partition 大小。
```

### Experiment 2: 固定 rows，改變 pollutant distribution

固定：

```text
rows = 1,000,000
stations = 20
pollutants = 11
```

變動：

```text
uniform distribution
skewed distribution
```

例如讓 `PM2.5` 佔 50% rows。

預期：

| Query | 預期結果 |
|---|---|
| `PollutantTrend` | 查 `PM2.5` 會比查其他污染物慢 |
| `StationPollutantRange` | 若 partition key 包含 station，skew 影響會被分散 |

這組可以展示 hot partition 問題。

### Experiment 3: 比較 schema 選擇

比較：

```text
measurements_by_pollutant
measurements_by_station_pollutant
```

對同樣的 trend/range 類查詢，觀察不同 partition key 是否造成 latency 差異。

這組可以用來說明：

```text
NoSQL schema 是 query-specific 的；同一份資料可以因不同 key design 呈現完全不同的效能。
```

## 4. 算力評估

目前 1,000,000 rows 已可在本機 Docker 跑完，但載入時間明顯增加。

初步觀察：

| Table | 1m rows 載入時間 |
|---|---:|
| `measurements_by_pollutant` | 約 56 秒 |
| `measurements_by_station_month` | 約 15 秒 |
| `measurements_by_station_pollutant` | 約 80 秒 |

因此下一階段建議先不要直接跳到 5m 或 10m。

較合理順序：

```text
1m rows, stations = 20
1m rows, stations = 100
1m rows, stations = 500
```

如果這三組跑得穩，再考慮：

```text
2m rows
5m rows
```

## 5. 報告價值

這個實驗比單純資料量放大更有解釋力，因為它可以回答：

```text
為什麼某些 query 隨資料量明顯變慢，而某些 query 幾乎不變？
```

答案不只是：

```text
資料量變大
```

而是：

```text
query 命中的 partition 變大。
```

這可以連回 NoSE 的核心精神：

```text
workload-driven schema design 必須考慮 access pattern 與 key design。
```

## 6. 下一步

需要修改 synthetic generator，使它支援任意 station count，而不是受限於目前內建 station name 清單。

完成後即可跑：

```powershell
powershell -ExecutionPolicy Bypass -Command "& workspace\air_pollution\run_synthetic_benchmark_matrix.ps1 -Rows @(1000000) -Stations 20 -Iterations 10"
powershell -ExecutionPolicy Bypass -Command "& workspace\air_pollution\run_synthetic_benchmark_matrix.ps1 -Rows @(1000000) -Stations 100 -Iterations 10"
powershell -ExecutionPolicy Bypass -Command "& workspace\air_pollution\run_synthetic_benchmark_matrix.ps1 -Rows @(1000000) -Stations 500 -Iterations 10"
```
