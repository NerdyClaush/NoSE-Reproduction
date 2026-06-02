# RUBiS Medium 5x 1k Iteration Result

## 1. 目的

本次原本嘗試將 medium 5x benchmark 提高到：

```text
iterations = 10000
```

但第一個 baseline browsing run 超過 15 分鐘仍未完成，且輸出 CSV 為 0 bytes。

因此改採 NoSE 原始 `run-experiments.sh` 中的預設：

```text
iterations = 1000
```

此設定比先前 100 iterations 更穩定，也更接近原工具的實驗流程。

## 2. Dataset

沿用 medium 5x RUBiS dataset：

| Table | Rows |
|---|---:|
| `users` | 5,000 |
| `items` | 25,000 |
| `bids` | 100,000 |
| `comments` | 50,000 |
| `buynow` | 25,000 |

## 3. Fig. 18-style Overall Result

單位：ms，採用 group-weighted average response time。

| Workload | NoSE | Normalized Baseline | Expert |
|---|---:|---:|---:|
| Browsing | 1.395 | 29.391 | 11.039 |
| Bidding | 2.629 | 46.116 | 10.631 |

圖表：

![RUBiS Medium 5x Overall Weighted Response Time 1k](../experiments/results/rubis_medium5x_overall_weighted_response_time_1kiter.svg)

## 4. Fig. 17-style Per-action Result

Bidding action 圖：

![RUBiS Medium 5x Bidding Action Latency 1k](../experiments/results/rubis_medium5x_bidding_action_latency_1kiter.svg)

注意：本文件不再將 browsing action 圖作為 Fig. 17-style 對照。Fig. 17 的 action 趨勢應主要參考 bidding workload；browsing 只保留作為 Fig. 18-style overall workload 對照。

## 5. 觀察

1k iterations 後，趨勢比 100 iterations 更穩定。

特別是 bidding 的 per-action 結果中：

| Action | Baseline ms | Expert ms | NoSE ms | Lowest |
|---|---:|---:|---:|---|
| `SearchByRegion` | 1.016 | 10.644 | 0.760 | NoSE |
| `RegisterItem` | 0.879 | 0.734 | 0.827 | Expert |
| `StoreBuyNow` | 0.966 | 2.367 | 2.025 | Baseline |
| `StoredBid` | 0.822 | 1.871 | 1.346 | Baseline |
| `Categories` | 167.456 | 2.381 | 1.828 | NoSE |

這表示先前 100 iterations 中某些 action 的趨勢可能受到抽樣噪音影響；提高到 1k 後，部分 action 變得較穩定。但 Region/SearchByRegion 類趨勢仍與論文 Fig. 17 不完全一致，因此目前不應宣稱已成功復刻 Fig. 17。

## 6. 結論

目前可採用的穩定版本是：

```text
medium 5x
iterations = 1000
```

10k iterations 在目前機器與 baseline schema 下成本過高，不建議作為常規實驗設定。

後續若要更接近 paper-scale，較合理的路線是：

```text
1. 先保存 medium 5x / 1k results。
2. 再嘗試 medium 10x / 1k。
3. 若需要才針對單一 schema 或單一 workload 跑 10k。
```
