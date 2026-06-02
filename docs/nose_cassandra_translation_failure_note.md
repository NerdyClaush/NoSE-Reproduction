# NoSE to Cassandra Translation Failure Note

## 1. 問題摘要

在空氣污染資料集的 NoSE 延伸實驗中，NoSE advisor 成功為 read-only workload 產生 query plan。其中 `StationPollutantRange` 被 NoSE 表示為：

```text
StationMonthlySummary index + filter
```

也就是使用以 `Station.StationID` 為 partition key 的 index，再於查詢階段過濾 `Pollutant.PollutantID` 與月份範圍。

然而，當我們將此 query plan 直接轉換成 Cassandra CQL 時，查詢失敗。

錯誤訊息：

```text
InvalidRequest: PRIMARY KEY column "pollutant_id" cannot be restricted
(preceding column "measurement_id" is not restricted)
```

## 2. 失敗原因

原本 Cassandra table 設計近似：

```text
PRIMARY KEY ((station_id), month, measurement_id, pollutant_id)
```

這個 key order 適合：

```text
station_id + month -> all pollutant values
```

但不適合直接查：

```text
station_id + pollutant_id + month range
```

因為在 Cassandra 2.1 中，若要限制 clustering column，必須遵守 clustering key 的前綴順序。`pollutant_id` 排在 `measurement_id` 後面，因此不能在沒有先限制 `measurement_id` 的情況下直接限制 `pollutant_id`。

這代表 NoSE 的 logical query plan 不能完全機械式轉成 Cassandra CQL。

## 3. 修正方式

為了讓 `StationPollutantRange` 成為 Cassandra 合法且有效的查詢，我們新增了一張 physical adaptation table：

```text
measurements_by_station_pollutant
PRIMARY KEY ((station_id, pollutant_id), month, measurement_id)
```

這張表支援：

```text
station_id + pollutant_id + month range
```

因此可以合法執行區間查詢。

## 4. 這個轉換是否有價值？

這個轉換是有價值的，但必須清楚定位。

它不能被解釋成：

```text
NoSE 直接產生了完整可用的 Cassandra schema
```

比較合理的解釋是：

```text
NoSE 提供 workload-driven 的 schema design direction；
實際落地到 Cassandra 時，仍需根據 Cassandra 的 primary key 與 query restriction 做 physical adaptation。
```

因此，這次失敗反而揭示了 NoSE reproduction 中一個重要工程問題：

```text
logical schema recommendation != executable physical schema
```

## 5. 對資料庫解釋性的影響

空氣污染資料集本身仍然可以被解釋，因為它的 access patterns 很清楚：

| Query behavior | 實際意義 | Cassandra table |
|---|---|---|
| `PollutantTrend` | 查某污染物跨月份趨勢 | `measurements_by_pollutant` |
| `StationMonthlySummary` | 查某測站某月份所有污染物 | `measurements_by_station_month` |
| `StationPollutantRange` | 查某測站某污染物的月份區間 | `measurements_by_station_pollutant` |

這些 table 都能對應到空污監測情境，而不是任意製造出來的 schema。

因此，這個資料庫仍有解釋價值；只是它應被視為 NoSE pipeline 的延伸應用與工程落地測試，而不是原論文 RUBiS evaluation 的直接替代品。

## 6. 結論

本次失敗是有研究價值的。

它說明：

- NoSE 可以幫助我們從 workload 推導 schema 方向。
- Cassandra 的實際 CQL 查詢限制會影響 schema 是否可執行。
- 從 NoSE advisor output 到 Cassandra implementation 之間需要一層人工或自動化 translation/adaptation。
- 空污資料集可以作為延伸展示，但要明確說明其 schema 是經過 Cassandra physical adaptation 後完成。

後續若要復刻論文等級實驗，應把這一層 translation/adaptation 明確納入 pipeline，而不是假設 NoSE output 能直接執行。
