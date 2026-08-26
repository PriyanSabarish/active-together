# Hourly Environment Context 数据说明

## 1. 文件作用

`hourly_environment_context.csv` 是 Active Together 项目的环境上下文整合数据。它把
Open-Meteo Weather Forecast 和 Open-Meteo Air Quality 两个清洗后的数据集连接在一起，
用于支持以下产品功能：

- 根据家长选择的日期和时间查询天气；
- 在推荐户外活动地点时考虑温度、体感温度、降水概率和风；
- 在空气质量预测可用时提供 UV、PM2.5 和 PM10；
- 为推荐结果生成“为什么推荐”或“为什么降权”的环境说明；
- 支持未来的 context matching 和活动地点排序。

该文件是产品使用层的精简数据，不包含 raw API 返回的全部元数据。原始 JSON 位于
`data/raw/open_meteo/`，清洗后的独立数据位于 `data/processed/open_meteo/`。

## 2. 一行代表什么

一行代表：

```text
一个 Metropolitan Melbourne LGA 代表点在一个预测小时的环境条件
```

当前覆盖31个 Metropolitan Melbourne municipalities，每个地区有168个 Weather
预测小时，因此整合文件共有5,208行。

复合主键是：

```text
site_name + timestamp_utc
```

这两个字段组合后应当唯一。不要只用 `site_name` 或经纬度判断重复，因为同一个地区会在
不同小时出现多行。

## 3. 为什么同一经纬度会有不同数值

经纬度描述空间位置，时间字段描述预测时刻。对于 Monash 等地区，所有行使用相同的 LGA
代表坐标，但每行的 `timestamp_local` 和 `timestamp_utc` 不同，因此温度、PM2.5、UV、
降水概率和风速也会随时间变化。

下面这种情况是正常的：

```text
site_name  latitude  longitude  timestamp_local          pm2_5_ugm3
monash     相同      相同       2026-08-26T00:00+10:00   3.8
monash     相同      相同       2026-08-26T01:00+10:00   3.9
monash     相同      相同       2026-08-26T02:00+10:00   4.4
```

只有在 `site_name` 和 `timestamp_utc` 都相同但环境数值不同的情况下，才属于重复或连接
错误。生成脚本会检查并拒绝这种情况。

## 4. 地理范围和空间限制

地区清单来自 `pipeline/config/open_meteo_locations.csv`，包括31个 Metropolitan
Melbourne LGA。`latitude` 和 `longitude` 是每个 LGA 的 ABS ASGS 2025 LGA point
代表坐标，并不是：

- 用户的实时位置；
- 某个具体公园或活动地点的坐标；
- Open-Meteo 最终采用的模型网格中心坐标；
- 对整个 LGA 每个位置都同样精确的观测站坐标。

因此，该文件适合进行 LGA 级原型和推荐逻辑验证，但不能证明同一 LGA 内所有地点的天气
或空气质量完全相同。尤其是 Cardinia、Yarra Ranges、Mornington Peninsula 等面积较大
的 LGA，一个代表点无法描述整个区域内部的空间差异。
Local Government Area

后续如果需要场所级精度，应使用 Vicmap 活动地点坐标请求 Open-Meteo，并把多个相近场所
映射到去重后的 Weather/Air Quality 模型网格，而不是继续增加 LGA 中心点。

## 5. 字段说明

| 字段 | 类型/单位 | 说明 |
|---|---|---|
| `site_name` | string | 机器使用的 LGA 标识，小写 snake_case，例如 `greater_dandenong`。 |
| `display_name` | string | 界面显示的 LGA 名称，例如 `Greater Dandenong`。 |
| `lga_code` | string | ABS 2025 LGA code。应当作为字符串处理。 |
| `timestamp_local` | ISO 8601 | Australia/Sydney 本地预测时间，包含 UTC 偏移。 |
| `timestamp_utc` | ISO 8601 | 同一时刻的 UTC 时间，推荐作为系统连接和存储时间。 |
| `latitude` | decimal degrees | LGA 代表请求点纬度，WGS84。 |
| `longitude` | decimal degrees | LGA 代表请求点经度，WGS84。 |
| `temperature_c` | °C | 地面以上2米的预测温度。 |
| `apparent_temperature_c` | °C | 综合湿度、风和辐射等因素的体感温度。 |
| `precipitation_probability_pct` | % | 对应小时的降水概率，范围0–100。 |
| `weather_code` | integer | WMO weather interpretation code。 |
| `weather_description` | string | `weather_code` 对应的英文机器可读描述。 |
| `wind_speed_kmh` | km/h | 地面以上10米的预测风速。 |
| `wind_gusts_kmh` | km/h | 地面以上10米的预测阵风。 |
| `uv_index` | index | Open-Meteo Air Quality API 的 UV index；不可用时为空。 |
| `pm2_5_ugm3` | µg/m³ | PM2.5 预测浓度；不可用时为空。 |
| `pm10_ugm3` | µg/m³ | PM10 预测浓度；不可用时为空。 |
| `air_quality_available` | boolean text | `true` 表示三个空气质量字段都有值，`false` 表示均不可用。 |

字段名称中的单位后缀用于避免前后端混淆：

- `_c`：摄氏度；
- `_pct`：百分比；
- `_kmh`：千米/小时；
- `_ugm3`：微克/立方米。

## 6. Weather 与 Air Quality 的时间范围不同

Weather Forecast 当前下载7天，即每个地区168小时。Air Quality 当前下载5天，但 API
快照的最后一个小时中 UV、PM2.5 和 PM10 同时为空；wrangling 阶段删除了这31行全空记录，
所以每个地区有119个有效空气质量小时。

整合使用：

```text
Weather LEFT JOIN Air Quality
ON site_name + timestamp_utc
```

因此：

- 最终文件保留全部5,208行 Weather；
- 3,689行同时具有 Air Quality；
- 1,519行只有 Weather；
- 没有 Air Quality 的行保留为空，并设置 `air_quality_available=false`；
- 不使用均值、前向填充或插值制造空气质量预测。

应用程序读取 UV 或颗粒物之前，必须先检查 `air_quality_available`。

## 7. 推荐的查询方式

查询某个地区在用户选择时刻的环境数据时，优先使用：

```text
site_name + timestamp_utc
```

如果用户输入的是本地时间，应先按照 `Australia/Sydney` 转换为 UTC，再进行匹配。不要直接
用 CSV 行号、经纬度或 `hour` 数字进行连接。

示例：

```python
import pandas as pd

context = pd.read_csv(
    "data/processed/integrated/hourly_environment_context.csv",
    dtype={"lga_code": "string"},
    parse_dates=["timestamp_local", "timestamp_utc"],
)

selection = context.loc[
    (context["site_name"] == "monash")
    & (context["timestamp_utc"] == pd.Timestamp("2026-08-26T01:00:00Z"))
]
```

## 8. 使用注意事项

- 数据是预测值，不是安全保证或实时观测值。
- 不要把探索阶段使用的降水、UV 或颗粒物阈值直接当作医疗或安全标准。
- `weather_description` 是代码描述，不等同于完整的家长提示文本。
- 相邻 LGA 可能落入同一个 Open-Meteo 模型网格，因此数值可能完全相同。
- 大面积 LGA 内部可能存在明显空间差异。
- 每次重新下载后，时间范围和具体预测值都会变化。
- 后端应为网络失败、预测范围外和空气质量不可用提供明确降级逻辑。

## 9. 数据来源和生成流程

数据来源：

- Open-Meteo Weather Forecast API；
- Open-Meteo Air Quality API；
- ABS ASGS 2025 LGA point 地理坐标。

生成顺序：

```powershell
python pipeline/exploration/download_open_meteo.py
python pipeline/exploration/explore_open_meteo.py
python pipeline/wrangling/wrangle_weather_forecast.py
python pipeline/wrangling/wrangle_air_quality.py
python pipeline/integration/build_open_meteo_context.py
```

其中最终整合逻辑位于：

```text
pipeline/integration/build_open_meteo_context.py
```

每次原始快照更新后，应重新执行 exploration、wrangling 和 integration，并重新检查 validation
报告后再交给服务器使用。
