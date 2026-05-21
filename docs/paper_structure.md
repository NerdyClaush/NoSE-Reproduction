# NoSE 論文結構導讀

論文：*NoSE: Schema Design for NoSQL Applications*

這份文件的目的不是翻譯全文，而是建立複現時需要的「閱讀地圖」。後續所有實作、Docker、實驗、報告圖，都可以回頭對照這份結構。

## 1. 整體主線

NoSE 的論文結構可以理解成三層：

```text
問題定義層：為什麼 NoSQL schema design 難？
方法層：NoSE 如何把 schema design 轉成 optimization problem？
評估層：NoSE 產生的 schema 是否比人工 baseline 好？
```

對應到論文章節：

| 層次 | 章節 | 角色 |
|---|---|---|
| 問題定義 | Section 1-3 | 定義 NoSQL schema design 問題、輸入資料與表示法 |
| 方法核心 | Section 4-7 | NoSE advisor pipeline、BIP、cost model、updates |
| 案例與評估 | Section 8-9 | EAC case study、RUBiS benchmark、runtime scalability |
| 收尾 | Section 10-11 | 相關研究與結論 |

## 2. Section-by-Section

### Section 1: Introduction

核心問題：

- NoSQL extensible record stores 雖然 schema flexible，但仍然需要設計 column families。
- Schema 會大幅影響 query performance。
- 關聯式資料庫的 physical design advisor 不能直接套用到 NoSQL。

複現意義：

- 這一節主要是動機，不需要實作。
- 報告中可用來說明「為什麼需要 NoSE」。

### Section 2: Background / Running Example

核心內容：

- 使用 hotel booking system 當 running example。
- 介紹 Cassandra-like column family 設計直覺。
- 展示不同 schema 如何影響查詢成本。

複現意義：

- 可做成 toy example，但不是官方 repo 已經完整提供的主實驗。
- 若老師要求從簡單例子說明 NoSE，這節適合拿來畫簡化圖。

目前狀態：

- 官方 repo 有 EAC、RUBiS、eBay model。
- 尚未確認有 hotel booking model；目前視為需要自行補的教學範例。

### Section 3: Application Model

這是 NoSE 的輸入定義。

包含三個元素：

| 元素 | 說明 | 複現重點 |
|---|---|---|
| Conceptual Model | entity graph、entity attributes、relationships | 需理解 model DSL |
| Workload | queries / updates / frequencies | 需理解 workload DSL |
| Column Family | `K -> C -> V` triple | 後續 enumeration 與 BIP 都依賴這個表示 |

複現意義：

- 這節是所有實作的地基。
- 若這節沒讀清楚，後面 Algorithm 1/2 會很難理解。

官方程式碼對應：

- `upstream/NoSE/models/`
- `upstream/NoSE/workloads/`
- `upstream/NoSE/lib/nose/model.rb`
- `upstream/NoSE/lib/nose/workload.rb`
- `upstream/NoSE/lib/nose/indexes.rb`

### Section 4: Schema Advisor

這是論文方法的主體。

包含四步驟：

1. Candidate Enumeration
2. Query Planning
3. Schema Optimization
4. Plan Recommendation

複現意義：

- 這是最重要的章節。
- 後續 pipeline 圖主要來自這一節。

子重點：

| 小節 | 內容 | 重要性 |
|---|---|---|
| 4.1.1 | Algorithm 1 Materialize | 必讀 |
| 4.1.2 | Algorithm 2 Enumerate | 必讀 |
| 4.1.3 | Candidate Combination | 必讀 |
| 4.2 | Query Planning | 必讀，但比 enumeration 稍晚實作 |

官方程式碼對應：

- `upstream/NoSE/lib/nose/enumerator.rb`
- `upstream/NoSE/lib/nose/indexes.rb`
- `upstream/NoSE/lib/nose/plans/`

### Section 5: Schema Optimization

核心內容：

- 把 schema selection 轉成 Binary Integer Program。
- 變數包含：
  - 是否選某個 column family。
  - 某條 query 是否使用某個 plan / index。
- 約束包含：
  - query plan 必須完整。
  - 使用的 index 必須被選進 schema。
  - storage size 不可超過限制。

複現意義：

- 這是 NoSE 和一般 heuristic schema design 最大差異。
- 論文使用 Gurobi；開源流程使用 CBC。

官方程式碼對應：

- `upstream/NoSE/lib/nose/search/problem.rb`
- `upstream/NoSE/lib/nose/search/constraints.rb`

風險：

- Solver 不同會造成結果或 runtime 不完全一致。
- 若完整 EAC / RUBiS 解太久，需要分析 candidate 數量與 ILP 大小。

### Section 6: Cost Model

核心內容：

- NoSE 用 cost model 估計 query plan 的成本。
- 論文對 Cassandra 建立 `T(n, w)` 類型的成本模型。
- 成本模型需要 calibration。

複現意義：

- 若只複現 advisor output，可先使用 repo 內建 cost model。
- 若要複現 latency / 論文數字，這節很關鍵。

風險：

- Calibration 腳本未必完整公開。
- 現代硬體與 Cassandra 版本會讓數字和論文不同。

官方程式碼對應：

- `upstream/NoSE/lib/nose/cost/`

### Section 7: Updates

核心內容：

- Updates 會讓 denormalized schema 的維護成本變高。
- NoSE 需要產生 support queries 取得 update 所需但 statement 沒提供的資料。
- 擴充 candidate enumeration 與 BIP objective。

重要演算法：

- Algorithm 3: Support Query Generation
- Algorithm 4: UpdateEnumerate

複現意義：

- 這是 NoSE 比單純 read-optimized schema advisor 更完整的地方。
- 目前我們已跑通 EAC read-only，但完整 EAC 含 updates 曾超過 5 分鐘未完成，因此這節會是下一個技術風險點。

官方程式碼對應：

- `upstream/NoSE/lib/nose/statements/update.rb`
- `upstream/NoSE/lib/nose/enumerator.rb`
- `upstream/NoSE/lib/nose/search/problem.rb`

### Section 8: Case Study - EasyAntiCheat

核心內容：

- 用 EAC workload 展示 NoSE 對實際應用 schema design 的建議。
- 論文重點是定性分析，不是大規模 latency benchmark。

複現意義：

- 這是最適合當第一個完整案例的章節。
- 比 RUBiS benchmark 輕，較容易先跑出 schema / plans。

目前狀態：

- 已成功跑通 EAC read-only。
- 結果存於 `experiments/results/eac_read_only.txt`。
- 完整含 updates 的版本尚待分析。

### Section 9: Evaluation

分成兩大實驗：

| 小節 | 實驗 | 目的 |
|---|---|---|
| 9.1 | Schema Quality | 比較 NoSE / Normalized / Expert schema 的 response time |
| 9.2 | Advisor Runtime | 測試 advisor 在更大 workload 上的 runtime scalability |

Schema Quality 使用 RUBiS 改編版：

- Cassandra 2.0.9。
- 200,000 users。
- 關閉 Cassandra-level caching。
- 比較 16 種 request type。

重要釐清：

- 論文本身描述的是將 RUBiS 原始 SQL statements 轉換成 NoSE workload。
- 論文 PDF 中沒有將 MySQL 描述為方法或實驗架構的一部分。
- MySQL 是官方開源 repo 的 RUBiS experiment README 中採用的工程實作細節，用來作為 source/staging database，讓 NoSE loader 將資料載入 Cassandra column families。
- 因此報告時應說：「論文以 Cassandra 作為 target backend；我們使用 MySQL 是為了重現官方 repo 的資料載入流程，而不是因為 NoSE 方法依賴 MySQL。」

複現意義：

- 這是最像「完整實驗復現」的章節。
- 但也是最容易卡環境與時間的章節。

風險：

- Cassandra 2.0.9 舊環境。
- 原硬體不可重現。
- RUBiS data generation / benchmark driver 需要額外整理。
- 論文 latency 數字不宜作為精準目標，應先追趨勢。

### Section 10: Related Work

核心內容：

- 關聯式資料庫 physical design advisor。
- NoSQL schema design。
- Workload-aware storage design。

複現意義：

- 不需實作。
- 報告中可用來說明 NoSE 的定位。

### Section 11: Conclusion

核心內容：

- NoSE 自動化 NoSQL schema design。
- 以 workload + cost model + BIP solver 選 schema。
- 實驗顯示可優於 normalized / expert baselines。

複現意義：

- 可作為報告結論的框架。

## 3. 複現優先順序

目前建議順序：

| 優先 | 目標 | 對應章節 |
|---|---|---|
| P0 | 跑通 Docker advisor 環境 | 工程環境 |
| P1 | 理解 Section 3 application model | Section 3 |
| P1 | 跑 EAC read-only / 對照 query plans | Section 8 |
| P1 | 梳理 Algorithm 1/2 與程式碼 | Section 4 |
| P2 | 分析完整 EAC updates 卡住原因 | Section 7 / 8 |
| P2 | 跑 RUBiS advisor output | Section 9.1 |
| P3 | Cassandra latency benchmark | Section 9.1 |
| P3 | Advisor runtime scaling | Section 9.2 |
| P4 | 補 cost calibration | Section 6 |

## 4. 報告呈現建議

若要向老師說明，建議不要照論文順序逐節念，而是改成：

1. NoSE 解決什麼問題？
2. NoSE 的輸入是什麼？
3. NoSE pipeline 怎麼運作？
4. NoSE 如何用 BIP 選 schema？
5. 我們目前複現到哪裡？
6. 哪些部分因環境或資料缺漏難以精準複現？

這樣會比直接從 Section 1 講到 Section 11 更清楚。
