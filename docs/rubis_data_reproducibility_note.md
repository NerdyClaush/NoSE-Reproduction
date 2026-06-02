# RUBiS Data Reproducibility Note

## 1. 核心判斷

NoSE 論文的主實驗使用 RUBiS benchmark 作為購物網站 workload。RUBiS 不是空污資料這種自行設計的 synthetic domain，而是既有的 auction / shopping website benchmark。

目前可確認：

```text
官方 repo 有 RUBiS model、workload、baseline/expert schema、資料產生腳本與實驗流程。
```

但目前看不到：

```text
論文當年實際使用的資料快照
固定 random seed
完整 request trace
完整 Cassandra snapshot
原硬體與環境狀態
```

因此，RUBiS evaluation 可以做「流程復刻」與「趨勢復刻」，但很難保證逐項 latency 數字與論文完全一致。

## 2. 官方 repo 中公開的 RUBiS 材料

相關檔案：

```text
upstream/NoSE/models/rubis.rb
upstream/NoSE/workloads/rubis.rb
upstream/NoSE/schemas/rubis_baseline.rb
upstream/NoSE/schemas/rubis_expert.rb
upstream/NoSE/plans/rubis_baseline.rb
upstream/NoSE/plans/rubis_expert.rb
upstream/nose-cli/experiments/rubis/fake.js
upstream/nose-cli/experiments/rubis/rubis-schema.sql
upstream/nose-cli/experiments/rubis/rubis-update.sql
upstream/nose-cli/experiments/rubis/README.md
```

`fake.js` 使用 `mysql-faker` 產生資料，規模如下：

| Table | Rows |
|---|---:|
| `categories` | 500 |
| `regions` | 50 |
| `users` | 200,000 |
| `items` | 2,000,000 |
| `bids` | 20,000,000 |
| `comments` | 10,000,000 |
| `buynow` | 2,000,000 |

這些規模和論文中提到的 RUBiS 大型購物網站 workload 方向一致。

## 3. 主要復刻困難

### 3.1 資料不是固定快照

`fake.js` 是資料產生器，不是論文實驗使用的資料 dump。

因此即使使用相同 row counts，也可能因為亂數資料不同而造成：

- item / bid / comment 分布不同。
- user / region / category 熱點不同。
- Cassandra partition size 不同。
- query latency 不同。

### 3.2 缺少固定 seed

目前 `fake.js` 沒有明確固定 random seed。這代表每次生成資料都可能不同。

若要提高可重現性，後續應考慮：

```text
固定 seed
保存 generated dataset manifest
保存 MySQL dump 或 Cassandra snapshot
```

### 3.3 缺少完整 request trace

論文比較的是不同 request type 的 response time。repo 有 workload definition，但若沒有論文當年的完整 request trace，就很難保證每次 benchmark 的 request sequence、參數分布與 hot keys 完全相同。

### 3.4 原環境不可完全重建

論文環境包含舊版 Cassandra、硬體、cache 設定與成本模型校準。即使資料能重建，現代 Docker/Windows/不同硬體也會改變 latency。

## 4. 可以復刻到什麼程度？

可較有把握復刻：

```text
RUBiS model/workload
NoSE advisor output
baseline/expert schema 建立流程
MySQL -> Cassandra loader 流程
不同 schema 的相對趨勢
資料量放大後的 scaling behavior
```

較難精準復刻：

```text
論文中每個 request type 的 exact response time
論文圖表的 exact numeric values
當年 Cassandra cache/compaction/JVM 狀態
當年 generated data 的 exact distribution
```

## 5. 建議報告措辭

建議使用：

```text
本研究依官方 NoSE repository 提供的 RUBiS model、workload、schema 與 fake.js 資料產生流程，重建 RUBiS evaluation pipeline。
由於論文未提供原始資料快照、固定 seed 與完整 request trace，本實驗目標為復刻流程與觀察相對趨勢，而非逐數字重現論文 latency。
```

避免使用：

```text
完全重現論文 RUBiS 實驗結果。
```

## 6. 與空污延伸實驗的關係

空污資料實驗應定位為：

```text
NoSE pipeline extension / engineering feasibility test
```

RUBiS 則應定位為：

```text
paper reproduction main line
```

空污實驗已證明本機 Docker/Cassandra pipeline 可處理 100k、500k、1m 等資料規模；但論文對照仍應回到 RUBiS。
