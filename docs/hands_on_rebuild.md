# Hands-on Rebuild Guide

這份文件是給自己或同學從零親手重建 NoSE 複現環境用的。目標不是直接追論文完整規模，而是先確認以下鏈條可以跑通：

```text
Docker
→ NoSE CLI
→ MySQL staging DB
→ RUBiS synthetic data
→ Cassandra target backend
→ NoSE create/load/execute
```

## 0. 為什麼同學可能裝不起來？

失敗原因通常不是 Linux 本身，而是這篇論文的實作環境很舊：

- Ruby 2.5.1
- Bundler 需要固定為 2.3.27
- NoSE CLI 0.1.5 依賴 `nose 0.1.4`
- Coin-OR CBC 不是新版 Gurobi
- Cassandra 2.0.9 已很舊，Docker Hub 沒有直接可用的 `cassandra:2.0.9`
- `NoSE` main branch 已是 `nose 0.2.0`，但 `nose-cli` main branch 仍偏向 `nose 0.1.4`

因此不要在主機上硬裝 Ruby/CBC/Cassandra。建議全部用 Docker。

## 1. 需要的主機工具

Windows / Linux / macOS 都可以，但需要：

```text
Git
Docker
Docker Compose
```

確認：

```powershell
git --version
docker --version
docker compose version
docker run --rm hello-world
```

## 1.1 容器作業系統決策

論文本身沒有指定 Docker container OS。論文描述的是實驗機器與 Cassandra 版本，而不是容器化流程。

本複現選擇：

```text
Ubuntu 18.04
```

理由：

1. 官方 `nose-cli/Dockerfile` 使用 `ubuntu:18.04`。
2. Ubuntu 18.04 apt repository 仍提供 `ruby2.5` / `ruby2.5-dev`，可對應 NoSE CLI 的舊 Ruby ecosystem。
3. Ubuntu 18.04 也提供 Coin-OR CBC library packages，例如 `coinor-libcbc3`、`coinor-libcbc-dev`。
4. 若使用太新的 Ubuntu，例如 22.04 / 24.04，Ruby、Bundler、native gems、CBC library 的版本漂移會更嚴重。

因此第一階段不選最新 Linux image，而是選擇和官方 NoSE CLI Dockerfile 一致的舊版 Ubuntu。

對應 Dockerfile 開頭：

```dockerfile
FROM ubuntu:18.04
```

目前本專案有兩個主要 NoSE image 都採用此 base：

```text
workspace/Dockerfile.advisor-release
workspace/Dockerfile.runner
```

重要補充：

- Cassandra target backend 使用獨立 container，不放在 NoSE runner container 裡。
- MySQL staging database 使用獨立 container，不放在 NoSE runner container 裡。
- RUBiS generator 使用 Node.js container，不放在 NoSE runner container 裡。

因此整體是 multi-container setup，而不是把全部東西塞進同一個 Ubuntu container。

## 2. Clone 本專案

```powershell
git clone <你的 GitHub repo URL> NoSE-Reproduction
cd NoSE-Reproduction
```

如果是用目前這台電腦：

```powershell
cd D:\Database_Project\NoSE-Reproduction
```

## 3. Clone 官方 upstream repos

本專案 `.gitignore` 不追蹤 `upstream/`，所以換電腦後要重新 clone：

```powershell
mkdir upstream
git clone https://github.com/michaelmior/NoSE.git upstream/NoSE
git clone https://github.com/michaelmior/nose-cli.git upstream/nose-cli
```

檢查：

```powershell
dir upstream
```

應該看到：

```text
NoSE
nose-cli
```

## 4. Build Docker images

建議先 build runner 和 generator：

```powershell
docker compose build nose-runner rubis-generator
```

如果只想測 NoSE advisor：

```powershell
docker build -f workspace\Dockerfile.advisor-release -t nose-repro-advisor-release .
```

## 5. 確認 NoSE CLI 版本

```powershell
docker compose run --rm nose-runner bash -lc "ruby -v && bundle -v && bundle info nose-cli && bundle info nose"
```

目前成功環境應為：

```text
Ruby      2.5.1p57
Bundler   2.3.27
nose-cli  0.1.5
nose      0.1.4
```

CBC 相關：

```powershell
docker compose run --rm nose-runner bash -lc "dpkg-query -W 'coinor-libcbc*' 'coinor-libcgl*' 'coinor-libclp*' 'coinor-libcoinutils*' 'coinor-libosi*' 2>/dev/null | sort; bundle info mipper"
```

目前成功環境：

```text
coinor-libcbc3     2.9.9+repack1-1
coinor-libcbc-dev  2.9.9+repack1-1
mipper             0.1.0
```

注意：容器內沒有獨立 `cbc` command-line binary；NoSE 透過 `mipper` 連 CBC library。

## 6. 啟動資料庫

```powershell
docker compose up -d mysql-rubis cassandra-rubis
docker compose ps
```

應看到：

```text
mysql-rubis       healthy
cassandra-rubis   healthy
```

目前使用：

```text
MySQL      5.7
Cassandra 2.1
```

注意：論文使用 Cassandra 2.0.9，但目前 Docker Hub 無直接可用 `cassandra:2.0.9` manifest，因此這裡是近似復現。

## 7. 初始化 RUBiS schema / keyspace

```powershell
docker compose run --rm nose-runner rubis-smoke-prepare
```

這會做三件事：

```text
寫入 /src/nose-cli/nose.yml
初始化 MySQL RUBiS schema
建立 Cassandra rubis keyspace
```

## 8. 產生小規模 RUBiS synthetic data

```powershell
docker compose run --rm rubis-generator
```

預設 smoke scale：

```text
categories  500
regions     50
users       1000
items       5000
bids        20000
comments    10000
buynow      5000
```

確認 MySQL 筆數：

```powershell
docker compose exec -T mysql-rubis mysql -uroot -proot -Drubis -e "SELECT 'categories' tbl, COUNT(*) n FROM categories UNION ALL SELECT 'regions', COUNT(*) FROM regions UNION ALL SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'items', COUNT(*) FROM items UNION ALL SELECT 'bids', COUNT(*) FROM bids UNION ALL SELECT 'comments', COUNT(*) FROM comments UNION ALL SELECT 'buynow', COUNT(*) FROM buynow;"
```

## 9. 載入 Cassandra baseline schema

```powershell
docker compose run --rm nose-runner bash -lc "rubis-write-nose-config && rubis-fix-generated-data && rubis-reset-cassandra && bundle exec nose create rubis_baseline && bundle exec nose load rubis_baseline"
```

這會：

```text
修正 categories/regions dummy 欄位
重建 Cassandra rubis keyspace
建立 rubis_baseline column families
從 MySQL staging DB 載入 Cassandra
```

確認 Cassandra 筆數：

```powershell
docker compose exec -T cassandra-rubis cqlsh 127.0.0.1 9042 -k rubis -e "SELECT COUNT(*) FROM items; SELECT COUNT(*) FROM bids; SELECT COUNT(*) FROM all_categories;"
```

應看到類似：

```text
items           5000
bids            20000
all_categories  500
```

## 10. 執行 baseline smoke benchmark

```powershell
docker compose run --rm nose-runner bash -lc "rubis-write-nose-config && bundle exec nose execute rubis_baseline --mix=browsing --num-iterations=5 --repeat=1 --no-fail-on-empty --format=csv | tee /results/rubis_baseline_smoke_execute_manual.csv"
```

重點：

- `rubis_baseline` 是 manually-defined plans，所以用 `nose execute`。
- 一定要指定 `--mix=browsing`。
- 若不指定 mix，輸出可能只有 CSV header。

結果會在：

```text
experiments/results/rubis_baseline_smoke_execute_manual.csv
```

## 11. 常見錯誤

### 只有 CSV header，沒有結果

原因：沒有指定 mix。

修正：

```powershell
--mix=browsing
```

### `Invalid null value for partition key part categories_dummy`

原因：官方 `rubis-update.sql` 在資料生成前設定 dummy，但 synthetic data 是之後插入，所以 dummy 變成 null。

修正：

```powershell
rubis-fix-generated-data
```

### 找不到 `cassandra:2.0.9`

目前 Docker Hub 沒有可直接使用的 `cassandra:2.0.9` manifest。

修正：先用 `cassandra:2.1` 做近似復現，報告中明確標註。

### `cbc: command not found`

目前環境使用 CBC library，不是 command-line binary。

確認 CBC library：

```powershell
docker compose run --rm nose-runner bash -lc "dpkg-query -W 'coinor-libcbc*'"
```

## 12. 今日可達成的最低目標

如果要親手證明環境成功，最低目標是跑出：

```text
rubis_baseline_smoke_execute_manual.csv
```

只要這個檔案有多行 benchmark result，就代表以下流程已經成功：

```text
Docker
→ MySQL staging data
→ Cassandra target backend
→ NoSE loader
→ NoSE execute
```
