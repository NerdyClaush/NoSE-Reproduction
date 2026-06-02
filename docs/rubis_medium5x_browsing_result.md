# RUBiS Medium 5x Browsing Result

## 1. 目的

本次補跑 RUBiS `browsing` mix，用來和 `bidding` mix 分開比較。

Browsing 屬於 read-heavy workload，因此理論上更容易展現 NoSE denormalized schema 的讀取優勢。

## 2. Dataset

沿用 medium 5x RUBiS generator 資料：

| Table | Rows |
|---|---:|
| `categories` | 500 |
| `regions` | 50 |
| `users` | 5,000 |
| `items` | 25,000 |
| `bids` | 100,000 |
| `comments` | 50,000 |
| `buynow` | 25,000 |

## 3. Benchmark 設定

```text
mix = browsing
iterations = 100
repeat = 1
```

測試 schema：

```text
rubis_baseline
rubis_expert
rubis_nose_browsing
```

產生的 CSV：

```text
experiments/results/rubis_baseline_browsing_medium5x_100.csv
experiments/results/rubis_expert_browsing_medium5x_100.csv
experiments/results/rubis_nose_browsing_medium5x_100.csv
```

注意：本文件不再將 browsing per-action chart 作為 Fig. 17-style 對照。Browsing 結果主要用於 Fig. 18-style overall weighted average。

## 4. Schema-level 結果

單位：ms。

| Schema | Statements | Groups | Statement Weighted Avg | Group Weighted Avg |
|---|---:|---:|---:|---:|
| `rubis_baseline` | 11 | 7 | 19.353 | 28.362 |
| `rubis_expert` | 12 | 7 | 6.816 | 10.755 |
| `rubis_nose_browsing` | 11 | 7 | 0.919 | 1.346 |

主要對照 Fig. 18 / weighted average response time 時，應使用：

```text
Group Weighted Avg
```

## 5. 解讀

Browsing 的結果比 bidding 更明顯：

```text
Baseline 28.362 ms
Expert   10.755 ms
NoSE      1.346 ms
```

這符合預期，因為 browsing 幾乎是 read-heavy workload；NoSE 可以透過 denormalization 將常見查詢轉成較直接的 lookup，降低 read latency。

與 bidding 不同的是，browsing 中沒有大量 write/update action，因此較少出現 write amplification 導致 NoSE 輸給 baseline/expert 的情況。

## 6. 注意事項

本結果仍屬 medium-scale reproduction，不是 paper-scale reproduction。

不可直接宣稱逐數字重現論文 Fig. 18，原因包括：

```text
1. 資料量尚未達論文設定。
2. Cassandra cache / hardware / seed / request trace 不完全一致。
3. NoSE-generated schema 使用現有 browsing JSON，尚未針對更大資料量重新 search。
```
