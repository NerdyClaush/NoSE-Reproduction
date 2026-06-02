# Air Pollution NoSE Read-Only Summary

這份文件是 `air_pollution_read_only.txt` 的報告友善版。原始檔保留 NoSE CLI 的完整輸出；本檔改用較穩定的文字格式，避免 Windows 顯示 box drawing / arrow 符號時出現亂碼。

## 1. Index 對照表

NoSE 原始輸出中的 `i1771458373`、`i3444539955` 是執行時由 NoSE 自動生成的 index identifier。它們不是資料集本身的 ID，也不是論文需要固定引用的名稱。

報告中可改用以下別名：

| 報告別名 | NoSE 原始 ID | 用途 | Size |
|---|---|---|---:|
| `I1` | `i1771458373` | 依污染物查月份趨勢 | 5390 |
| `I2` | `i3444539955` | 依測站與月份查污染物資料 | 4620 |

## 2. Index 結構

### I1: Pollutant trend index

```text
Partition key:
  Pollutant.PollutantID

Clustering / ordering fields:
  MonthlyMeasurement.Month
  MonthlyMeasurement.MeasurementID

Projected fields:
  MonthlyMeasurement.AverageValue
  MonthlyMeasurement.Note
```

### I2: Station-month summary index

```text
Partition key:
  Station.StationID

Clustering / ordering fields:
  MonthlyMeasurement.Month
  MonthlyMeasurement.MeasurementID
  Pollutant.PollutantID

Projected fields:
  MonthlyMeasurement.AverageValue
  Pollutant.PollutantName
  Pollutant.Unit
```

## 3. Query Plan 對照

| Workload group | 權重 | 查詢情境 | 使用 index |
|---|---:|---|---|
| `PollutantTrend` | 40 | 查某污染物的月份趨勢 | `I1` |
| `StationMonthlySummary` | 30 | 查某測站某月份所有測項 | `I2` |
| `StationPollutantRange` | 20 | 查某測站某污染物的月份區間 | `I2` 後再 filter |

## 4. 圖表

圖檔位置：

```text
experiments/results/air_pollution_nose_summary.png
```

這張圖把 index size、workload weight、query plan mapping 分開呈現，適合放進報告或簡報。

## 5. 解讀注意事項

這次執行使用：

```text
--read-only
```

因此 NoSE 只分析 read workload，`InsertMonthlyMeasurement` 不會出現在 query plan 中。

另外，這份測試的重點是驗證：

```text
CSV domain -> conceptual model -> NoSE workload -> NoSQL schema suggestion
```

它還不是 Cassandra 實際匯入資料後的查詢 benchmark。
