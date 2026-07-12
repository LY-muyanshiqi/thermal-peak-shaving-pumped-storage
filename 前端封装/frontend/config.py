"""
集中配置模块 — 参数预设、默认值、页面定义
火电深度调峰+抽水蓄能减碳效益优化系统
"""

# ---- 参数预设方案 ----
PRESETS = {
    "\U0001f3f7️ 自定义（手动调整）": None,
    "\U0001f4cb 默认方案": {
        'zpump': 1400, 'h_val': 4, 'efficiency_val': 0.75, 'min_power': 0.2,
        'carbon_factor': 0.5, 'coal_high': 300, 'coal_mid': 330, 'coal_low': 370,
    },
    "\U0001f33f 高消纳方案": {
        'zpump': 2000, 'h_val': 5, 'efficiency_val': 0.85, 'min_power': 0.15,
        'carbon_factor': 0.4, 'coal_high': 290, 'coal_mid': 320, 'coal_low': 360,
    },
    "\U0001f30d 深度低碳方案": {
        'zpump': 1600, 'h_val': 4, 'efficiency_val': 0.8, 'min_power': 0.15,
        'carbon_factor': 0.35, 'coal_high': 285, 'coal_mid': 315, 'coal_low': 355,
    },
    "⚡ 灵活调峰方案": {
        'zpump': 2500, 'h_val': 3, 'efficiency_val': 0.7, 'min_power': 0.25,
        'carbon_factor': 0.55, 'coal_high': 300, 'coal_mid': 330, 'coal_low': 380,
    },
}

# ---- 默认参数 ----
DEFAULT_PARAMS = {
    'zpump': 1400, 'h_val': 4, 'efficiency_val': 0.75, 'min_power': 0.2,
    'carbon_factor': 0.5, 'coal_high': 300, 'coal_mid': 330, 'coal_low': 370,
    'custom_params': None, 'recalculated_result': None, 'view_mode': '全年总览',
    '_last_preset': '\U0001f3f7️ 自定义（手动调整）',
    'preset_select': '\U0001f3f7️ 自定义（手动调整）',
}

# ---- CCER碳交易参数 ----
CCER_PARAMS = {
    # 准东园区默认参数
    'park_thermal_capacity': 7000,       # 火电装机 MW
    'park_wind_capacity': 2800,          # 风电装机 MW
    'park_pv_capacity': 4200,            # 光伏装机 MW
    'park_avg_load': 5933,               # 平均负荷 MW
    'park_peak_valley_ratio': 0.18,      # 峰谷差率
    'park_ps_capacity': 1200,            # 抽蓄装机 MW (阜康)
    'wind_annual_hours': 2200,           # 风电年利用小时
    'pv_annual_hours': 1200,             # 光伏年利用小时
    'process_emission_ratio': 0.35,      # 煤化工过程排放占比

    # 碳排放强度 tCO2/MWh
    'carbon_intensity_rated': 0.80,
    'carbon_intensity_deep': 0.92,
    'carbon_intensity_oil': 1.05,
    'intensity_weight_rated': 0.50,      # 额定工况时间占比
    'intensity_weight_deep': 0.30,       # 深度不助燃占比
    'intensity_weight_oil': 0.20,        # 深度助燃占比

    # CCER
    'ccer_price_low': 30,
    'ccer_price_base': 70,
    'ccer_price_high': 200,
    'ccer_discount_rate': 0.05,          # NPV折现率
    'ccer_project_life': 10,             # 项目寿命 年
    'ccer_dev_cost_low': 30,             # CCER开发成本 万元/年
    'ccer_dev_cost_high': 50,

    # 经济
    'avg_electricity_price': 0.35,       # 园区平均电价 元/kWh

    # 新能源
    'renewable_volatility': 0.45,        # 新能源出力波动率
    'curtailment_rate_no_ps': 0.125,     # 无抽蓄弃电率
    'ps_curtailment_absorption': 0.875,  # 抽蓄消纳弃电比例

    # 社会效益折算系数
    'tree_co2_absorption': 0.018,        # 单棵树年固碳 tCO2
    'household_annual_co2': 2.5,         # 户均年碳排放 tCO2
    'coal_to_co2': 2.78,                 # 吨标煤->tCO2
}

# ---- 页面分组导航 ----
PAGE_GROUPS = {
    "\U0001f4ca 核心看板": ["\U0001f3e0 系统总览", "\U0001f4c8 综合分析报告"],
    "\U0001f4c8 专项分析": ["\U0001f33f 新能源分析", "\U0001f4a7 抽水蓄能调度",
                        "\U0001f525 火电调峰与碳减排", "\U0001f3af Pareto前沿分析"],
    "\U0001f4b0 CCER碳交易": ["\U0001f4b0 碳交易核算", "\U0001f3ed 园区场景应用"],
    "⚙️ 模型与参数": ["\U0001f4d0 计算公式详解", "⚙️ 参数调整",
                         "\U0001f5c3️ 原始数据浏览"],
    "\U0001f52c 高级功能": ["\U0001f3a8 高级可视化", "\U0001f9e0 高级分析", "\U0001f52c A/B参数对比"],
}
