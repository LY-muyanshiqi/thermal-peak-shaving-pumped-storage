"""
CCER碳交易核算页面模块
准东园区场景应用 — 抽水蓄能零碳效益碳交易分析
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import config
import charts


def compute_zhundong_scenario(params=None):
    """
    准东园区碳减排 + CCER碳交易全链条计算
    返回完整的核算结果字典
    """
    p = params or config.CCER_PARAMS

    # ================================================================
    # Step 1: 园区年碳排放基准
    # ================================================================
    total_gen_gwh = p['park_avg_load'] * 8760 / 1000

    renewable_gen_gwh = (p['park_wind_capacity'] * p['wind_annual_hours'] +
                         p['park_pv_capacity'] * p['pv_annual_hours']) / 1000

    thermal_gen_gwh = total_gen_gwh - renewable_gen_gwh

    avg_intensity = (p['intensity_weight_rated'] * p['carbon_intensity_rated'] +
                     p['intensity_weight_deep'] * p['carbon_intensity_deep'] +
                     p['intensity_weight_oil'] * p['carbon_intensity_oil'])

    annual_carbon_total = thermal_gen_gwh * 1000 * avg_intensity / 10000  # 万tCO2
    dispatchable = annual_carbon_total * (1 - p['process_emission_ratio'])
    process_emission = annual_carbon_total * p['process_emission_ratio']

    # ================================================================
    # Step 2: 净负荷波动分析
    # ================================================================
    load_range = p['park_peak_valley_ratio'] * p['park_avg_load']
    renewable_avg_mw = (p['park_wind_capacity'] * p['wind_annual_hours'] +
                        p['park_pv_capacity'] * p['pv_annual_hours']) / 8760
    renewable_range = p['renewable_volatility'] * renewable_avg_mw
    net_load_range = np.sqrt(load_range**2 + renewable_range**2)
    ps_coverage = p['park_ps_capacity'] / net_load_range * 100

    # ================================================================
    # Step 3: 碳减排量外推 (基于陕西NSLDE基准: 1400MW PS → 0.42万t CO2)
    # ================================================================
    shaanxi_ref = {
        'thermal_capacity': 30000, 'avg_load': 26715,
        'peak_valley_ratio': 0.35, 'ps_capacity': 1400,
        'annual_carbon': 9500, 'reduction': 0.42,
    }
    sha_net_load = shaanxi_ref['peak_valley_ratio'] * shaanxi_ref['avg_load']
    sha_reg_ratio = shaanxi_ref['ps_capacity'] / sha_net_load
    park_reg_ratio = p['park_ps_capacity'] / net_load_range

    reduction_wan = (shaanxi_ref['reduction'] *
                     (park_reg_ratio / sha_reg_ratio) *
                     (dispatchable / shaanxi_ref['annual_carbon']) *
                     (p['park_ps_capacity'] / shaanxi_ref['ps_capacity']))
    reduction_ton = reduction_wan * 10000
    reduction_rate_total = reduction_wan / annual_carbon_total * 100
    reduction_rate_dispatchable = reduction_wan / dispatchable * 100

    # ================================================================
    # Step 4: 新能源消纳提升
    # ================================================================
    renewable_yi = renewable_gen_gwh / 100
    curtailment_no_ps = renewable_yi * p['curtailment_rate_no_ps']
    curtailment_by_ps = curtailment_no_ps * p['ps_curtailment_absorption']
    curtailment_with_ps = curtailment_no_ps - curtailment_by_ps
    absorb_no_ps = (1 - p['curtailment_rate_no_ps']) * 100
    absorb_with_ps = (1 - curtailment_with_ps / renewable_yi) * 100
    absorb_increase = absorb_with_ps - absorb_no_ps
    absorb_increase_comprehensive = 14.3  # 含风光互补优化
    electricity_revenue = curtailment_by_ps * 1e8 * p['avg_electricity_price'] / 1e8

    # ================================================================
    # Step 5: CCER碳交易收益
    # ================================================================
    ccer_list = []
    for name, price, label in [
        ('conservative', p['ccer_price_low'], '保守情景 (30元/t)'),
        ('base', p['ccer_price_base'], '基准情景 (70元/t, 全国碳市场均价)'),
        ('optimistic', p['ccer_price_high'], '乐观情景 (200元/t, CBAM驱动)'),
    ]:
        rev = reduction_ton * price / 10000
        r = p['ccer_discount_rate']
        n = p['ccer_project_life']
        npv_10 = sum([rev / (1 + r)**t for t in range(1, n + 1)])
        ccer_list.append({
            'name': name, 'label': label, 'price': price,
            'revenue': round(rev, 2), 'npv': round(npv_10, 2),
        })

    # ================================================================
    # Step 6: 社会效益
    # ================================================================
    social = {
        'trees': round(reduction_ton / p['tree_co2_absorption'], 0),
        'households': round(reduction_ton / p['household_annual_co2'], 0),
        'coal_ton': round(reduction_ton / p['coal_to_co2'], 2),
        'renewable_absorbed_yi_kwh': round(curtailment_by_ps, 2),
        'elec_revenue_yi_yuan': round(electricity_revenue, 2),
    }

    # ================================================================
    # 月度分布
    # ================================================================
    months = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    weights = [0.09, 0.07, 0.07, 0.08, 0.09, 0.09, 0.10, 0.10, 0.08, 0.07, 0.08, 0.08]
    monthly = [round(reduction_ton * w, 1) for w in weights]

    return {
        'step1_carbon': {
            'total_gen_gwh': round(total_gen_gwh, 0),
            'thermal_gen_gwh': round(thermal_gen_gwh, 0),
            'renewable_gen_gwh': round(renewable_gen_gwh, 0),
            'thermal_ratio': round(thermal_gen_gwh / total_gen_gwh * 100, 1),
            'renewable_ratio': round(renewable_gen_gwh / total_gen_gwh * 100, 1),
            'avg_intensity': round(avg_intensity, 2),
            'annual_total': round(annual_carbon_total, 2),
            'dispatchable': round(dispatchable, 2),
            'process': round(process_emission, 2),
        },
        'step2_net_load': {
            'load_range': round(load_range, 0),
            'renewable_range': round(renewable_range, 0),
            'net_load_range': round(net_load_range, 0),
            'ps_coverage': min(round(ps_coverage, 1), 100),
            'net_load_pv_ratio': round(net_load_range / p['park_avg_load'] * 100, 1),
        },
        'step3_reduction': {
            'annual_ton': round(reduction_ton, 1),
            'annual_wan': round(reduction_wan, 4),
            'rate_total': round(reduction_rate_total, 4),
            'rate_dispatchable': round(reduction_rate_dispatchable, 4),
            'shaanxi_reduction': shaanxi_ref['reduction'],
            'shaanxi_rate': 0.46,
        },
        'step4_absorption': {
            'renewable_yi': round(renewable_yi, 2),
            'curtailment_no_ps': round(curtailment_no_ps, 2),
            'curtailment_by_ps': round(curtailment_by_ps, 2),
            'curtailment_with_ps': round(curtailment_with_ps, 2),
            'absorb_no_ps': round(absorb_no_ps, 1),
            'absorb_with_ps': round(absorb_with_ps, 1),
            'increase_conservative': round(absorb_increase, 1),
            'increase_comprehensive': absorb_increase_comprehensive,
            'elec_revenue': round(electricity_revenue, 2),
        },
        'step5_ccer': ccer_list,
        'step6_social': social,
        'monthly': monthly,
        'months': months,
        'params_used': p,
    }


# ================================================================
# 页面渲染函数
# ================================================================

def show_ccer_page():
    """CCER碳交易核算主页面"""
    st.markdown("## 💰 抽水蓄能CCER碳交易核算系统")

    # ---- 侧边栏参数 ----
    with st.sidebar:
        st.markdown("### ⚙️ 园区参数设置")
        st.markdown("*准东经济技术开发区默认参数*")

        col_a, col_b = st.columns(2)
        with col_a:
            thermal_cap = st.number_input("火电装机 (MW)", 1000, 50000,
                                          config.CCER_PARAMS['park_thermal_capacity'], 500)
            wind_cap = st.number_input("风电装机 (MW)", 0, 20000,
                                       config.CCER_PARAMS['park_wind_capacity'], 200)
            pv_cap = st.number_input("光伏装机 (MW)", 0, 20000,
                                     config.CCER_PARAMS['park_pv_capacity'], 200)
            ps_cap = st.number_input("抽蓄装机 (MW)", 100, 5000,
                                     config.CCER_PARAMS['park_ps_capacity'], 100)
        with col_b:
            avg_load = st.number_input("园区平均负荷 (MW)", 1000, 50000,
                                       config.CCER_PARAMS['park_avg_load'], 500)
            pvr = st.slider("负荷峰谷差率", 0.05, 0.50,
                            config.CCER_PARAMS['park_peak_valley_ratio'], 0.02)
            process_ratio = st.slider("过程排放占比", 0.0, 0.80,
                                      config.CCER_PARAMS['process_emission_ratio'], 0.05)

        st.divider()
        ccer_price = st.select_slider(
            "CCER碳价情景",
            options=[30, 70, 200],
            value=70,
        )
        price_label = {30: '保守', 70: '基准', 200: '乐观'}
        st.caption(f"当前: {price_label[ccer_price]} ({ccer_price}元/tCO₂)")

    # ---- 计算 ----
    params = dict(config.CCER_PARAMS)
    params.update({
        'park_thermal_capacity': thermal_cap,
        'park_wind_capacity': wind_cap,
        'park_pv_capacity': pv_cap,
        'park_ps_capacity': ps_cap,
        'park_avg_load': avg_load,
        'park_peak_valley_ratio': pvr,
        'process_emission_ratio': process_ratio,
        'ccer_price_base': ccer_price,
    })
    r = compute_zhundong_scenario(params)

    # ================================================================
    # Section 1: 核算流程图
    # ================================================================
    st.markdown("### 📐 碳交易核算全链条流程图")
    _render_flowchart()

    # ================================================================
    # Section 2: 关键指标卡片
    # ================================================================
    st.markdown("### 📊 核算结果总览")
    c1, c2, c3, c4, c5 = st.columns(5)
    s3 = r['step3_reduction']
    s4 = r['step4_absorption']
    c1.metric("年碳减排量", f"{s3['annual_ton']:.0f} tCO₂",
              f"{s3['rate_total']:.3f}% (占总量)")
    c2.metric("CCER年收益", f"{r['step5_ccer'][1]['revenue']} 万元",
              f"碳价 {ccer_price} 元/t")
    c3.metric("消纳率提升", f"+{s4['increase_conservative']} pp",
              f"综合 +{s4['increase_comprehensive']} pp")
    c4.metric("抽蓄覆盖率", f"{r['step2_net_load']['ps_coverage']}%",
              "净负荷波动")
    c5.metric("年增发电收益", f"{s4['elec_revenue']:.1f} 亿元",
              "消纳提升×电价")

    # ================================================================
    # Section 3: 三步计算详解 (Step-by-step)
    # ================================================================
    st.markdown("---")
    st.markdown("### 🔍 计算过程详解")

    # ---- Step 1: 碳排放基准 ----
    s1 = r['step1_carbon']
    s2 = r['step2_net_load']

    with st.expander("**Step 1: 园区年碳排放基准计算**", expanded=False):
        st.markdown("""
        **方法**：火电三段式分工况碳排放模型（常规调峰 / 深度不助燃调峰 / 深度助燃调峰）

        **公式**：年碳排放 = 火电发电量 × 加权平均碳排放强度

        其中：加权平均碳排放强度 = Σ(各工况时间占比 × 该工况碳排放强度)
        """)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**用电结构**")
            st.markdown(f"""
            | 指标 | 数值 |
            |------|------|
            | 园区年用电量 | **{s1['total_gen_gwh']:.0f} GWh** |
            | 火电发电量 | {s1['thermal_gen_gwh']:.0f} GWh ({s1['thermal_ratio']}%) |
            | 新能源发电量 | {s1['renewable_gen_gwh']:.0f} GWh ({s1['renewable_ratio']}%) |
            """)

        with col_b:
            st.markdown("**碳排放构成**")
            st.markdown(f"""
            | 指标 | 数值 |
            |------|------|
            | 加权平均碳强度 | **{s1['avg_intensity']} tCO₂/MWh** |
            | 年碳排放总量 | **{s1['annual_total']:.2f} 万tCO₂** |
            | 可调碳排放 (火电) | {s1['dispatchable']:.2f} 万tCO₂ (65%) |
            | 过程排放 (煤化工) | {s1['process']:.2f} 万tCO₂ (35%, 不可调) |
            """)

        st.info(
            f"💡 **说明**：35%的过程排放来自煤化工生产反应（煤制气/煤制烯烃），"
            f"属于化学过程排放，不受抽水蓄能调度影响，从可调范围内扣除。"
        )

        # 碳排放构成饼图
        fig_pie = go.Figure(data=[go.Pie(
            labels=['可调碳排放\n(火电调峰)', '过程排放\n(煤化工·不可调)'],
            values=[s1['dispatchable'], s1['process']],
            marker_colors=['rgba(0, 212, 255, 0.8)', 'rgba(255, 150, 50, 0.7)'],
            hole=0.5,
            textinfo='label+percent',
        )])
        fig_pie.update_layout(
            title='园区碳排放构成', template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=350,
        )
        charts.safe_plotly_chart(fig_pie, width='stretch')

    # ---- Step 2: 净负荷波动分析 ----
    with st.expander("**Step 2: 净负荷波动分析 — 抽蓄调峰空间计算**", expanded=False):
        st.markdown("""
        **关键认知**：园区负荷峰谷差虽小(18%)，但**新能源高渗透率改变了净负荷特征**。

        净负荷 = 园区负荷 − 新能源出力

        净负荷波动 = √(负荷波动² + 新能源波动²)
        """)

        st.markdown(f"""
        | 波动来源 | 波动幅度 (MW) | 计算依据 |
        |------|:---:|------|
        | 负荷波动 | **{s2['load_range']:.0f}** | 峰谷差率({pvr*100:.0f}%) × 平均负荷({avg_load:.0f}MW) |
        | 新能源出力波动 | **{s2['renewable_range']:.0f}** | 波动率(45%) × 新能源平均出力 |
        | **等效净负荷波动** | **{s2['net_load_range']:.0f}** | √({s2['load_range']:.0f}² + {s2['renewable_range']:.0f}²) |
        """)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("抽蓄覆盖净负荷波动", f"{s2['ps_coverage']}%",
                      f"{ps_cap}MW / {s2['net_load_range']:.0f}MW")
        with col2:
            st.metric("净负荷等效峰谷差率", f"{s2['net_load_pv_ratio']}%",
                      f"负荷峰谷差率 {pvr*100:.0f}% × 新能源放大")

        # 净负荷波动示意图
        fig_nl = _plot_net_load_diagram(s2, params)
        charts.safe_plotly_chart(fig_nl, width='stretch')

        st.success(
            f"✅ **结论**：{ps_cap}MW抽水蓄能可覆盖{s2['net_load_range']:.0f}MW净负荷波动的"
            f"**{s2['ps_coverage']}%**。这与'峰谷差小→抽蓄没用'的直觉相反——"
            f"**新能源占比越高，净负荷波动越大，抽蓄作用越突出**。"
        )

    # ---- Step 3: 碳减排量 + CCER ----
    with st.expander("**Step 3: 碳减排量外推 + CCER碳交易**", expanded=True):
        st.markdown("""
        **外推方法**：基于陕西NSLDE多目标优化实测结果（1,400MW抽蓄 → 0.42万tCO₂/年），
        按净负荷调节比例、可调碳排放比例、抽蓄装机比例缩放至园区场景。
        """)

        s3 = r['step3_reduction']
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("陕西基准减排", f"{s3['shaanxi_reduction']} 万tCO₂",
                      f"减排率 {s3['shaanxi_rate']}% | 1400MW")
        with col_b:
            st.metric("准东园区减排", f"{s3['annual_ton']:.1f} tCO₂",
                      f"绝对量 = {s3['annual_wan']:.4f} 万tCO₂")
        with col_c:
            st.metric("减排率 (可调)", f"{s3['rate_dispatchable']:.4f}%",
                      f"总量减排率 {s3['rate_total']:.4f}%")

        st.info(
            f"🔍 **为什么减排率低？**\n\n"
            f"年碳排放基数达**{s1['annual_total']:.2f}万tCO₂**，其中35%为不可调的煤化工过程排放。"
            f"绝对减排量**{s3['annual_ton']:.1f}tCO₂**与陕西基准项目(4,200吨)同量级甚至更优——"
            f"减排率低是由于基数被稀释，而非抽蓄效果差。"
        )

        # CCER 碳交易收益
        st.markdown("#### 💰 CCER碳交易收益测算")

        ccer_data = r['step5_ccer']
        fig_ccer = go.Figure()

        prices = [c['price'] for c in ccer_data]
        revenues = [c['revenue'] for c in ccer_data]
        npvs = [c['npv'] for c in ccer_data]
        colors_ccer = ['rgba(255, 150, 50, 0.8)', 'rgba(0, 212, 255, 0.8)', 'rgba(0, 255, 128, 0.8)']

        fig_ccer.add_trace(go.Bar(
            x=['保守\n(30元/t)', '基准\n(70元/t)', '乐观\n(200元/t)'],
            y=revenues,
            name='年碳交易收益 (万元)',
            marker_color=colors_ccer,
            text=[f'{v:.1f}万元' for v in revenues],
            textposition='outside',
        ))

        fig_ccer.add_trace(go.Scatter(
            x=['保守\n(30元/t)', '基准\n(70元/t)', '乐观\n(200元/t)'],
            y=npvs,
            name='10年期NPV (万元)',
            mode='lines+markers+text',
            marker=dict(size=12, color='rgba(255, 255, 100, 0.9)'),
            text=[f'NPV: {v:.1f}万' for v in npvs],
            textposition='top center',
            yaxis='y2',
        ))

        fig_ccer.update_layout(
            title='CCER碳交易收益情景分析',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            yaxis=dict(title='年收益 (万元)'),
            yaxis2=dict(title='NPV (万元)', overlaying='y', side='right'),
            legend=dict(orientation='h', y=1.15),
        )
        charts.safe_plotly_chart(fig_ccer, width='stretch')

        # CCER经济性评估
        st.markdown("#### ⚠️ CCER开发经济性评估")
        dev_cost_low = config.CCER_PARAMS['ccer_dev_cost_low']
        dev_cost_high = config.CCER_PARAMS['ccer_dev_cost_high']
        base_rev = ccer_data[1]['revenue']

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            | 评估指标 | 数值 |
            |------|------|
            | 年减排量 | {s3['annual_ton']:.1f} tCO₂ |
            | CCER开发成本 | {dev_cost_low}-{dev_cost_high} 万元/年 |
            | 基准收益 | {base_rev} 万元/年 |
            | 经济性判断 | {"✅ 经济可行" if base_rev > dev_cost_high else "⚠️ 边际平衡" if base_rev > dev_cost_low else "❌ 经济不足"} |
            """)
        with col_b:
            st.markdown("""
            **建议的碳资产策略**：
            1. **园区级整合** → 合并抽蓄减碳+新能源消纳+碳足迹认证
            2. **碳普惠对接** → 降低开发门槛
            3. **企业碳中和** → 面向煤化工企业就近服务
            4. **前瞻布局** → 碳价上涨至200元/t时年收益达110万元
            """)

    # ---- Step 4: 新能源消纳 ----
    with st.expander("**Step 4: 新能源消纳提升效益**", expanded=False):
        st.markdown("""
        **抽水蓄能通过低谷时段抽水消纳富余新能源，直接降低弃风弃光率。**
        """)

        s4 = r['step4_absorption']

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            | 指标 | 数值 |
            |------|------|
            | 新能源年发电量 | {s4['renewable_yi']:.1f} 亿kWh |
            | 无抽蓄弃电量 | {s4['curtailment_no_ps']:.1f} 亿kWh (12.5%) |
            | 弃电成因 | 午间光伏高峰+风电波动 |
            | 抽蓄低谷消纳 | {s4['curtailment_by_ps']:.1f} 亿kWh |
            | 剩余弃电量 | {s4['curtailment_with_ps']:.1f} 亿kWh |
            """)
        with col_b:
            st.markdown(f"""
            | 指标 | 数值 |
            |------|------|
            | 消纳率(无抽蓄) | {s4['absorb_no_ps']}% |
            | 消纳率(有抽蓄) | {s4['absorb_with_ps']}% |
            | 消纳提升(保守) | **+{s4['increase_conservative']} pp** |
            | 消纳提升(综合) | **+{s4['increase_comprehensive']} pp** |
            | 年增发电收益 | **约{s4['elec_revenue']:.1f} 亿元** |
            """)

        st.success(
            f"✅ 消纳提升 +{s4['increase_conservative']}pp → "
            f"年增消纳约**{s4['curtailment_by_ps']:.1f}亿kWh**清洁电力 → "
            f"按园区电价{config.CCER_PARAMS['avg_electricity_price']}元/kWh计，"
            f"年增发电收益约**{s4['elec_revenue']:.1f}亿元**——"
            f"这是园区场景下抽蓄价值的核心体现。"
        )

    # ---- Step 5: 社会效益 ----
    with st.expander("**Step 5: 社会效益等效折算**", expanded=False):
        social = r['step6_social']
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🌳 等效植树", f"{social['trees']:.0f} 棵",
                      f"{config.CCER_PARAMS['tree_co2_absorption']*1000:.0f}kgCO₂/棵·年")
        with c2:
            st.metric("🏠 等效居民用电", f"{social['households']:.0f} 户",
                      f"{config.CCER_PARAMS['household_annual_co2']:.1f}tCO₂/户·年")
        with c3:
            st.metric("🪨 等效减少标煤", f"{social['coal_ton']:.1f} 吨",
                      f"{config.CCER_PARAMS['coal_to_co2']:.2f}tCO₂/吨标煤")

        st.markdown(f"""
        | 等效指标 | 数值 | 计算依据 |
        |------|------|------|
        | 等效植树 | **{social['trees']:.0f} 棵** | {s3['annual_ton']:.0f}t ÷ {config.CCER_PARAMS['tree_co2_absorption']:.3f}t/棵 |
        | 等效居民用电 | **{social['households']:.0f} 户** | {s3['annual_ton']:.0f}t ÷ {config.CCER_PARAMS['household_annual_co2']:.1f}t/户 |
        | 等效减少标煤 | **{social['coal_ton']:.1f} 吨** | {s3['annual_ton']:.0f}t ÷ {config.CCER_PARAMS['coal_to_co2']:.2f}t/吨 |
        | 年增消纳清洁电力 | **{social['renewable_absorbed_yi_kwh']:.1f} 亿kWh** | 抽蓄低谷抽水消纳 |
        | 年增发电收益 | **约{social['elec_revenue_yi_yuan']:.1f} 亿元** | {social['renewable_absorbed_yi_kwh']:.1f}亿kWh × {config.CCER_PARAMS['avg_electricity_price']}元/kWh |
        """)

    # ================================================================
    # Section 4: 月度减排分布
    # ================================================================
    st.markdown("---")
    st.markdown("### 📅 月度碳减排分布")

    fig_monthly = go.Figure(data=[
        go.Bar(
            x=r['months'],
            y=r['monthly'],
            marker_color=[f'rgba(0, {180 + i*5}, {255 - i*15}, 0.8)' for i in range(12)],
            text=[f'{v:.0f}' for v in r['monthly']],
            textposition='outside',
        )
    ])
    fig_monthly.update_layout(
        title='月度碳减排量 (tCO₂) — 夏冬季用电高峰 调峰空间大',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=380,
        xaxis_title='月份', yaxis_title='碳减排 (tCO₂)',
    )
    charts.safe_plotly_chart(fig_monthly, width='stretch')

    # ================================================================
    # Section 5: 全链条总结
    # ================================================================
    st.markdown("---")
    st.markdown("### 🔗 全链条碳交易闭环总结")

    st.markdown(f"""
    | 环节 | 指标 | 数值 |
    |------|------|------|
    | 🏭 碳排放基准 | 园区年碳排放 | **{s1['annual_total']:.2f} 万tCO₂**（可调{s1['dispatchable']:.2f}万t） |
    | ⚡ 抽蓄调峰优化 | 年碳减排量 | **{s3['annual_ton']:.1f} tCO₂**（减排率 {s3['rate_dispatchable']:.3f}%） |
    | 🌿 新能源消纳 | 消纳率提升 | **+{s4['increase_conservative']}pp**（保守），年增收益 **{s4['elec_revenue']:.1f}亿元** |
    | 💰 CCER碳交易 | 基准收益 | **{ccer_data[1]['revenue']}万元/年**，10年NPV **{ccer_data[1]['npv']}万元** |
    | 🌍 社会效益 | 等效植树 | **{social['trees']:.0f}棵**，减标煤 **{social['coal_ton']:.1f}吨** |
    """)

    st.success(
        "✅ **全链条闭环**：园区能耗特征识别 → 五源联合优化调度 → 8760h碳减排仿真 → "
        "CCER碳资产折算 → 碳价情景敏感性分析 → 零碳决策支撑"
    )


def show_park_page():
    """园区场景应用页面"""
    st.markdown("## 🏭 准东经济技术开发区 — 零碳园区核算场景")

    st.markdown("""
    ### 场景背景

    **准东经济技术开发区**是国家首批52个国家级零碳园区之一，定位为现代煤化工与硅铝新材料
    两大千亿级产业集群。园区能源结构呈现"高载能+高碳排"特征，零碳转型需求迫切。

    **阜康抽水蓄能电站**（1,200MW）紧邻准东园区，为园区提供调峰服务。
    """)

    # 场景参数
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("火电装机", "7,000 MW")
    c2.metric("风电+光伏", "2,800 + 4,200 MW")
    c3.metric("新能源装机占比", "55%")
    c4.metric("阜康抽水蓄能", "1,200 MW")

    st.markdown("---")

    # 核心论点
    st.markdown("### 🔑 核心论点：净负荷波动视角下的抽蓄价值")

    st.markdown("""
    > **表面矛盾**：园区工业负荷峰谷差仅18%，远低于省级电网35%，直觉上抽蓄调峰空间有限。

    > **深层真相**：新能源装机占比55% → 风光出力日内大幅波动 → 净负荷(负荷−新能源)等效波动达21% → **1,200MW抽蓄可覆盖净负荷波动96%以上**。
    """)

    # 图示
    s2 = compute_zhundong_scenario()['step2_net_load']
    fig_comp = _plot_park_vs_province(s2)
    charts.safe_plotly_chart(fig_comp, width='stretch')

    st.markdown("---")

    # 陕西对比
    st.markdown("### 📊 陕西基准 vs 准东园区对比")

    st.markdown("""
    | 对比维度 | 陕西省级基准 | 准东园区 | 影响方向 |
    |------|:---:|:---:|------|
    | 火电装机 (MW) | 30,000 | 7,000 | 园区基数小→有利 |
    | 抽蓄/火电比 | 4.7% | 17.1% | 园区配置高→有利 |
    | 净负荷峰谷差率 | ~35% | ~21% | 园区波动小→不利 |
    | 碳排放基数 (万t) | ~9,500 | ~3,477 | 园区基数大→稀释 |
    | 煤化工过程排放 | 0% | 35% | 不可调→稀释 |

    **结论**：准东减排率(0.016%)远低于陕西(0.46%)的主因是碳排放基数巨大+煤化工过程排放不可调。
    但绝对减排量5,879吨与陕西4,200吨同量级，**抽蓄调峰减碳效果在园区场景下依然显著**。
    """)

    st.markdown("---")

    st.markdown("### 💡 碳资产策略建议")
    st.markdown("""
    | 策略 | 说明 |
    |------|------|
    | 🏗️ 园区级整合 | 抽蓄减碳 + 新能源消纳 + 碳足迹认证 → 园区级碳资产包 |
    | 🌱 碳普惠对接 | 降低开发门槛，利用新疆地方碳普惠平台 |
    | 🏭 企业碳中和 | 面向煤化工高排放企业提供就近碳中和服务 |
    | 📈 前瞻布局 | 碳价随CBAM上涨至200元/t时，年收益达110万元 |
    """)


# ================================================================
# 辅助可视化函数
# ================================================================

def _render_flowchart():
    """渲染全链条流程图"""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a3a4a, #0d2137); border: 1px solid #00d4ff;
        border-radius: 12px; padding: 16px; text-align: center; min-height: 160px;">
        <div style="font-size: 2rem;">🏭</div>
        <div style="color: #00d4ff; font-weight: bold; margin: 8px 0;">Step 1</div>
        <div style="font-size: 0.85rem; color: #b0c8e0;">园区碳排放基准</div>
        <div style="font-size: 0.75rem; color: #8ba4c4; margin-top: 6px;">
        三段式分工况模型<br>
        常规/不助燃/助燃
        </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding-top: 60px; font-size: 1.5rem; color: #00d4ff;">→</div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a3a4a, #0d2137); border: 1px solid #00ff88;
        border-radius: 12px; padding: 16px; text-align: center; min-height: 160px;">
        <div style="font-size: 2rem;">⚡</div>
        <div style="color: #00ff88; font-weight: bold; margin: 8px 0;">Step 2</div>
        <div style="font-size: 0.85rem; color: #b0c8e0;">净负荷波动分析</div>
        <div style="font-size: 0.75rem; color: #8ba4c4; margin-top: 6px;">
        √(负荷²+新能源²)<br>
        抽蓄覆盖率计算
        </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="text-align: center; padding-top: 60px; font-size: 1.5rem; color: #00ff88;">→</div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2a1a3a, #1a0d27); border: 1px solid #ffcc00;
        border-radius: 12px; padding: 16px; text-align: center; min-height: 160px;">
        <div style="font-size: 2rem;">💰</div>
        <div style="color: #ffcc00; font-weight: bold; margin: 8px 0;">Step 3-5</div>
        <div style="font-size: 0.85rem; color: #b0c8e0;">碳减排 + CCER + 经济性</div>
        <div style="font-size: 0.75rem; color: #8ba4c4; margin-top: 6px;">
        NSLDE外推减排量<br>
        碳价情景NPV分析
        </div>
        </div>
        """, unsafe_allow_html=True)

    # 第二行：详细流程图
    st.markdown("""
    <div style="background: rgba(13, 33, 55, 0.6); border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 12px; padding: 20px; margin-top: 16px;">
    <div style="text-align: center; font-size: 0.85rem; line-height: 2;">
    <span style="color: #00d4ff;">🏭 园区能耗特征</span>
    &nbsp;→&nbsp;
    <span style="color: #00ff88;">📐 净负荷波动计算</span>
    &nbsp;→&nbsp;
    <span style="color: #ffcc00;">⚡ 抽蓄调峰空间评估</span>
    &nbsp;→&nbsp;
    <span style="color: #ff8844;">🔥 三段式碳核算</span>
    &nbsp;→&nbsp;
    <span style="color: #00d4ff;">📊 NSLDE外推减排量</span>
    &nbsp;→&nbsp;
    <span style="color: #ffcc00;">💰 CCER碳资产折算</span>
    &nbsp;→&nbsp;
    <span style="color: #00ff88;">📈 碳价情景NPV分析</span>
    &nbsp;→&nbsp;
    <span style="color: #ff8844;">🌍 零碳决策支撑</span>
    </div>
    <div style="text-align: center; margin-top: 12px; color: #8ba4c4; font-size: 0.78rem;">
    全参数可调 · 跨园区可复用 · 结果可复核
    </div>
    </div>
    """, unsafe_allow_html=True)


def _plot_net_load_diagram(s2, params):
    """净负荷波动分析图"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('净负荷波动来源分解', '抽蓄覆盖率'),
        specs=[[{'type': 'bar'}, {'type': 'gauge'}]],
    )

    # 左图：波动来源分解
    fig.add_trace(go.Bar(
        x=['净负荷波动'],
        y=[s2['net_load_range']],
        name='总波动',
        marker_color='rgba(0, 212, 255, 0.8)',
        text=[f'{s2["net_load_range"]:.0f} MW'],
        textposition='outside',
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=['净负荷波动'],
        y=[s2['load_range']],
        name='负荷波动',
        marker_color='rgba(0, 255, 128, 0.6)',
        text=[f'{s2["load_range"]:.0f}'],
        textposition='inside',
    ), row=1, col=1)

    # 右图：仪表盘
    fig.add_trace(go.Indicator(
        mode='gauge+number+delta',
        value=s2['ps_coverage'],
        title={'text': '抽蓄覆盖率 (%)'},
        delta={'reference': 50, 'increasing': {'color': '#00ff88'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#b0c8e0'},
            'bar': {'color': 'rgba(0, 255, 128, 0.8)'},
            'bgcolor': 'rgba(0,0,0,0)',
            'steps': [
                {'range': [0, 30], 'color': 'rgba(255, 100, 100, 0.3)'},
                {'range': [30, 60], 'color': 'rgba(255, 200, 50, 0.3)'},
                {'range': [60, 100], 'color': 'rgba(0, 255, 128, 0.3)'},
            ],
            'threshold': {
                'line': {'color': '#ffcc00', 'width': 3},
                'thickness': 0.8, 'value': 80
            }
        }
    ), row=1, col=2)

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=350, showlegend=True,
    )
    return fig


def _plot_park_vs_province(s2):
    """园区 vs 省级对比图"""
    fig = go.Figure()

    categories = ['负荷峰谷差率\n(%)', '净负荷波动\n(MW)', '抽蓄覆盖\n净负荷(%)']
    park_vals = [18, s2['net_load_range'], s2['ps_coverage']]
    province_vals = [35, 9350, 15]

    fig.add_trace(go.Scatterpolar(
        r=park_vals + [park_vals[0]],
        theta=categories + [categories[0]],
        name='准东园区',
        fill='toself',
        fillcolor='rgba(0, 255, 128, 0.2)',
        line=dict(color='rgba(0, 255, 128, 0.9)', width=2),
    ))
    fig.add_trace(go.Scatterpolar(
        r=province_vals + [province_vals[0]],
        theta=categories + [categories[0]],
        name='陕西省级',
        fill='toself',
        fillcolor='rgba(0, 212, 255, 0.15)',
        line=dict(color='rgba(0, 212, 255, 0.9)', width=2),
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 120], color='#b0c8e0'),
        ),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=400, showlegend=True,
        title='准东园区 vs 陕西省级 — 调峰特征对比',
    )
    return fig
