# Docker Strategy

本專案優先採用 Docker 複現 NoSE，原因如下：

- NoSE 依賴 Ruby、Bundler、Coin-OR CBC solver，Windows native 安裝風險較高。
- 論文 evaluation 使用 Cassandra 2.0.9，屬於舊環境，容器化比較容易固定版本。
- Docker 可讓 advisor-only reproduction 與 Cassandra latency benchmark 分階段處理。

## Phase A: Advisor-only Container

目標：先跑通官方 schema advisor，不碰 Cassandra latency。

官方 README 建議：

```powershell
docker run --interactive --tty --rm michaelmior/nose /bin/bash
```

進容器後優先嘗試：

```bash
bundle exec nose help
bundle exec nose search eac
bundle exec nose search rubis
```

目前已建立兩個 advisor Dockerfile：

- `workspace\Dockerfile.advisor-release`
  - 使用 `nose-cli` source tree。
  - 依賴 Rubygems 發布版 `nose 0.1.4`。
  - 目前已成功 build。
  - 目前建議作為第一條複現路線。
- `workspace\Dockerfile.advisor`
  - 嘗試使用本地 `upstream\NoSE` main branch，也就是 `nose 0.2.0`。
  - 目前卡在 `nose-cli 0.1.5` 與 `nose 0.2.0` 依賴版本不完全相容。
  - 暫時保留作為後續 source-level reproduction 路線。

已驗證成功：

```powershell
cd D:\Database_Project\NoSE-Reproduction
docker build -f workspace\Dockerfile.advisor-release -t nose-repro-advisor-release .
docker run --rm nose-repro-advisor-release bundle exec nose help search
docker run --rm nose-repro-advisor-release bundle exec nose search eac --read-only --no-interactive
```

已保存 EAC read-only 結果：

```text
D:\Database_Project\NoSE-Reproduction\experiments\results\eac_read_only.txt
```

結果摘要：

- 3 個 indexes。
- 5 條 query plans。
- Total size: `391380000`。
- Total cost: `20`。

完整 EAC 含 updates 的 search 曾執行超過 5 分鐘未完成，需後續另行分析 update support / ILP 求解時間。

若官方 image 內沒有最新 source 或 CLI 狀態不一致，再改為掛載本機 clone：

```powershell
docker run --interactive --tty --rm `
  -v D:\Database_Project\NoSE-Reproduction\upstream\NoSE:/src/NoSE `
  -v D:\Database_Project\NoSE-Reproduction\upstream\nose-cli:/src/nose-cli `
  michaelmior/nose /bin/bash
```

## Phase B: Reproducible Local Image

如果官方 image 不穩定，建立本專案自己的 Dockerfile：

- base image 先參考 `upstream\nose-cli\Dockerfile`
- 安裝 Ruby / Bundler / CBC
- clone 或 copy `NoSE` 與 `nose-cli`
- 固定 gem install 步驟

輸出目標：

- `bundle exec nose help`
- `bundle exec nose search eac`
- `bundle exec nose search rubis`

本專案已先放置 advisor-only Dockerfile：

```powershell
cd D:\Database_Project\NoSE-Reproduction
docker build -f workspace\Dockerfile.advisor -t nose-repro-advisor .
docker run --interactive --tty --rm nose-repro-advisor
```

容器內：

```bash
bundle exec nose help
bundle exec nose search eac
bundle exec nose search rubis
```

## Phase C: Cassandra Benchmark

這是後期工作，先不跟 advisor-only 混在一起。

需要確認：

- Cassandra 2.0.9 image 是否可用。
- Java 版本相容性。
- Cassandra-level caching 關閉設定。
- RUBiS data generation 是否可跑。
- client-side execution engine 是否能連到 Cassandra。

若 Cassandra 2.0.9 無法穩定啟動，記錄為 approximate reproduction，改用較新 Cassandra 版本做趨勢驗證。

## First Docker Check

Docker 安裝完成後，在 PowerShell 執行：

```powershell
docker --version
docker run --rm hello-world
docker run --interactive --tty --rm michaelmior/nose /bin/bash
```
