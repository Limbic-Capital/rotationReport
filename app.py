import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

es = pd.read_csv('Data/ES.txt')
es["Datetime"] = pd.to_datetime(es["Date"] + es[" Time"])
es['range'] = abs(es[' High'] - es[' Low'])
df = es.set_index("Datetime")
df["bar_count"] = range(0,len(df))

###########################
# Src https://stackoverflow.com/questions/65800877/python-zig-zag-algorithm-function-not-returning-expected-results
PEAK, VALLEY = 1, -1

def _identify_initial_pivot(X, up_thresh, down_thresh):
    """Quickly identify the X[0] as a peak or valley."""
    x_0 = X[0]
    max_x = x_0
    max_t = 0
    min_x = x_0
    min_t = 0
    up_thresh += 1
    down_thresh += 1

    for t in range(1, len(X)):
        x_t = X[t]

        if x_t / min_x >= up_thresh:
            return VALLEY if min_t == 0 else PEAK

        if x_t / max_x <= down_thresh:
            return PEAK if max_t == 0 else VALLEY

        if x_t > max_x:
            max_x = x_t
            max_t = t

        if x_t < min_x:
            min_x = x_t
            min_t = t

    t_n = len(X)-1
    return VALLEY if x_0 < X[t_n] else PEAK

def peak_valley_pivots_candlestick(close, high, low, up_thresh, down_thresh):
    """
    Finds the peaks and valleys of a series of HLC (open is not necessary).
    TR: This is modified peak_valley_pivots function in order to find peaks and valleys for OHLC.
    Parameters
    ----------
    close : This is series with closes prices.
    high : This is series with highs  prices.
    low : This is series with lows prices.
    up_thresh : The minimum relative change necessary to define a peak.
    down_thesh : The minimum relative change necessary to define a valley.
    Returns
    -------
    an array with 0 indicating no pivot and -1 and 1 indicating valley and peak
    respectively
    Using Pandas
    ------------
    For the most part, close, high and low may be a pandas series. However, the index must
    either be [0,n) or a DateTimeIndex. Why? This function does X[t] to access
    each element where t is in [0,n).
    The First and Last Elements
    ---------------------------
    The first and last elements are guaranteed to be annotated as peak or
    valley even if the segments formed do not have the necessary relative
    changes. This is a tradeoff between technical correctness and the
    propensity to make mistakes in data analysis. The possible mistake is
    ignoring data outside the fully realized segments, which may bias analysis.
    """
    if down_thresh > 0:
        raise ValueError('The down_thresh must be negative.')

    initial_pivot = _identify_initial_pivot(close, up_thresh, down_thresh)

    t_n = len(close)
    pivots = np.zeros(t_n, dtype='i1')
    pivots[0] = initial_pivot

    # Adding one to the relative change thresholds saves operations. Instead
    # of computing relative change at each point as x_j / x_i - 1, it is
    # computed as x_j / x_1. Then, this value is compared to the threshold + 1.
    # This saves (t_n - 1) subtractions.
    up_thresh += 1
    down_thresh += 1

    trend = -initial_pivot
    last_pivot_t = 0
    last_pivot_x = close[0]
    for t in range(1, len(close)):

        if trend == -1:
            x = low[t]
            r = x / last_pivot_x
            if r >= up_thresh:
                pivots[last_pivot_t] = trend#
                trend = 1
                #last_pivot_x = x
                last_pivot_x = high[t]
                last_pivot_t = t
            elif x < last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t
        else:
            x = high[t]
            r = x / last_pivot_x
            if r <= down_thresh:
                pivots[last_pivot_t] = trend
                trend = -1
                #last_pivot_x = x
                last_pivot_x = low[t]
                last_pivot_t = t
            elif x > last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t


    if last_pivot_t == t_n-1:
        pivots[last_pivot_t] = trend
    elif pivots[t_n-1] == 0:
        pivots[t_n-1] = trend

    return pivots



pivots = peak_valley_pivots_candlestick(df[' Last'], df[" High"], df[' Low'] ,.001,-.001)
df['Pivots'] = pivots
df['Pivot Price'] = np.nan  # This line clears old pivot prices
df.loc[df['Pivots'] == 1, 'Pivot Price'] = df[" High"]
df.loc[df['Pivots'] == -1, 'Pivot Price'] = df[" Low"]


df_diff = df['Pivot Price'].dropna().diff().copy()
#########################

zz = pd.DataFrame(df["Pivot Price"].dropna())
zz["Chg"] = abs(zz["Pivot Price"] - zz["Pivot Price"].shift(-1))

ChangeSeries = zz["Chg"].dropna()
std = np.std(ChangeSeries)
avg = np.average(ChangeSeries)
median = np.median(ChangeSeries)
impulse = np.percentile(ChangeSeries, 90)

##########################

fig = go.Figure(data=[go.Histogram(x=zz["Chg"], histnorm='probability')])
fig.update_layout(title_text='E-Mini S&P500 Rotations (normalized)', title_x=0.5)
fig.update_xaxes(title_text="Size (pts)")
fig.update_yaxes(title_text="Probability")
fig.update_layout()
fig.add_vline(x=impulse, name="Impulse")
fig.write_image("Output/chart.png")


##########################
page_title_text='Rotational Analysis (ES)'
title_text = 'Key Metrics'
text = 'Hello, welcome to your report!'
prices_text = 'Historical prices of S&P 500'
stats_text = 'Historical prices summary statistics'


# 2. Combine them together using a long f-string
html = f'''
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{page_title_text}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-0evHe/X+R7YkIZDRvuzKMRqM+OrBnVFBL6DOitfPri4tjfHxaWutUpFmBp4vmVor" crossorigin="anonymous">
    </head>
    <body>
        <div class="container">
            <center><img src='chart.png' width="700"></center>
        
            <table class="table">
                <thead>
                <tr>
                <th scope="col">Market</th>
                <th scope="col">Average</th>
                <th scope="col">Median</th>
                <th scope="col">Standard Dev</th>
                <th scope="col">1 Sigma</th>
                <th scope="col">Impulse (90th Percentile)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                <th scope="row">ES (pts)</th>
                <td>{round(avg,2)}</td>
                <td>{round(median,2)}</td>
                <td>{round(std,2)}</td>
                <td>{round(std+avg,2)}</td>
                <td>{round(impulse,2)}</td>
                </tr>
            </tbody>
            </table>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/js/bootstrap.bundle.min.js" integrity="sha384-pprn3073KE6tl6bjs2QrFaJGz5/SUsLqktiwsUTF55Jfv3qYSDhgCecCxMW52nD2" crossorigin="anonymous"></script>
    </body>
    </html>
    '''
# 3. Write the html string as an HTML file
with open('./Output/report.html', 'w') as f:
    f.write(html)