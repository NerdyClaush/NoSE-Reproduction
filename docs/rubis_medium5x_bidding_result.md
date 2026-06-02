# RUBiS Medium 5x Bidding Result

## 1. 目的

本次實驗將 RUBiS generator 的資料量由小型 pilot 放大 5 倍，用來觀察資料量增加後：

```text
Average Response Time
Weighted Average Response Time
per-action latency
```

是否仍呈現 NoSE / Expert / Baseline 的差異。

注意：本文件紀錄的是 `iterations = 100` 的初步 medium 5x 結果。後續較穩定的主結果應優先參考：

```text
docs/rubis_medium5x_1k_iteration_result.md
```

## 2. Generator 設定

本次使用 `workspace/rubis/fake_scaled.js`，透過 Docker compose environment variables 調整資料量。

| Table | Small pilot | Medium 5x |
|---|---:|---:|
| `categories` | 500 | 500 |
| `regions` | 50 | 50 |
| `users` | 1,000 | 5,000 |
| `items` | 5,000 | 25,000 |
| `bids` | 20,000 | 100,000 |
| `comments` | 10,000 | 50,000 |
| `buynow` | 5,000 | 25,000 |

實際 row count 已於 MySQL 中確認：

```text
categories  500
regions     50
users       5000
items       25000
bids        100000
comments    50000
buynow      25000
```

## 3. Benchmark 設定

```text
mix = bidding
iterations = 100
repeat = 1
```

測試 schema：

```text
rubis_baseline
rubis_expert
rubis_nose_bidding
```

產生的 CSV：

```text
experiments/results/rubis_baseline_bidding_medium5x_100.csv
experiments/results/rubis_expert_bidding_medium5x_100.csv
experiments/results/rubis_nose_bidding_medium5x_100.csv
```

Per-action 圖表由以下腳本產生：

```text
workspace/rubis/plot_rubis_action_latency.py
```

輸出：

```text
experiments/results/rubis_medium5x_bidding_action_latency.svg
experiments/results/rubis_medium5x_bidding_action_latency_summary.csv
```

## 4. Schema-level 結果

單位：ms。

| Schema | Statements | Groups | Statement Weighted Avg | Group Weighted Avg |
|---|---:|---:|---:|---:|
| `rubis_baseline` | 41 | 16 | 25.912 | 50.757 |
| `rubis_expert` | 37 | 16 | 5.547 | 10.606 |
| `rubis_nose_bidding` | 56 | 16 | 2.212 | 5.142 |

此處主要對照論文 Fig. 18 的指標為：

```text
Group Weighted Avg
```

原因是 Fig. 18 的 weighted average response time 應以 action/request group 為單位加權，而不是把每個 statement 各自重複加權。

整體排序：

```text
NoSE-generated schema < Expert schema < Normalized/Baseline schema
```

## 5. Per-action 觀察

本次中型資料下，NoSE 仍然不是每個 action 都最低。

![RUBiS Medium 5x Bidding Per-Action Latency](../experiments/results/rubis_medium5x_bidding_action_latency.svg)

| Action group | 最低者 | Baseline ms | Expert ms | NoSE ms |
|---|---|---:|---:|---:|
| `BrowseCategories` | NoSE | 184.621 | 2.466 | 2.141 |
| `BrowseRegions` | NoSE | 37.412 | 33.241 | 1.034 |
| `SearchItemsByCategory` | NoSE | 14.923 | 15.172 | 1.256 |
| `RegisterItem` | Expert | 1.029 | 0.773 | 2.880 |
| `SearchItemsByRegion` | Baseline | 0.983 | 10.261 | 21.956 |
| `StoreBid` | Baseline | 0.937 | 1.782 | 1.520 |
| `StoreBuyNow` | Baseline | 0.999 | 2.028 | 2.186 |
| `ViewBidHistory` | Expert | 3.986 | 0.775 | 0.824 |

這表示 NoSE 在整體 workload 上仍然較佳，但某些 update/write 或特定 access pattern 會因為 denormalization 與 index maintenance 而不一定最低。不過此處只有 100 iterations，Region/SearchByRegion 類 action 不應用來宣稱 Fig. 17 趨勢已復刻。

## 6. 解讀

本次結果比小型 pilot 更有鑑別度：

```text
1. Baseline 的 BrowseCategories 明顯放大到高 latency。
2. NoSE 在 category/region/list 類 read-heavy action 上有明顯優勢。
3. RegisterItem、StoreBid、StoreBuyNow 等 update/write action 不一定由 NoSE 勝出。
4. Group weighted average 仍由 NoSE 最低，符合 workload-level optimization 的主張。
```

因此這階段可以支撐以下說法：

```text
資料量放大後，NoSE 的整體 group-weighted average response time 仍最低；
但 per-action latency 顯示 NoSE 並非逐項最低，符合 NoSQL schema design 的讀寫取捨。
```

## 7. 下一步

建議下一階段不要直接衝最大資料量，而是增加兩組：

```text
1. Medium 10x:
   users=10000, items=50000, bids=200000, comments=100000, buynow=50000

2. Update-heavy mix:
   write_medium 或 write_heavy
```

這樣可以分別觀察：

```text
資料量放大
更新比例放大
```

對 NoSE / Expert / Baseline 的影響。
