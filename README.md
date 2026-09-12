# Active Together

[English](#english) | [中文](#中文)

## English

Active Together is a location-based activity recommendation application for the
City of Melbourne, City of Monash and City of Melton. A user selects an exact
starting address or their current location, chooses a search radius and time
window, and receives nearby activity suggestions informed by current weather
and air-quality conditions.

### Main features

- Exact address autocomplete within the three pilot LGAs
- Browser geolocation with high-accuracy mode
- 3 km, 5 km and 10 km spatial searches
- Activity recommendations from processed Vicmap Features of Interest data
- Weather and air-quality context
- Leaflet maps with OpenStreetMap tiles

### Address search

The client waits until at least three characters have been entered and applies
a 300 ms debounce. It then calls the local FastAPI endpoint:

```http
GET /locations/autocomplete?q=11%20Exhibition%20Street%20Melbourne&limit=5
```

The backend queries the Victorian Government Vicmap Address WFS and restricts
results to these Vicmap LGA codes:

| LGA | Vicmap code |
| --- | --- |
| City of Melbourne | `343` |
| City of Melton | `344` |
| City of Monash | `348` |

Only active, primary addresses are returned. When the user selects a result,
its EPSG:4326 latitude and longitude become the centre of the existing
recommendation search.

Address data is provided by the State of Victoria under a Creative Commons
Attribution 4.0 International licence. See the
[Vicmap Address catalogue](https://www.land.vic.gov.au/maps-and-spatial/spatial-data/vicmap-catalogue/vicmap-address).

### Technology

- Client: Vue 3, Pinia, Vite, Leaflet
- API: FastAPI, SQLAlchemy, HTTPX
- Database: PostgreSQL with PostGIS
- Data: Vicmap Address and Vicmap Features of Interest

### Prerequisites

- Node.js LTS and npm
- Python 3.12
- PostgreSQL with PostGIS

### Environment configuration

Create `server/app/.env`:

```env
ENVIRONMENT=local
DEBUG=true
DATABASE_URL=postgresql+pg8000://postgres:postgres@localhost:5432/active_together
WEATHERAPI_KEY=
```

`WEATHERAPI_KEY` is optional for local development. Without it, weather is
reported as unavailable while address and place searches continue to work.

Create `client/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Both `.env` files are ignored by Git. Never commit credentials.

### First-time installation

Run from PowerShell:

```powershell
cd E:\Github\active-together\server
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd ..\client
npm install
```

If the database has not yet been prepared, create it, enable PostGIS and load
the application-ready place data:

```powershell
cd E:\Github\active-together\server
psql -d active_together -f scripts/schema.sql
.\.venv\Scripts\python.exe scripts/load_places.py --csv ../data/vicmap_app_ready.csv
```

### Start the application

Start both services from one PowerShell terminal:

```powershell
$root='E:\Github\active-together'; $backend=Start-Job -ArgumentList $root -ScriptBlock { param($r) Set-Location "$r\server"; & ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000 }; try { Set-Location "$root\client"; npm run dev } finally { Stop-Job $backend; Remove-Job $backend }
```

Open <http://localhost:5174>. The API runs at <http://localhost:8000> and its
interactive documentation is available at <http://localhost:8000/docs>.

Useful checks:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod 'http://localhost:8000/locations/autocomplete?q=11%20Exhibition%20Street%20Melbourne'
```

### Tests

```powershell
cd E:\Github\active-together\server
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest tests

cd ..\client
npm test
npm run build
```

### Troubleshooting

- `npm is not recognized`: install Node.js LTS, restart PyCharm, and check
  `node --version` and `npm --version`.
- Address search is temporarily unavailable: confirm `client/.env` points to
  `http://localhost:8000`, restart Vite, and test the autocomplete endpoint
  directly.
- Places dataset is unavailable: check `DATABASE_URL`, PostgreSQL and the
  `places` table.
- No weather data: configure `WEATHERAPI_KEY`; this does not prevent address
  search from working.

## 中文

Active Together 是一个面向 City of Melbourne、City of Monash 和 City of
Melton 的位置活动推荐应用。用户可以选择精确起始地址或使用当前位置，设置
搜索半径和活动时间，然后获得结合实时天气及空气质量的附近活动建议。

### 主要功能

- 在三个试点 LGA 范围内进行精确地址自动补全
- 使用浏览器高精度定位
- 支持 3 km、5 km 和 10 km 空间查询
- 基于处理后的 Vicmap Features of Interest 数据推荐活动场所
- 显示天气及空气质量信息
- 使用 Leaflet 和 OpenStreetMap 展示地图

### 地址查询原理

用户输入至少三个字符后，前端等待 300 ms，再调用本地 FastAPI 接口：

```http
GET /locations/autocomplete?q=11%20Exhibition%20Street%20Melbourne&limit=5
```

后端查询 Victoria 政府的 Vicmap Address WFS，并通过 Vicmap LGA code 将
结果限制在以下区域：

| 区域 | Vicmap code |
| --- | --- |
| City of Melbourne | `343` |
| City of Melton | `344` |
| City of Monash | `348` |

接口只返回有效的主要地址。用户选中地址后，其 EPSG:4326 经纬度会成为现有
推荐查询的中心点。

地址数据由 State of Victoria 根据 Creative Commons Attribution 4.0
International 许可提供。详情参见
[Vicmap Address 数据目录](https://www.land.vic.gov.au/maps-and-spatial/spatial-data/vicmap-catalogue/vicmap-address)。

### 技术栈

- 前端：Vue 3、Pinia、Vite、Leaflet
- 后端：FastAPI、SQLAlchemy、HTTPX
- 数据库：PostgreSQL + PostGIS
- 数据来源：Vicmap Address、Vicmap Features of Interest

### 环境要求

- Node.js LTS 和 npm
- Python 3.12
- PostgreSQL，并启用 PostGIS

### 环境变量

创建 `server/app/.env`：

```env
ENVIRONMENT=local
DEBUG=true
DATABASE_URL=postgresql+pg8000://postgres:postgres@localhost:5432/active_together
WEATHERAPI_KEY=
```

本地开发时 `WEATHERAPI_KEY` 可以留空。此时天气显示为不可用，但地址查询和
地点推荐仍可继续运行。

创建 `client/.env`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

两个 `.env` 文件均已被 Git 忽略，请勿提交密钥或数据库凭据。

### 首次安装

在 PowerShell 中执行：

```powershell
cd E:\Github\active-together\server
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

cd ..\client
npm install
```

如果数据库还没有初始化，需要创建数据库、启用 PostGIS 并导入地点数据：

```powershell
cd E:\Github\active-together\server
psql -d active_together -f scripts/schema.sql
.\.venv\Scripts\python.exe scripts/load_places.py --csv ../data/vicmap_app_ready.csv
```

### 启动项目

在一个 PowerShell Terminal 中同时启动前后端：

```powershell
$root='E:\Github\active-together'; $backend=Start-Job -ArgumentList $root -ScriptBlock { param($r) Set-Location "$r\server"; & ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000 }; try { Set-Location "$root\client"; npm run dev } finally { Stop-Job $backend; Remove-Job $backend }
```

打开 <http://localhost:5174>。后端地址是 <http://localhost:8000>，FastAPI
接口文档位于 <http://localhost:8000/docs>。

检查服务：

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod 'http://localhost:8000/locations/autocomplete?q=11%20Exhibition%20Street%20Melbourne'
```

### 测试

```powershell
cd E:\Github\active-together\server
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest tests

cd ..\client
npm test
npm run build
```

### 常见问题

- 出现 `npm is not recognized`：安装 Node.js LTS，重启 PyCharm，然后检查
  `node --version` 和 `npm --version`。
- 显示 `Address search is temporarily unavailable`：确认 `client/.env` 指向
  `http://localhost:8000`，重新启动 Vite，并直接测试地址接口。
- 显示地点数据不可用：检查 `DATABASE_URL`、PostgreSQL 和 `places` 表。
- 没有天气数据：配置 `WEATHERAPI_KEY`；这不会影响地址查询。
