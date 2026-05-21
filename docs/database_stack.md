# Database Stack Setup

本文件記錄目前 MySQL / Cassandra / NoSE runner 的 Docker 架設狀態。

## 1. Services

目前 `docker-compose.yml` 包含四個服務：

| Service | Image | 用途 |
|---|---|---|
| `mysql-rubis` | `mysql:5.7` | RUBiS source/staging database；不是 NoSE 的目標資料庫 |
| `cassandra-rubis` | `cassandra:2.1` | NoSE target Cassandra backend |
| `nose-runner` | `nose-repro-runner` | Ruby / NoSE / MySQL client / Cassandra driver |
| `rubis-generator` | `nose-rubis-generator` | Node.js / mysql-faker synthetic data generator |

注意：論文使用 Cassandra 2.0.9，但 Docker Hub 上目前沒有可直接使用的 `cassandra:2.0.9` manifest，因此先使用 `cassandra:2.1` 作為近似復現。

## 2. 已驗證指令

啟動資料庫：

```powershell
docker compose up -d mysql-rubis cassandra-rubis
docker compose ps
```

初始化 MySQL source/staging schema、NoSE config、Cassandra keyspace：

```powershell
docker compose run --rm nose-runner rubis-smoke-prepare
```

產生小規模 RUBiS data 到 MySQL staging database：

```powershell
docker compose run --rm rubis-generator
```

確認 MySQL 筆數：

```powershell
docker compose exec -T mysql-rubis mysql -uroot -proot -Drubis -e "SELECT 'users' tbl, COUNT(*) n FROM users;"
```

修正 generated data 的 dummy 欄位、重置 Cassandra、建立 baseline schema、載入資料：

```powershell
docker compose run --rm nose-runner bash -lc "rubis-write-nose-config && rubis-fix-generated-data && rubis-reset-cassandra && bundle exec nose create rubis_baseline && bundle exec nose load rubis_baseline"
```

確認 Cassandra tables：

```powershell
docker compose exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -k rubis -e "DESCRIBE TABLES"
```

## 3. Smoke Dataset

MySQL 在這裡只是官方實驗流程的 staging layer。NoSE 論文真正評估的 target backend 是 Cassandra；`nose load` 會把 MySQL 中的 RUBiS source data 轉成 Cassandra column families。

目前 `rubis-generator` 預設小規模：

| Table | Rows |
|---|---:|
| `categories` | 500 |
| `regions` | 50 |
| `users` | 1,000 |
| `items` | 5,000 |
| `bids` | 20,000 |
| `comments` | 10,000 |
| `buynow` | 5,000 |

MySQL 驗證結果：

| Table | Rows |
|---|---:|
| `categories` | 500 |
| `regions` | 50 |
| `users` | 1,000 |
| `items` | 5,000 |
| `bids` | 20,000 |
| `comments` | 10,000 |
| `buynow` | 5,000 |

## 4. Load 驗證

`nose load rubis_baseline` 已成功完成。

部分 Cassandra count 驗證：

| Table | Rows |
|---|---:|
| `items` | 5,000 |
| `bids` | 20,000 |
| `all_categories` | 500 |
| `regions` | 50 |
| `categories` | 500 |
| `users` | 894 |
| `users_by_region` | 894 |

`users` 在 MySQL 為 1,000，但 Cassandra baseline tables 中目前為 894。其他主要表與 index 已吻合。這可能與 NoSE loader/model mapping 或 generated values 有關，需後續追查，但目前已足以證明資料流：

```text
MySQL -> NoSE loader -> Cassandra
```

已經打通。

## 5. Scale Strategy

後續放大資料量時，建議依序使用：

1. smoke scale：目前設定。
2. medium scale：`users=10000`、`items=100000`、`bids=1000000`。
3. paper scale：官方 `fake.js` 規模。

完整論文規模：

| Table | Rows |
|---|---:|
| `users` | 200,000 |
| `items` | 2,000,000 |
| `bids` | 20,000,000 |
| `comments` | 10,000,000 |
| `buynow` | 2,000,000 |
