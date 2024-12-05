import pandas as pd
import pyecharts.options as opts
from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line,HeatMap,Scatter
import pandas_ta as ta
from utils.indicators import calculate_ema


def _split_data(df: pd.DataFrame):
    x_data = df.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
    y_data = df[["open", "close", "low", "high"]].values.tolist()
    df_close = df["close"]

    # 成交量相关
    df_remake =df.reset_index(drop=True)
    df_remake["index"] = df_remake.index
    df_remake["rise"] = df_remake[["open", "close"]].apply(lambda x: 1 if x[0] > x[1] else -1, axis=1)
    y_vol = df_remake[["index", "volume", "rise"]].values.tolist()
    #print("成交量数据： ",y_vol)

    # 主力合约热力图相关
    # 索引重置并转为date格式，方便统计
    res = df.reset_index()
    res["index"] = pd.to_datetime(res["index"]).dt.date
    # 按日期和合约品种计数,按索引排序（默认按值排序）,并转为list输出
    count_df = res[['index', 'code']].value_counts(sort=False).sort_index().reset_index()
    hm_data = count_df.values.tolist()
    hm_x_data = count_df['index'].tolist()
    hm_y_data = count_df['code'].unique().tolist()

    return x_data, y_data, df_close, y_vol, hm_data, hm_x_data, hm_y_data

def _split_result(df: pd.DataFrame):
    result_datatime = df.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
    open = df.query("策略触发类型=='开仓'")["成交价"]
    re_open = df.query("策略触发类型=='反向开仓'")["成交价"]
    stop = df.query("策略触发类型=='止盈'")["成交价"]
    cover = df.query("策略触发类型=='补仓'")["成交价"]
    #cover_res = df.query("策略触发类型=='补仓'")["成交价"].values.tolist()
    t0=df["成交价"]
    t3 = pd.concat(
        [t0, open,re_open,stop,cover],
        axis=1,
        ignore_index=False)
    t3.columns=['成交价','开仓','反向开仓','止盈','补仓']
    open_res = t3['开仓'].values.tolist()
    re_open_res= t3['反向开仓'].values.tolist()
    stop_res= t3['止盈'].values.tolist()
    cover_res= t3['补仓'].values.tolist()
    return result_datatime,open_res,re_open_res,stop_res,cover_res
def draw_pro_kline_fut(period,ema_params,future_df,result_df):
    """
    Args:
        period (str): 行情间隔
        ema_params (dict): ema的参数
        future_df (dataframe): 行情数据
        result_df (dataframe): 交易及ema数据
    """
    x_data, y_data, df_close, y_vol, hm_data, hm_x_data, hm_y_data = _split_data(future_df)
    x_Scatter,open_res,re_open_res,stop_res,cover_res = _split_result(result_df)

    # https://blog.csdn.net/qq_57099024/article/details/122030069
    kline = (
        Kline()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name=period,
            y_axis=y_data,
            itemstyle_opts=opts.ItemStyleOpts(color="#ec0000", color0="#00da3c"),
        )
        .set_global_opts(
            # 图例配置项
            legend_opts=opts.LegendOpts(
                is_show=True, pos_bottom=10, pos_left="center"
            ),
            # 区域缩放组件
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False,
                    type_="inside",
                    xaxis_index=[0, 1],
                    range_start=0,
                    range_end=2,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0, 1],
                    type_="slider",
                    pos_top="85%",
                    range_start=0,
                    range_end=2,
                ),
            ],
            # 坐标轴配置
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            # 提示浮框层设置
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(245, 245, 245, 0.8)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
            # 视觉映射层设置
            visualmap_opts=opts.VisualMapOpts(
                is_show=False,
                dimension=2,
                series_index=9,
                is_piecewise=True,
                pieces=[
                    {"value": 1, "color": "#00da3c"},
                    {"value": -1, "color": "#ec0000"},
                ],
            ),
            # 坐标轴指示器设置
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
            # 区域选择组件
            brush_opts=opts.BrushOpts(
                x_axis_index="all",
                brush_link="all",
                out_of_brush={"colorAlpha": 0.1},
                brush_type="lineX",
            ),
        )
    )

    ema_line_1 = (
        Line()
        #.add_xaxis(xaxis_data=x_data[ema_params["ema1"]:])
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="EMA" + str(ema_params["ema1"]),
            y_axis=calculate_ema(day_count=ema_params["ema1"], close=df_close),
            # 是否平滑显示
            is_smooth=True,
            # 是否开启hover在拐点上的提示动画效果
            is_hover_animation=False,
            # width:线宽，opacity: 透明度
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            itemstyle_opts=opts.ItemStyleOpts(color='yellow'),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
    )
    ema_line_2 = (
        Line()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="EMA" + str(ema_params["ema2"]),
            y_axis=calculate_ema(day_count=ema_params["ema2"], close=df_close),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color='green'),
        )

    )
    ema_line_3 = (
        Line()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="EMA" + str(ema_params["ema3"]),
            y_axis=calculate_ema(day_count=ema_params["ema3"], close=df_close),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color='purple'),
        )

    )
    ema_line_4 = (
        Line()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="EMA" + str(ema_params["ema4"]),
            y_axis=calculate_ema(day_count=ema_params["ema4"], close=df_close),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color='blue'),
        )

    )
    # 成交量柱状图
    bar = (
        Bar()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="Volume",
            y_axis=y_vol,
            xaxis_index=1,
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                grid_index=1,
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                split_number=20,
                min_="dataMin",
                max_="dataMax",
            ),
            yaxis_opts=opts.AxisOpts(
                grid_index=1,
                is_scale=True,
                split_number=2,
                axislabel_opts=opts.LabelOpts(is_show=False),
                axisline_opts=opts.AxisLineOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )

    open_scatter = (
        Scatter()
        .add_xaxis(xaxis_data=x_Scatter)
        .add_yaxis(
            series_name= "开仓",
            y_axis=open_res,
            symbol_size=15,
            symbol='triangle',
            itemstyle_opts=opts.ItemStyleOpts(color='orange')
            )
        .add_yaxis(
            series_name="反向开仓",
            y_axis=re_open_res,
            symbol_size=15,
            symbol='triangle',
            itemstyle_opts=opts.ItemStyleOpts(color='black')
        )
        .add_yaxis(
            series_name="止盈",
            y_axis=stop_res,
            symbol_size=15,
            symbol='triangle',
            itemstyle_opts=opts.ItemStyleOpts(color='blue')
        )
        .add_yaxis(
            series_name="补仓",
            y_axis=cover_res,
            symbol_size=15,
            symbol='circle',
            itemstyle_opts=opts.ItemStyleOpts(color='purple')
        )
        # 禁止展示金额
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        # 禁止展示图例
        .set_global_opts(legend_opts=opts.LegendOpts(is_show=True))
    )



    # Kline And Line

    overlap_kline_line = kline.overlap(ema_line_1)
    overlap_kline_line = overlap_kline_line.overlap(ema_line_2)
    overlap_kline_line = overlap_kline_line.overlap(ema_line_3)
    overlap_kline_line = overlap_kline_line.overlap(ema_line_4)
    overlap_kline_line = overlap_kline_line.overlap(open_scatter)


    # Grid Overlap + Bar

    grid_chart = Grid(
        init_opts=opts.InitOpts(
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )

    grid_chart.add(
        overlap_kline_line,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="50%"),
    )

    grid_chart.add(
        bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="63%",height="20%"
        ),
    )


    grid_chart_position = Grid(
        init_opts=opts.InitOpts(
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )


    # hm_data, hm_x_data, hm_y_data
    position = (
        HeatMap()
        .add_xaxis(xaxis_data=hm_x_data)
        .add_yaxis("",
                   hm_y_data,
                   hm_data,
                   label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="主力合约分布月份热力图"),
            visualmap_opts=opts.VisualMapOpts(),

        )
    )

    grid_chart_position.add(
        position,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%"
        ),
    )
    return grid_chart,grid_chart_position
