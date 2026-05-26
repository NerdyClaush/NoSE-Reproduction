# Sharing Docker Environment

如果同學無法自行安裝 NoSE 依賴，可以把 Docker 環境分享給他。這裡有兩種方法。

## 方法 A：分享 GitHub repo，讓對方自行 build

這是最推薦的方法。

優點：

- 檔案小。
- 可追蹤版本。
- 比較符合 reproducible research。
- 對方可以看到 Dockerfile 與 compose 設定。

對方需要：

```text
Git
Docker Desktop / Docker Engine
Docker Compose
```

操作：

```powershell
git clone <你的 GitHub repo URL> NoSE-Reproduction
cd NoSE-Reproduction
mkdir upstream
git clone https://github.com/michaelmior/NoSE.git upstream/NoSE
git clone https://github.com/michaelmior/nose-cli.git upstream/nose-cli
docker compose build nose-runner rubis-generator
docker compose up -d mysql-rubis cassandra-rubis
```

接著照 `docs/hands_on_rebuild.md` 跑。

## 方法 B：匯出已 build 好的 image 給同學

Docker 支援把 image 存成 tar 檔：

```powershell
docker save -o nose-repro-images.tar nose-repro-runner:latest nose-rubis-generator:latest nose-repro-advisor-release:latest
```

同學拿到檔案後：

```powershell
docker load -i nose-repro-images.tar
```

然後仍然需要 repo 裡的：

```text
docker-compose.yml
workspace/
docs/
```

因為 compose service、scripts、結果目錄等仍由 repo 管理。

## 是否需要一起打包 MySQL / Cassandra？

可以，但不建議一開始就打包。

目前相關 image 大小：

| Image | Size |
|---|---:|
| `nose-repro-runner` | 約 1.12 GB |
| `nose-rubis-generator` | 約 1.3 GB |
| `nose-repro-advisor-release` | 約 1.03 GB |
| `mysql:5.7` | 約 700 MB |
| `cassandra:2.1` | 約 511 MB |

若全部打包：

```powershell
docker save -o nose-full-stack-images.tar nose-repro-runner:latest nose-rubis-generator:latest nose-repro-advisor-release:latest mysql:5.7 cassandra:2.1
```

這個 tar 可能會很大，但可以避免對方重新 pull image。

同學載入：

```powershell
docker load -i nose-full-stack-images.tar
```

注意：`docker save` 只會保存 image，不會保存 container 內資料庫資料。MySQL / Cassandra 的實際資料存在 Docker volumes。

目前本專案資料 volume 名稱：

```text
nose-reproduction_mysql-rubis-data
nose-reproduction_cassandra-rubis-data
```

如果要把目前已產生的 RUBiS smoke dataset 與已載入的 Cassandra column families 一起搬給同學，還要匯出 volumes。

## 方法 B2：完整搬移 images + database volumes

完整搬移需要兩類檔案：

```text
1. Docker images tar
2. Docker volumes tar
```

本專案已提供 PowerShell 腳本：

```text
workspace\host-scripts\export_full_stack.ps1
workspace\host-scripts\import_full_stack.ps1
```

### 在你的電腦匯出

於專案根目錄執行：

```powershell
cd D:\Database_Project\NoSE-Reproduction
powershell -ExecutionPolicy Bypass -File .\workspace\host-scripts\export_full_stack.ps1
```

預設會輸出到：

```text
D:\Database_Project\NoSE-Reproduction\handoff\
```

內容會包含：

```text
nose-full-stack-images.tar
nose-mysql-rubis-data.tar.gz
nose-cassandra-rubis-data.tar.gz
manifest.txt
```

不要把這些大型 tar 檔 commit 進 GitHub repo。可以用：

- 外接硬碟 / USB
- 雲端硬碟
- GitHub Release 附件（若檔案大小允許）
- 學校內部檔案分享空間

GitHub repo 本身只放程式碼、Dockerfile、compose、scripts、docs。

### 在同學電腦還原

同學先 clone repo 並把 `handoff` 資料夾放在 repo 根目錄：

```powershell
git clone <你的 GitHub repo URL> NoSE-Reproduction
cd NoSE-Reproduction
```

資料夾結構應類似：

```text
NoSE-Reproduction
├── docker-compose.yml
├── workspace\
├── docs\
└── handoff\
    ├── nose-full-stack-images.tar
    ├── nose-mysql-rubis-data.tar.gz
    ├── nose-cassandra-rubis-data.tar.gz
    └── manifest.txt
```

然後執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\workspace\host-scripts\import_full_stack.ps1
```

還原後驗證：

```powershell
docker compose ps
docker compose run --rm nose-runner bash -lc "rubis-write-nose-config && bundle exec nose execute rubis_baseline --mix=browsing --num-iterations=5 --repeat=1 --no-fail-on-empty --format=csv"
```

### 匯出 images

```powershell
docker save -o nose-full-stack-images.tar `
  nose-repro-runner:latest `
  nose-rubis-generator:latest `
  nose-repro-advisor-release:latest `
  mysql:5.7 `
  cassandra:2.1
```

### 匯出 MySQL volume

```powershell
docker run --rm `
  -v nose-reproduction_mysql-rubis-data:/volume `
  -v ${PWD}:/backup `
  alpine tar czf /backup/nose-mysql-rubis-data.tar.gz -C /volume .
```

### 匯出 Cassandra volume

匯出前建議先停止 database containers，避免複製到一半資料還在寫入：

```powershell
docker compose stop mysql-rubis cassandra-rubis
```

接著匯出：

```powershell
docker run --rm `
  -v nose-reproduction_cassandra-rubis-data:/volume `
  -v ${PWD}:/backup `
  alpine tar czf /backup/nose-cassandra-rubis-data.tar.gz -C /volume .
```

匯出完可重新啟動：

```powershell
docker compose up -d mysql-rubis cassandra-rubis
```

### 同學端載入 images

```powershell
docker load -i nose-full-stack-images.tar
```

### 同學端建立 volumes

```powershell
docker volume create nose-reproduction_mysql-rubis-data
docker volume create nose-reproduction_cassandra-rubis-data
```

### 同學端還原 MySQL volume

```powershell
docker run --rm `
  -v nose-reproduction_mysql-rubis-data:/volume `
  -v ${PWD}:/backup `
  alpine sh -c "cd /volume && tar xzf /backup/nose-mysql-rubis-data.tar.gz"
```

### 同學端還原 Cassandra volume

```powershell
docker run --rm `
  -v nose-reproduction_cassandra-rubis-data:/volume `
  -v ${PWD}:/backup `
  alpine sh -c "cd /volume && tar xzf /backup/nose-cassandra-rubis-data.tar.gz"
```

### 同學端啟動 compose

```powershell
docker compose up -d mysql-rubis cassandra-rubis
docker compose ps
```

如果 volume 名稱因專案資料夾名稱不同而改變，請以 `docker volume ls` 的實際名稱為準，或讓同學也使用同名資料夾 `NoSE-Reproduction`。

## 方法 C：推到 Docker Hub / GitHub Container Registry

如果要更正式，可以把 image push 到 registry。

範例：

```powershell
docker tag nose-repro-runner:latest <dockerhub-user>/nose-repro-runner:latest
docker push <dockerhub-user>/nose-repro-runner:latest
```

但這需要 Docker Hub / GHCR 帳號與登入設定。對課堂專案來說，通常 GitHub repo + Dockerfile 已經足夠。

## Container vs Image

要注意用詞：

- Image：可重複建立 container 的環境模板。
- Container：由 image 啟動後正在執行或曾經執行的實例。

建議分享 image 或 Dockerfile，不建議分享正在跑的 container。

## 推薦做法

給同學最穩的方式：

1. 分享 GitHub repo。
2. 若他網路或 build 失敗，再補一份 `docker save` 匯出的 image tar。
3. 若希望連目前 MySQL / Cassandra 的已載入資料也保留，額外提供 volume tar。
4. 文件指定他照 `docs/hands_on_rebuild.md` 或本文件的完整搬移流程操作。
