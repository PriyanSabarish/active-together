# Active Together Environment Data

这是一个可直接接入后端的独立 Python 模块，负责三个试点 LGA 的天气和空气质量：

- City of Melton (`24650`, `melton`)
- City of Melbourne (`24600`, `melbourne`)
- City of Monash (`24970`, `monash`)

模块只使用 Python 标准库。Live API 和七天离线预测包输出同一种
`EnvironmentContext`，并共用同一套 Concept V2 环境规则。

## 目录

```text
server/environment_data/
├── config/pilot_locations.csv   三个地区及代表坐标
├── open_meteo_client.py         Open-Meteo 请求和超时
├── normalizer.py                Weather + AQ 按 UTC 小时合并
├── models.py                    后端公共数据模型
├── policy.py                    Concept V2 阈值判断
├── cache.py                     gzip、checksum、原子更新和查询
├── service.py                   Live 优先、Cache 回退
├── build_offline_bundle.py      七天包 CLI
├── backend_example.py           后端调用示例
└── tests/                       标准库 unittest
```

## 生成七天离线包

从仓库根目录运行：

```powershell
python -m server.environment_data.build_offline_bundle
```

默认输出：

```text
data/environment_cache/environment-bundle-v1.json.gz
```

天气和空气质量请求都明确使用 `forecast_days=7`。如果空气质量 API 单独失败，仍然会
生成天气包；AQ 字段为 `null` 且 `air_quality_available=false`，不会插值。

每次更新先写临时文件、完成 checksum 和结构检查后再替换正式缓存。更新失败不会破坏
上一个预测包。

## 后端接入

```python
from pathlib import Path
from server.environment_data.backend_example import create_environment_service

environment_service = create_environment_service(
    Path("data/environment_cache")
)

result = environment_service.get_context(
    site_name="monash",
    requested_at=user_selected_datetime,
)
return result.to_dict()
```

建议由 FastAPI 暴露：

```text
GET  /api/v1/environment/context?site_name=monash&at=<ISO-8601>
POST /api/v1/environment/cache/refresh
GET  /api/v1/environment/cache/status
```

`at` 必须包含时区，例如 `2026-09-02T17:00:00+10:00`。查询会向下取到 UTC 整点。
返回的 `timestamp_local` 已转换为 `Australia/Sydney`。

Live 查询成功后，完整七天响应会保存到 `latest-live-forecast-v1.json.gz`，可以成为下一次
网络失败时的优先缓存。Live 请求失败、响应结构非法或所选小时不存在时，会按以下顺序查找：

1. 最近一次成功的 Live forecast；
2. 预下载的三地区离线包；
3. 均没有对应小时则抛出 `EnvironmentUnavailable`，绝不外推。

## 返回结构

```json
{
  "context": {
    "lga_code": "24970",
    "site_name": "monash",
    "display_name": "City of Monash",
    "source_mode": "cached",
    "timestamp_utc": "2026-09-02T07:00:00+00:00",
    "timestamp_local": "2026-09-02T17:00:00+10:00",
    "fetched_at_utc": "2026-08-31T03:00:00+00:00",
    "temperature_c": 16.2,
    "precipitation_probability_pct": 20,
    "wind_gusts_kmh": 28,
    "uv_index": 4.1,
    "pm2_5_ugm3": 8.4,
    "pm10_ugm3": 14.2,
    "weather_available": true,
    "air_quality_available": true
  },
  "assessment": {
    "tier": "normal",
    "show_uv_reminder": true,
    "warnings": [],
    "unavailable_fields": []
  }
}
```

## Concept V2 规则

- 降水概率 `>= 60%`：户外候选项降权。
- 阵风 `>= 40 km/h`：户外候选项降权。
- PM2.5 `>= 25 µg/m³`：户外候选项降权。
- PM10 `>= 80 µg/m³`：户外候选项降权。
- UV `>= 3`：显示防晒提醒，但 UV 本身不降权。
- 缺失值只标为 unavailable，不估算、不插值。

`tier` 应在推荐层用于排序：正常候选项优先，然后才是降权候选项。它不是安全判断，也不应
直接删除地点。

## 空间精度

当前每个 LGA 使用一个代表坐标，因此属于地区级预测。后端必须先使用边界数据确定用户属于
哪个 LGA，再把对应 `site_name` 交给本模块；不能用“离三个中心点哪个最近”代替行政区判断。
Melton 面积较大，后续提高精度时应优先增加 Melton 内部采样点。

## 测试

```powershell
python -m unittest discover -s server/environment_data/tests -v
```

测试不访问网络，覆盖三地区限制、阈值边界、UV 单独提醒、AQ 单独失败、UTC 合并、缓存
回退和超出预测范围时禁止外推。
