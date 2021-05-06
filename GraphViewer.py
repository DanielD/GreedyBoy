#!/usr/bin/env python
##
## GraphViewer.py
##

__author__      = "Kevin Pruvost"
__copyright__   = "Copyright 2021, GreedyBoy"
__credits__     = ["Kevin Pruvost", "Hugo Matthieu-Steinbach"]
__license__     = "Proprietary"
__version__     = "1.0.0"
__maintainer__  = "Kevin Pruvost"
__email__       = "pruvostkevin0@gmail.com"
__status__      = "Test"

import matplotlib.pyplot as plt
import mplfinance
import matplotlib.animation as animation
import mplcursors
import pandas as pandas

class GraphViewer:
    """
    :param priceData: Dataframe containing detailed informations about prices.
    :type priceData: DataFrame
    :param bollingerData: Dataframe containing informations about bollinger gaps.
    :type bollingerData: DataFrame
    :param animateCallback: Callback called on the animation loop.
    :type animateCallback: Function
    :param fullscreen: De/Activates fullscreen mode for Matplotlib.
    :type fullscreen: bool

    Draws in 2 plots, the **bollinger bands**, the **bollinger gaps** and the
    **price chart** of a given cryptocurrency.

    ``priceData`` and ``bollingerData`` must be 2 ``DataFrame`` (``pandas``) in these formats:

    .. _PriceData:

    **Price Data**

    +---------------------+----------------------------+----------------------------+------------------------------+----------------------------+-----------+------------+--------------+--------------+
    | Date (as index)     | :abbr:`Open (First price)` | :abbr:`Close (Last price)` | :abbr:`High (Highest price)` | :abbr:`Low (Lowest price)` | :ref:`MA` | :ref:`Std` | :ref:`LBand` | :ref:`HBand` |
    +=====================+============================+============================+==============================+============================+===========+============+==============+==============+
    | 2021-04-24 05:00:00 | 1917.24                    | 1920.21                    | 1932.10                      | 1899.24                    | 1901.26   | 20.547     | 1860.124     | 1948.472     |
    +---------------------+----------------------------+----------------------------+------------------------------+----------------------------+-----------+------------+--------------+--------------+
    | ...                 | ...                        | ...                        | ...                          | ...                        | ...       | ...        | ...          | ...          |
    +---------------------+----------------------------+----------------------------+------------------------------+----------------------------+-----------+------------+--------------+--------------+

    .. _BollingerData:

    **Bollinger Data**

    ===================  ========
    Date (as index)      Value
    ===================  ========
    2021-04-24 05:00:00  67.00
    ...                  ...
    ===================  ========
    """

    ani = None
    """Contains the animation callback."""

    def __init__(self, priceData: pandas.DataFrame, bollingerData: pandas.DataFrame, animateCallback = None, fullscreen: bool = True):
        s = mplfinance.make_mpf_style(base_mpf_style='mike', rc={'font.size': 12})
        fig = mplfinance.figure(figsize=(15, 7), style=s)    # Defining figure size
        ax1 = fig.add_subplot(2, 1, 1)              # Defining plot 1
        ax2 = fig.add_subplot(2, 1, 2)              # Defining plot 2

        idf, df = priceData, bollingerData
        bollinger_bands = idf[['HBand', 'LBand']]

        def animate(ival):
            if animateCallback: animateCallback()
            if (20 + ival) > len(df):
                print('no more data to plot')
                ani.event_source.interval *= 3
                if ani.event_source.interval > 12000:
                    exit()
                return
            # datas = df.iloc[0:(20+ival)]

            ##
            ## Drawing Price Candle Chart + Bollinger Bands
            ##
            ax1.clear()     # Clear
            mplfinance.plot(idf, ax=ax1, type='candle', style='charles')    # Drawing Candle Chart
            chart1 = bollinger_bands.plot(ax=ax1, use_index=False)          # Drawing Bollinger Bands

            ##
            ## Drawing Bollinger Gaps
            ##
            ax2.cla()           # Clear
            df.plot(ax=ax2)     # Drawing data lines
            ax2.axhline(y=100, color="red", lw=1.5, linestyle="-")    # Drawing '100' line limit
            ax2.axhline(y=0, color="green", lw=1.5, linestyle="-")    # Drawing '0' line limit

            # Defining scatter points color considering their values
            # <= 0      : Green,
            # >= 100    : Red,
            # Otherwise : Blue
            colors = ['g' if val <= 0 else 'r' if val >= 100 else '#00000033' for val in df['Value']]
            chart2 = ax2.scatter(df.index, df['Value'], color=colors)

            # Activating cursor interactions
            cursors = list()
            cursors.append(mplcursors.cursor(chart1, hover=True))
            cursors.append(mplcursors.cursor(chart2, hover=True))
            for cursor in cursors:
                @cursor.connect("add")
                def _(sel):
                    print(sel.annotation.get_text())
                    sel.annotation.set_color('black')
                    sel.annotation.get_bbox_patch().set(color="white", alpha=1)
                    sel.annotation.arrow_patch.set(arrowstyle="fancy", color="white", alpha=1)

        self.ani = animation.FuncAnimation(fig, animate, interval=1000)  # Creating Animation
        ani = self.ani

        ##
        ## Customizing Matplotlib
        ##
        figManager = plt.get_current_fig_manager()
        if fullscreen: figManager.full_screen_toggle()
        plt.subplots_adjust(left=0.04, bottom=0.067, right=0.93, top=0.955)

    def start(self):
        """Starts the graph.

        .. important::

           It is a blocking function (like an app.exec() in Qt).
        """
        plt.show()