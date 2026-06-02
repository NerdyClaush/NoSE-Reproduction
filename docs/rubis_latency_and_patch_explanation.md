# RUBiS Latency and Patch Explanation

## 1. 為什麼 Figure 17 不是每個動作都是 NoSE 最低

論文中的 NoSE 不是在追求：

```text
讓每一個單獨 action 都成為最低 latency
```

而是在追求：

```text
在 storage constraint 與 workload weight 下，讓整體 workload cost 最低
```

因此 Figure 17 中某些動作，例如 `StoreComment`、`RegisterUser`、category 類查詢，不一定會是 NoSE 最低。這是合理現象，不一定代表 NoSE 失敗。

核心原因是 NoSQL schema design 有取捨：

```text
讀取最佳化通常需要 denormalization；
denormalization 會讓更新與插入需要同步更多 index/table；
所以 read-heavy action 可能變快，但 write/update action 可能變慢。
```

換句話說，NoSE 的 schema 是 workload-level optimization，不是 per-action winner selection。

## 2. 本次 RT 測的是哪一部分

目前我們的 RT 來自 RUBiS `bidding` mix 的 runtime benchmark。

輸出 CSV 欄位包含：

```text
label, group, name, weight, mean, cost
```

其中：

| 欄位 | 意義 |
|---|---|
| `label` | schema 類型，例如 `rubis_baseline`、`rubis_expert`、`rubis_nose_bidding` |
| `group` | RUBiS interaction/action 類別，例如 `StoreBid`、`RegisterUser`、`BrowseCategories` |
| `name` | 該 action 內實際執行的 query/update/insert statement |
| `weight` | workload 中該 action 的權重 |
| `mean` | 此 statement 的平均 response time |
| `cost` | NoSE cost model 估計值 |

因此我們先前的 summary：

```text
Average Response Time
Weighted Average Response Time
```

是把 CSV 中所有 statement 聚合後得到的 schema-level 結果。這比較接近論文 Fig. 17 / Fig. 18 的整體比較，但不是逐一 action 的圖。

如果要對照 Figure 17 中每個 action，就必須依照 `group` 聚合，而不是只看 schema-level average。

## 3. 本次 pilot 的 per-action 觀察

本次小規模 `bidding` pilot 中，NoSE 並非每個 action 都最低。

例子：

| Action group | 最低者 | 說明 |
|---|---|---|
| `BrowseCategories` | NoSE | NoSE 對 category list 類讀取有明顯改善 |
| `BrowseRegions` | NoSE | baseline/expert 類似 normalized lookup，NoSE 較快 |
| `RegisterUser` | NoSE | 本次 pilot 中 NoSE 較低，但論文 Figure 17 不一定如此 |
| `RegisterItem` | Expert | NoSE 需要寫入更多 generated indexes，write amplification 較高 |
| `StoreBid` | Baseline | NoSE/Expert 需維護 bid/item 相關 denormalized index |
| `StoreBuyNow` | Baseline | update 類 action 容易受到 denormalization 寫入成本影響 |
| `ViewItem` | Expert/NoSE 接近 | NoSE 不一定在每個 read action 都壓倒 expert schema |

這代表我們的 pilot 已經看見 NoSE 的典型 trade-off：

```text
整體 weighted average 較低；
但部分 write/update action 不一定最低。
```

這也正是值得向老師說明的地方：NoSE 的優勢不是每個操作都最快，而是根據 workload mix 找出整體較好的 schema。

## 4. 為什麼需要 patch script

本次復現時遇到的主要問題不是 NoSE search/advisor 無法產生 schema，而是 CLI runtime benchmark 在 update workload 上出現 parameter binding 不一致。

錯誤包含：

```text
rubis_baseline:
expecting exactly 6 bind parameters, 5 given

rubis_expert:
expecting exactly 8 bind parameters, 7 given

rubis_nose_bidding:
argument for "items_name" must be text, timestamp given
```

這些錯誤代表：

```text
schema 可以建立；
資料可以 load；
但執行 update/insert benchmark 時，prepared statement 的欄位與傳入 value 對不上。
```

因此 `workspace/scripts/patch_nose_gem.rb` 的目的不是改變 NoSE cost model，也不是讓 NoSE 變快，而是讓 runtime benchmark 能正確執行。

## 5. patch script 修了什麼

修補腳本會在 Docker image build 時 patch container 中的 RubyGem：

```text
nose-0.1.4
```

修補三處：

```text
1. rubis_baseline StoreBid/AddToBids
   補上缺少的 items.id parameter。

2. rubis_expert StoreBid/AddBid
   補上 GetUserNickname support query，
   讓 insert item_bids 時可取得 users.nickname。

3. CassandraBackend::InsertStatementStep
   讓 values 依照 prepared INSERT CQL 的 @fields 順序綁定，
   避免 items_end_date 這類 timestamp 被錯綁到 items_name。
```

## 6. 這是否可能是 CLI 故意設計

從目前錯誤型態來看，比較不像是故意設計。

理由：

```text
1. prepared statement 參數數量不足會直接導致 benchmark crash。
2. timestamp 被綁到 text 欄位會直接違反 Cassandra 型別檢查。
3. 修補後並沒有改變 NoSE search result 或 cost model，只是讓 runtime binding 對齊。
4. browsing/read-only workload 原本可跑，問題集中在 bidding/update execution path。
```

比較保守的說法應該是：

```text
NoSE advisor 的 schema search 能運作；
但 nose-cli / nose-0.1.4 在 RUBiS bidding update benchmark 上存在 runtime binding incompatibility。
本研究以最小 patch 修復執行層問題，使其能完成 pilot-scale benchmark。
```

這樣不會過度宣稱「原作者寫錯」，也不會假裝未經修補就能完整復現。

## 7. 向老師說明時可以採用的說法

可以簡短說明為：

```text
我們在復現 RUBiS bidding workload 時，發現 NoSE 的 schema search 與 Cassandra loading 可以完成，
但 CLI 在執行 update benchmark 時有 parameter binding 不一致問題。

因此我們沒有修改 NoSE 的最佳化模型，也沒有修改實驗結果計算方式；
只在 Docker build 階段加入 patch script，修正 runtime 執行層的參數對齊問題。

修補後可以取得 baseline、expert、NoSE 三種 schema 的 pilot-scale response time。
結果顯示 NoSE 在整體 weighted average 上最低，但不是每個 action 都最低；
這可用來展示 NoSQL schema design 的讀寫取捨；但目前 medium-scale 結果尚未完整對齊論文 Figure 17 的所有 per-action 趨勢。
```
