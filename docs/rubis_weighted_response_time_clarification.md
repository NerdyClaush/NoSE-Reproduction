# RUBiS Weighted Response Time Clarification

## 1. 混淆來源

先前看到的數字其實來自不同層級：

| 數字來源 | 意義 |
|---|---|
| 論文 Fig. 17 / Fig. 18 的 87ms、41ms、8ms | paper-scale RUBiS experiment 的 weighted overall average |
| 先前腳本輸出的 12ms、25ms 等 | statement-level average / statement-level weighted average |
| 修正後主要採用的數字 | action/group-level weighted average |

因此：

```text
12ms 不是 Fig. 18 對應數字。
```

它是把 CSV 中每一個 statement 當成獨立項目平均後得到的結果，資訊層級比較低。

## 2. Fig. 18 應該看哪個指標

NoSE CLI 原本的 `analyze` 邏輯是：

```text
1. 先依 group/action 聚合。
2. 將同一個 action 底下的多個 statement mean 加總。
3. 若要 total，使用 action 的 workload weight 做加權平均。
```

因此後續對照 Fig. 18 時，主要採用：

```text
group_weighted_average_response_time
```

而不是：

```text
statement_weighted_average_response_time
```

## 3. Medium 5x Bidding 結果

單位：ms。

| Schema | Statement Weighted Avg | Group Weighted Avg |
|---|---:|---:|
| Baseline | 25.912 | 50.757 |
| Expert | 5.547 | 10.606 |
| NoSE | 2.212 | 5.142 |

若要對照 Fig. 18，應看右欄：

```text
Baseline 50.757 ms
Expert   10.606 ms
NoSE      5.142 ms
```

這和論文中的：

```text
Normalized 87.0 ms
Expert     41.6 ms
NoSE        8.4 ms
```

方向一致，但數值仍不能直接逐項相等，因為資料量、Cassandra 設定、cache、硬體、seed 與 request trace 都不同。

## 4. Medium 5x Browsing 結果

單位：ms。

| Schema | Statement Weighted Avg | Group Weighted Avg |
|---|---:|---:|
| Baseline | 19.353 | 28.362 |
| Expert | 6.816 | 10.755 |
| NoSE | 0.919 | 1.346 |

Browsing 是 read-heavy workload，因此 NoSE 的 denormalized schema 優勢更明顯。

## 5. 後續報告原則

後續文件與圖表採用以下規則：

```text
1. Fig. 18 / overall weighted average:
   使用 group_weighted_average_response_time。

2. Per-action figure:
   使用 group/action 聚合後的 response time。

3. Statement-level average:
   僅作為 debugging 或補充資訊，不作為主要論文對照。
```

這樣可以避免把「statement 平均」誤認為「workload weighted average」。

## 6. Figure 17 / Figure 18 命名規則

Figure 17 是 per-action response time 圖，因此圖表上的 action label 應與論文圖一致。

目前 `plot_rubis_action_latency.py` 會將 NoSE/RUBiS 原始 group name 轉成以下 Figure 17 label：

| 原始 group | Figure 17 label |
|---|---|
| `StoreComment` | `StoreComment` |
| `PutComment` | `PutComment` |
| `RegisterItem` | `RegisterItem` |
| `RegisterUser` | `RegisterUser` |
| `StoreBuyNow` | `StoreBuyNow` |
| `BuyNow` | `BuyNow` |
| `ViewBidHistory` | `BidHistory` |
| `AboutMe` | `AboutMe` |
| `StoreBid` | `StoredBid` |
| `ViewUserInfo` | `UserInfo` |
| `BrowseRegions` | `Regions` |
| `SearchItemsByRegion` | `SearchByRegion` |
| `BrowseCategories` | `Categories` |
| `ViewItem` | `ViewItem` |
| `SearchItemsByCategory` | `SearchByCategory` |

Figure 18 則不是 per-action 圖，不應拆成上述 action。它只比較：

```text
Browsing / Bidding workload
NoSE / Normalized Baseline / Expert
```

因此 Figure 18-style 圖由以下檔案產生：

```text
workspace/rubis/plot_rubis_overall_weighted.py
experiments/results/rubis_medium5x_overall_weighted_response_time.svg
```
