# NoSE 論文複現路線圖

本文整理自：

- `C:\Users\Rachel\Downloads\evaluate_report(1).md`
- `C:\Users\Rachel\Downloads\NoSE_Schema_Design_for_NoSQL_Applications.pdf`
- 官方 GitHub：`https://github.com/michaelmior/NoSE`
- 官方 CLI：`https://github.com/michaelmior/nose-cli`

## 0. 目前最重要的結論

這篇論文不是完全需要從零重刻。官方已經公開主要實作：

- `michaelmior/NoSE`：核心 Ruby library，包含 model/workload DSL、candidate enumeration、query planning、BIP 建構、update support、RUBiS/EAC workload 等。
- `michaelmior/nose-cli`：命令列工具，用來執行 `nose search`、benchmark 等流程。
- `michaelmior/nose` Docker image：可快速取得含相依套件的環境。

所以本專案的合理策略是：

1. 先復現官方 repo 能直接跑出的 advisor 結果。
2. 再檢查論文中哪些 evaluation 需要 Cassandra、舊版環境、資料填充或缺漏腳本。
3. 最後才決定哪些部分需要自行補實作。

## 1. 論文結構

| 區塊 | 內容 | 複現重點 |
|---|---|---|
| Section 1 | 問題動機 | NoSQL schema design 需要依 workload 設計 |
| Section 2 | Hotel booking 範例 | 用來解釋 column family 設計問題 |
| Section 3 | Application model | Conceptual model、workload、column family 表示 |
| Section 4 | Schema advisor | Candidate enumeration、query planning、schema optimization、plan recommendation |
| Section 5 | BIP optimization | 以 Binary Integer Program 選 schema 與 query plans |
| Section 6 | Cost model | `T(n, w)` 成本模型與 Cassandra calibration |
| Section 7 | Updates | support query、UpdateEnumerate、update cost |
| Section 8 | EAC case study | 以 EasyAntiCheat workload 做定性驗證 |
| Section 9 | Evaluation | RUBiS schema quality、write intensity、advisor runtime |

## 2. 可用 GitHub / 外部資源

| 資源 | 用途 | 判斷 |
|---|---|---|
| `https://github.com/michaelmior/NoSE` | 官方核心 library | 必用 |
| `https://github.com/michaelmior/nose-cli` | 官方 CLI | 跑完整流程時必用 |
| `michaelmior/nose` Docker image | 快速環境 | 推薦優先嘗試 |

## 3. 哪些可以直接復現

- Conceptual model / workload DSL。
- Column family 表示。
- Algorithm 1 / Algorithm 2。
- Candidate combination。
- Query planning。
- BIP 建構與求解流程。
- Update support：Algorithm 3 / Algorithm 4。
- EAC case study 的 schema recommendation。
- RUBiS workload、baseline/expert schema、部分 experiment scaffold。

## 4. 哪些只能部分復現

- EAC 完整執行：需要 `nose-cli`。
- RUBiS schema quality experiment：需要 Cassandra、資料填充、benchmark driver。
- Write intensity experiment：需要對不同 workload mix 重跑 advisor。
- Advisor runtime experiment：repo 有 random workload 元件，但 scale-factor driver 需要確認或補寫。

## 5. 高風險 / 可能無法精準復現

| 項目 | 問題 | 建議處理 |
|---|---|---|
| Cassandra 2.0.9 | 很舊，現代 Java / driver / Docker 相容性可能卡住 | 優先用 Docker 或舊環境；若失敗，標註為 approximate reproduction |
| Gurobi | 論文使用 Gurobi；官方開源流程使用 CBC | 先接受 CBC，之後再比較是否需要 Gurobi academic license |
| Cost calibration | Section 6.1 的 synthetic DB + linear regression 腳本未完整公開 | 可能需要自行補校準工具 |
| RUBiS latency 數字 | 硬體、磁碟、Cassandra caching、JVM 都會影響 | 先追趨勢與相對比較，不追逐精準 ms |
| Hotel booking Fig. 1 | 官方 repo 沒有此 toy model | 可自行依論文補成 model/workload |

## 6. 建議執行順序

1. 跑通 `nose-cli` 的 help / list / search。
2. 跑 EAC workload，對照論文 Fig. 16。
3. 跑 RUBiS advisor output，對照 schema / plans。
4. 設定 Cassandra，再做 RUBiS latency benchmark。
5. 補 cost calibration、Hotel booking model、advisor runtime scale driver。

