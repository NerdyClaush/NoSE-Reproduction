# Air Pollution Benchmark Plan

## 1. Pipeline 修正

對一般 CSV 資料集而言，不需要經過 MySQL。

NoSE schema design 階段：

```text
CSV
-> preprocessing / profiling
-> NoSE model DSL
-> NoSE workload DSL
-> NoSE advisor/search
-> schema recommendation / query plan
```

Cassandra 實測階段：

```text
CSV or synthetic generator
-> denormalized CSV files matching recommended indexes
-> Cassandra schema
-> Cassandra loader
-> automated query script
-> latency / response-time report
```

MySQL 目前只應視為 RUBiS 複現線的一部分，不是空污資料集的必要元件。

## 2. 為什麼需要額外的自動化查詢腳本？

論文 evaluation 重點包含：

- 查詢成本推估。
- schema size。
- workload mix。
- query execution / response time。

NoSE advisor 本身只會產生 schema recommendation 與 query plan；若要量測實際 Cassandra 反應時間，就必須額外寫 benchmark runner。

因此目前分成兩層：

| 層級 | 目的 | 目前狀態 |
|---|---|---|
| NoSE advisor test | 驗證模型與 workload 是否能被 NoSE 分析 | 已完成 |
| Cassandra smoke benchmark | 實際載入資料並跑查詢 | 已新增腳本，可開始測 |
| Paper-grade benchmark | 長駐 client、warmup、重複實驗、統計延遲 | 尚未完成 |

## 3. 已新增腳本

### 3.1 產生 2,000 到 10,000 筆合成資料

```powershell
& 'C:\Users\Rachel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  workspace\air_pollution\generate_synthetic_dataset.py `
  --rows 10000 `
  --stations 20
```

輸出位置：

```text
experiments/data/air_pollution_synthetic/
```

主要輸出：

| 檔案 | 用途 |
|---|---|
| `measurements_normalized.csv` | 正規化後的原始資料 |
| `measurements_by_pollutant.csv` | 對應 NoSE I1 的 denormalized table |
| `measurements_by_station_month.csv` | 對應 NoSE I2 的 denormalized table |
| `measurements_by_station_pollutant.csv` | 對應區間查詢的 Cassandra physical table |
| `schema.cql` | Cassandra keyspace/table schema |
| `manifest.json` | 本次合成資料的維度設定 |

合成資料的維度：

```text
Station x Pollutant x Month
+ region_name
+ station_type
+ population_band
+ season
```

數值生成不是單純 random，而是依污染物基準值疊加：

```text
base pollutant value
* seasonal bias
* station type bias
* pollutant-specific station bias
+ gaussian noise
```

例如：

- `traffic` 測站會提高 `NO`, `NO2`, `NOx`。
- `industrial` 測站會提高 `PM2.5`, `PM10`, `SO2`。
- `background` 測站污染值較低，但 `O3` 可能較高。
- `winter` 會提高 `PM2.5`, `PM10`, `NOx` 類污染。
- `summer` 會提高 `O3`。

### 3.2 載入 Cassandra

```powershell
powershell -ExecutionPolicy Bypass -File workspace\air_pollution\load_synthetic_to_cassandra.ps1
```

這會建立：

```text
air_pollution.measurements_by_pollutant
air_pollution.measurements_by_station_month
air_pollution.measurements_by_station_pollutant
```

`measurements_by_station_pollutant` 是一個 Cassandra physical adaptation。NoSE read-only plan 將 `StationPollutantRange` 表示為 `I2 + filter`，但 Cassandra 2.1 不允許在沒有先限制前序 clustering column 的情況下限制 `pollutant_id`。因此實測階段額外建立此表，讓區間查詢可以使用合法的 partition key：

```text
PRIMARY KEY ((station_id, pollutant_id), month, measurement_id)
```

### 3.3 執行 smoke benchmark

```powershell
& 'C:\Users\Rachel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  workspace\air_pollution\benchmark_cassandra_smoke.py `
  --iterations 30 `
  --stations 20
```

輸出：

```text
experiments/results/air_pollution_cassandra_smoke.csv
experiments/results/air_pollution_cassandra_smoke_summary.csv
```

### 3.4 執行 2,000 / 5,000 / 10,000 rows 實驗矩陣

```powershell
powershell -ExecutionPolicy Bypass -File workspace\air_pollution\run_synthetic_benchmark_matrix.ps1
```

這會依序：

```text
generate synthetic data
-> load Cassandra
-> run query benchmark
-> write result CSV
```

輸出範例：

```text
experiments/results/air_pollution_cassandra_2000.csv
experiments/results/air_pollution_cassandra_2000_summary.csv
experiments/results/air_pollution_cassandra_5000.csv
experiments/results/air_pollution_cassandra_5000_summary.csv
experiments/results/air_pollution_cassandra_10000.csv
experiments/results/air_pollution_cassandra_10000_summary.csv
```

### 3.5 產生 benchmark 圖表

```powershell
& 'C:\Users\Rachel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  workspace\air_pollution\plot_benchmark_summary.py
```

輸出：

```text
experiments/results/air_pollution_cassandra_benchmark_summary.png
```

## 4. 目前 benchmark 的限制

目前的 benchmark 使用 `docker compose exec ... cqlsh -e` 逐次執行查詢，因此量到的是：

```text
host Python script
+ docker exec overhead
+ cqlsh startup overhead
+ Cassandra query time
```

這適合做 smoke benchmark，也就是確認：

- schema 可以建立。
- 資料可以載入。
- 查詢可以跑。
- 不同 query pattern 有初步可比較的反應時間。

但它不適合直接宣稱為論文等級的 response time。

若要更貼近論文，需要改成：

```text
long-running benchmark client
-> warmup
-> repeated workload mix
-> percentile latency
-> multiple dataset sizes
-> controlled Cassandra cache / restart policy
```

## 5. 建議資料量

目前原始空污 CSV 只有 55 rows，展示性足夠，但實驗鑑賞度有限。

建議先做三組：

| 規模 | 用途 |
|---|---|
| 2,000 rows | 快速驗證 loader/query |
| 5,000 rows | 中間規模 smoke benchmark |
| 10,000 rows | 報告展示用的小型延伸實驗 |

若要更像論文 evaluation，再逐步提高到 100,000 rows 以上。
