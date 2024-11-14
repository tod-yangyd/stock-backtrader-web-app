import pandas as pd
import pyecharts.options as opts
from pyecharts import options as opts
from pyecharts.charts import Bar, Grid, Kline, Line,HeatMap
import pandas_ta as ta


def split_data(df: pd.DataFrame):
    x_data = df.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
    y_data = df[["open", "close", "low", "high"]].values.tolist()
    df_close = df["close"]

    df_remake =df.reset_index(drop=True)

    df_remake["index"] = df_remake.index
    df_remake["rise"] = df_remake[["open", "close"]].apply(lambda x: 1 if x[0] > x[1] else -1, axis=1)
    y_vol = df_remake[["index", "volume", "rise"]].values.tolist()
    print("成交量数据： ",y_vol)

    # 索引重置并转为date格式，方便统计
    res = df.reset_index()
    res["index"] = pd.to_datetime(res["index"]).dt.date
    # 按日期和合约品种计数,按索引排序（默认按值排序）,并转为list输出
    count_df = res[['index', 'code']].value_counts(sort=False).sort_index().reset_index()

    hm_data = count_df.values.tolist()
    hm_x_data = count_df['index'].tolist()
    hm_y_data = count_df['code'].unique().tolist()

    return x_data, y_data, df_close, y_vol, hm_data, hm_x_data, hm_y_data


def calculate_ma(day_count: int, df: pd.DataFrame):
    return df.rolling(day_count).mean().fillna("-").values.tolist()

def calculate_ema(day_count: int, df: pd.DataFrame):
    result =  df.ewm(span=day_count,adjust=False).mean()
    #result = ta.ema(df, length=day_count)

    return  result.dropna(axis=0, how='any').astype(int)

def draw_pro_kline_fut(period:str,ema_params:dict,df: pd.DataFrame):
    x_data, y_data, df_close, y_vol, hm_data, hm_x_data, hm_y_data = split_data(df)

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
                is_show=False, pos_bottom=10, pos_left="center"
            ),
            # 区域缩放组件
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False,
                    type_="inside",
                    xaxis_index=[0, 1],
                    range_start=98,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0, 1],
                    type_="slider",
                    pos_top="85%",
                    range_start=98,
                    range_end=100,
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
                series_index=5,
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

    # 均线图
    line = (
        Line()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="MA"+str(ema_params["ema1"]),
            y_axis=calculate_ma(ema_params["ema1"], df_close),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )

        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
    )

    # ema移动平均线
    ema_line = (
        Line()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name="EMA"+str(ema_params["ema1"]),

            y_axis=calculate_ema(ema_params["ema1"], df_close),
            # 是否平滑显示
            is_smooth=True,
            # 是否开启hover在拐点上的提示动画效果
            is_hover_animation=False,
            # width:线宽，opacity: 透明度
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            itemstyle_opts=opts.ItemStyleOpts(color='yellow'),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="EMA" + str(ema_params["ema2"]),
            y_axis=calculate_ema(ema_params["ema2"], df_close),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color='green'),
        )
        .add_yaxis(
            series_name="EMA" + str(ema_params["ema3"]),
            y_axis=calculate_ema(ema_params["ema3"], df_close),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color='purple'),
        )
        .add_yaxis(
            series_name="EMA" + str(ema_params["ema4"]),
            y_axis=calculate_ema(ema_params["ema4"], df_close),
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=2, opacity=1),
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color='blue'),
        )
        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
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
#hm_data, hm_x_data, hm_y_data
    position = (
        HeatMap()
        .add_xaxis(xaxis_data=hm_x_data)
        .add_yaxis("",
                   hm_y_data,
                   hm_data,
                   label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            title_opts=opts.TitleOpts(title = "主力合约分布月份热力图"),
            visualmap_opts=opts.VisualMapOpts(),

        )
    )

    # Kline And Line
    overlap_kline_line = kline.overlap(ema_line)

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

    grid_chart_position.add(
        position,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%"
        ),
    )
    return grid_chart,grid_chart_position
