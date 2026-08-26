# Open-Meteo Data Wrangling 说明

## 目标和文件位置

两个脚本分别处理天气和空气质量，避免一个数据源失败时阻塞另一个：

```powershell
python pipeline/wrangling/wrangle_weather_forecast.py
python pipeline/wrangling/wrangle_air_quality.py
```

输入是 `data/raw/open_meteo/` 中日期最新的 JSON，输出是：

- `data/processed/open_meteo/weather_forecast_clean.csv`
- `data/processed/open_meteo/air_quality_clean.csv`
- `data/validation/open_meteo/*_wrangling_report.json`

## 共同处理步骤

`open_meteo_common.py` 负责共享逻辑：

1. 自动查找最新日期快照，避免在代码中固定日期；
2. 将“地点列表—hourly 数组”展开为一行一个地点、一个小时的长表；
3. 保留请求坐标、API 网格坐标、海拔、源时区和源文件名，保证可追溯性；
4. 将 Open-Meteo 返回的 Sydney 本地时间显式本地化，并同时生成 UTC 时间；
5. 检查 `(site_name, timestamp_local)` 复合主键是否唯一；
6. 输出机器可读的 JSON 验证报告。

显式保存本地和 UTC 时间很重要：产品面向家长时需要本地小时，而后端存储、跨系统合并和
夏令时处理更适合使用 UTC。

## Weather 清洗规则

- 六个核心指标强制转换为数值；不能解析时立即报错，而不是静默变成空值。
- `weather_code` 转换为整数，并根据 WMO 代码新增英文
  `weather_description`。出现未知代码时脚本停止，提醒开发者更新映射。
- 对温度、体感温度、降水概率、风速和阵风执行宽松的物理范围检查。范围用于发现单位错误
  或损坏数据，不是产品安全阈值。
- 不删除本次 Forecast 的任何行，也不把连续变量人为分箱，避免在 wrangling 阶段损失信息。

## Air Quality 缺失值规则

探索阶段发现每个 LGA 最后一个小时的 UV、PM2.5、PM10 同时为空。清洗脚本采用完整且可
审计的规则：

- 三个指标同时为空：删除该地点—小时记录；
- 只有部分指标为空：立即报错，等待为具体字段制定规则；
- 不使用均值、前向填充或插值，因为这些值将影响户外活动建议，不能把估算值伪装成 API
  预测值。

删除的地点、数量和时间戳全部记录在 validation JSON 中。

## 为什么不在本阶段加入推荐阈值

Data wrangling 的职责是修正结构、类型、主键、时间和缺失值，而不是决定“是否适合户外
活动”。降水概率、UV 或颗粒物阈值属于产品规则，应在后续 config/context-matching 阶段
集中管理。这样数据输出保持通用，也能避免把探索性阈值误当作安全保证。
