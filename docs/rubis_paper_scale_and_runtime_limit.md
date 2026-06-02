# RUBiS Paper Scale and Runtime Limit

## 1. 論文/官方實驗的資料規模

官方 NoSE RUBiS experiment 的 `fake.js` 使用以下資料量：

| Table | Paper-scale count |
|---|---:|
| `categories` | 500 |
| `regions` | 50 |
| `users` | 200,000 |
| `items` | 2,000,000 |
| `bids` | 20,000,000 |
| `comments` | 10,000,000 |
| `buynow` | 2,000,000 |

來源：

```text
upstream/NoSE/experiments/rubis/fake.js
upstream/nose-cli/experiments/rubis/fake.js
```

## 2. 目前 medium 5x 的資料規模

目前我們已跑完的 medium 5x dataset：

| Table | Medium 5x count | Paper-scale count | Ratio |
|---|---:|---:|---:|
| `categories` | 500 | 500 | 100% |
| `regions` | 50 | 50 | 100% |
| `users` | 5,000 | 200,000 | 2.5% |
| `items` | 25,000 | 2,000,000 | 1.25% |
| `bids` | 100,000 | 20,000,000 | 0.5% |
| `comments` | 50,000 | 10,000,000 | 0.5% |
| `buynow` | 25,000 | 2,000,000 | 1.25% |

這表示目前的 medium 5x 對 bids/comments 只到 paper-scale 的約 0.5%。

## 3. 為什麼 paper-scale 目前不適合直接跑

目前測得的 runtime 訊號：

```text
medium 5x / baseline browsing / 1k iterations:
約 7.5 分鐘完成。

medium 5x / baseline browsing / 10k iterations:
超過 15 分鐘仍未完成，CSV 為 0 bytes。
```

在 paper-scale 下，資料量不是增加 5 倍或 10 倍，而是對主要表增加到：

```text
items:    80x medium 5x
bids:    200x medium 5x
comments: 200x medium 5x
```

因此直接跑完整 paper-scale 很可能不適合目前的 Docker/Desktop 環境。

## 4. 對 Fig. 17 的影響

Fig. 17 是 per-action latency 圖，對資料分布、partition size、cache、range scan 與 request sampling 都很敏感。

目前 Region / SearchByRegion 類 action 趨勢仍與論文不完全一致，因此不應宣稱已復刻 Fig. 17。

較保守的說法是：

```text
目前已能重建 Fig. 17-style 的 bidding per-action benchmark pipeline；
但 medium 5x dataset 尚不足以重現所有 action 的 paper trend。
```

## 5. 後續建議

不建議直接跳到 paper-scale。

建議採用階段式資料量：

| Stage | users | items | bids | comments | buynow |
|---|---:|---:|---:|---:|---:|
| Medium 5x | 5,000 | 25,000 | 100,000 | 50,000 | 25,000 |
| Medium 10x | 10,000 | 50,000 | 200,000 | 100,000 | 50,000 |
| Large 25x | 25,000 | 125,000 | 500,000 | 250,000 | 125,000 |
| Large 50x | 50,000 | 250,000 | 1,000,000 | 500,000 | 250,000 |
| Paper-scale | 200,000 | 2,000,000 | 20,000,000 | 10,000,000 | 2,000,000 |

每個 stage 先跑：

```text
bidding
iterations = 1000
baseline / expert / NoSE
Fig. 18-style overall weighted average
Fig. 17-style bidding per-action chart
```

若 Large 25x 或 Large 50x 開始超時，就以該點作為本機可承受上限，並在報告中說明 paper-scale 受限於硬體與 Docker runtime。
