# RUBiS Response Time Pilot Result

## 1. 實驗目標

本階段先針對 RUBiS 小規模資料集測試：

```text
Average Response Time
Weighted Average Response Time
```

目標不是逐數字重現 Fig. 17 / Fig. 18，而是先確認：

```text
RUBiS source data
-> MySQL staging
-> NoSE loader
-> Cassandra schema
-> nose execute / benchmark
-> response-time summary
```

這條 pipeline 可以完整執行。

## 2. 實驗設定

本次使用 Docker compose 預設的小規模 RUBiS data：

| Table | Rows |
|---|---:|
| `categories` | 500 |
| `regions` | 50 |
| `users` | 1,000 |
| `items` | 5,000 |
| `bids` | 20,000 |
| `comments` | 10,000 |
| `buynow` | 5,000 |

執行設定：

```text
mix = browsing
iterations = 100
repeat = 1
```

測試 schema：

| Label | 說明 |
|---|---|
| `rubis_baseline` | Normalized / baseline manually-defined schema |
| `rubis_expert` | Expert manually-defined schema |
| `rubis_nose_browsing` | NoSE 針對 browsing mix 自動產生的 schema |

## 3. Summary

單位：ms。

| Schema | Statements | Average Response Time | Weighted Average Response Time |
|---|---:|---:|---:|
| `rubis_baseline` | 11 | 33.949 | 16.456 |
| `rubis_expert` | 12 | 4.782 | 3.088 |
| `rubis_nose_browsing` | 11 | 0.938 | 0.789 |

## 4. 與論文 Fig. 17 的關係

論文 Fig. 17 文字說明中給出的 weighted overall average response time 為：

| Schema | Weighted overall average |
|---|---:|
| NoSE | 8.4 ms |
| Normalized | 87.0 ms |
| Expert | 41.6 ms |

本次結果不能直接與論文數字逐項比較，原因包括：

- 本次資料量遠小於論文設定。論文使用 200,000 users，官方 `fake.js` 對應更大資料規模。
- 本次先跑 `browsing` mix；論文 Fig. 17 的主要 schema quality 實驗依 RUBiS bidding workload 權重建立。
- 本機 Docker/Cassandra 版本與論文環境不同。
- 論文關閉 Cassandra-level caching；目前 Docker smoke/pilot 尚未完整重現此設定。
- 論文未提供原始資料快照、固定 seed 與完整 request trace。

因此目前應解讀為：

```text
pilot-scale pipeline validation
```

而非：

```text
paper-scale latency reproduction
```

## 5. 初步觀察

相對排序符合論文主張：

```text
NoSE-generated schema < Expert schema < Normalized/Baseline schema
```

其中 `rubis_baseline` 的 `BrowseCategories/Categories` request 明顯偏慢，原因是 baseline schema 對 category list 類型查詢較不友善；`rubis_nose_browsing` 則針對 browsing mix 建立了高度 read-optimized 的 denormalized schema。

這與論文對 browsing mix 的敘述一致：

```text
NoSE 在 read-heavy / browsing workload 上可以大量 denormalize，
因此 response time 會明顯降低。
```

## 6. 下一步

為了更接近 Fig. 17 / Fig. 18，需要繼續做：

```text
1. 跑 bidding mix，而不只 browsing mix。
2. 跑 write_heavy 或 10x / 100x update-frequency mix。
3. 將資料量放大到更接近官方 fake.js / 論文規模。
4. 比較 NoSE / Expert / Normalized 的 weighted average。
5. 明確記錄無法逐數字復刻的原因。
```

## 7. Bidding mix 目前狀態

已嘗試執行小規模 `bidding` mix：

```text
rubis_baseline
rubis_expert
rubis_nose_bidding
```

結果：三者都在 update execution 階段失敗，尚未產生可計算 average / weighted average 的 CSV。

詳細紀錄：

```text
docs/rubis_bidding_update_failure_note.md
```

因此目前的可靠 response-time 數字僅限於 `browsing` pilot。下一步應先修復或定位 bidding update pipeline，而不是直接放大 RUBiS dataset。
