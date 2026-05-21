# NoSE Reproduction Project

本目錄用來複現論文 *NoSE: Schema Design for NoSQL Applications*。

## Directory Layout

```text
D:\Database_Project\NoSE-Reproduction
├── upstream\
│   ├── NoSE\       # 官方核心 library: https://github.com/michaelmior/NoSE
│   └── nose-cli\   # 官方 CLI: https://github.com/michaelmior/nose-cli
├── workspace\      # 本專案自行撰寫的 scripts / notes / glue code
├── experiments\    # 實驗輸出、benchmark results、log
└── docs\           # 論文整理、復現計畫、可行性分析
```

核心文件：

- `docs\reproduction_plan.md`：整體複現路線。
- `docs\docker_strategy.md`：Docker-first 環境策略。
- `docs\nose_pipeline.md`：NoSE pipeline 導讀與 Mermaid 圖。
- `docs\paper_structure.md`：論文章節結構與複現優先順序。
- `docs\dataset_plan.md`：RUBiS synthetic dataset 與資料載入規劃。
- `docs\database_stack.md`：MySQL / Cassandra / NoSE runner 架設與驗證紀錄。

## Current Strategy

1. 以 Docker 為優先環境，先讓官方 `NoSE` 與 `nose-cli` 跑起來。
2. 優先復現 EAC case study，因為它比 RUBiS latency benchmark 小很多。
3. 再復現 RUBiS advisor output。
4. 最後才處理 Cassandra latency experiment、cost calibration、advisor runtime scaling。

## Known Environment Needs

- Git: installed at `C:\Program Files\Git\cmd\git.exe`
- Ruby 2+
- Bundler
- Coin-OR CBC solver
- Docker Desktop / Docker CLI

目前 Codex session 的 `PATH` 尚未看到 `git`，所以暫時使用完整路徑：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status
```

Docker-first 原則：

- 不在 Windows native 環境手動追 CBC / Ruby gem 相依，除非 Docker 路線失敗。
- 先使用官方 `michaelmior/nose` image 驗證 advisor。
- Cassandra latency experiment 再獨立設計 compose / legacy image。
