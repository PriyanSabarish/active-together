# Open-Meteo 最终整合说明

运行：

```powershell
python pipeline/integration/build_open_meteo_context.py
```

脚本以 `weather_forecast_clean.csv` 为主表，通过
`site_name + timestamp_utc` 左连接 `air_quality_clean.csv`。使用 UTC 连接可以避免本地时间
和夏令时产生歧义。

输出文件：

```text
data/processed/integrated/hourly_environment_context.csv
```

Weather 的全部预测时段都会保留。Air Quality 预测范围较短时，对应的 UV、PM2.5、PM10
保持为空，并设置 `air_quality_available=false`。脚本不会使用插值伪造空气质量数据。

输出的一行代表一个 LGA 在一个小时的环境条件，并保留 `lga_code`、机器用
`site_name` 和界面用 `display_name`，可供后端根据用户选择的地点和时间进行查询。
字段名称包含单位，例如 `_c`、`_pct`、`_kmh` 和 `_ugm3`，减少前后端对单位的误解。
