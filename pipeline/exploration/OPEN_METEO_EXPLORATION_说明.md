# Open-Meteo 数据探索代码说明

## 运行方法

在项目根目录运行：

```powershell
python pipeline/exploration/explore_open_meteo.py
```

脚本自动选择 `data/raw/open_meteo/` 中日期最新的 Forecast 和 Air Quality
JSON，并把探索结果写入：

```text
data/processed/open_meteo/exploration/
```

脚本只读取 raw 数据，不修改原始文件。核心分析只依赖 `pandas` 和 `numpy`。
如果环境中存在 `matplotlib`，还会生成 PNG 图；没有安装时统计分析仍能完整运行。

当前地点清单是 `pipeline/config/open_meteo_locations.csv` 中的31个 Metropolitan
Melbourne municipalities，坐标来自 ABS ASGS 2025 LGA point 图层。

## 代码结构

### 1. `latest_snapshot`

根据 `weather_forecast_YYYY-MM-DD.json` 或
`air_quality_YYYY-MM-DD.json` 的文件名排序，选择最新快照。这样组员更新数据后不需要
手动修改代码中的日期。

### 2. `flatten_hourly_json`

Open-Meteo 的原始结构是“地点列表 → hourly 字典 → 每个变量一个数组”。该函数把它
转换成长表：一行代表一个地点的一个小时。地点名、请求坐标和 API 实际采用的网格坐标
会保留下来，便于后续检查空间偏差。

### 3. `quality_report`

逐字段报告：

- 数据类型和总行数；
- 缺失数量与缺失比例；
- 唯一值数量；
- 数值变量的最小值和最大值。

这个表用于先发现结构或质量问题，再进行统计解释。例如空气质量第一个时间点可能出现
空值；raw 层应保留它，后续处理时再依据业务规则决定删除、插值或使用最近有效值。

### 4. `validate_hourly_panel`

按地点检查开始时间、结束时间、重复时间戳和非一小时间隔。天气/API 数据属于面板数据，
即多个地点共享一组时间序列；若某个地点少一小时，直接汇总可能产生不公平比较。

### 5. `weather_summary`

按地点计算温度、体感温度、降水概率、风速和阵风的均值或极值，并统计降水概率大于等于
50% 的小时数。这些指标对应项目中的“活动时间是否合适”和“户外选项是否降权”。50%
只是探索标签，不应直接当作安全保证或最终产品规则。

### 6. `air_quality_summary`

按地点汇总 UV、PM2.5 和 PM10。UV 大于等于 3 和 6 的小时数用于观察不同强度时段的
分布；代码不把颗粒物数值自动转换成健康建议，以免在没有确认正式业务标准前做出医疗或
安全结论。

### 7. `numeric_correlations`

生成 Pearson 相关矩阵，用于观察变量是否一起变化。例如温度与体感温度通常高度相关，
PM2.5 与 PM10 也可能同向变化。相关性只能描述线性共同变化，不能证明因果关系。

### 8. `save_optional_charts`

如果有 `matplotlib`，生成两张基础图：Melbourne CBD 温度时间序列，以及各地点 PM2.5/
PM10 平均值对比。图表是探索辅助，不取代输出 CSV 中的精确结果。

## 输出文件

- `weather_quality.csv`、`air_quality_quality.csv`：字段质量报告；
- `*_panel_validation.csv`：逐地点时间完整性检查；
- `*_site_summary.csv`：逐地点描述性统计；
- `*_correlations.csv`：变量相关矩阵；
- `exploration_metadata.json`：输入文件、单位、行数和探索阈值；
- 可选 PNG：基础可视化。

## 后续数据处理建议

探索完成后，wrangling 阶段应把时间统一为带时区字段，明确空气质量首时段缺失值策略，
并输出面向推荐系统的地点—小时特征表。产品阈值应集中放入 config，而不是散落在分析代码
中，方便组员评审和后续修改。

## 本次 2026-08-26 快照的主要发现

- Weather 有 5,208 行，即31个 LGA 乘以168小时；没有缺失值、重复时间戳或非一小时
  间隔。Air Quality 有3,720行，即31个 LGA 乘以120小时；时间序列同样连续。
- Air Quality 的 UV、PM2.5、PM10 各有31个缺失值，恰好是每个 LGA 一个时间点，缺失率
  0.833%。这说明它是系统性的边界时段缺失，不宜当作随机缺失直接均值填补。
- Air Quality 的预测网格比 LGA 范围粗，相邻 LGA 可能落入同一预测网格。因此多个 LGA
  的空气质量汇总完全相同并不一定代表真实环境相同，而可能是网格分辨率造成的结果。
- 本次天气均温约在 10.63–12.21°C 之间。最高降水概率达到100%，最大阵风达到
  82.8 km/h；推荐系统不能只看全期平均值，应匹配用户选择的具体小时。
- 温度与体感温度相关系数为0.933，风速与阵风为0.913。两组变量高度相关，但含义不同，
  在给家长解释推荐原因时可以选更易理解的指标，模型内部仍可保留全部字段。
- PM2.5 与 PM10 的相关系数为0.963，说明这次快照中二者变化非常接近。UV 与 PM2.5
  的相关系数为 -0.273，呈
  轻微负相关，但这是单次短期预测快照，不能据此推断稳定规律或因果关系。
