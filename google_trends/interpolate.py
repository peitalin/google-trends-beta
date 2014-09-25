
import arrow
from IPython import embed

def interpolate_ioi(date, ioi):
    """ takes a list of dates and interest over time and
    interpolates the dates. Called by change_in_ioi()"""

    def linspace(start, stop, n):
        start, stop = float(start), float(stop)
        if n == 1:
            yield start
            return
        h = (stop - start) / (n - 1)
        for i in range(n):
            yield start + h * i

    def date_range(date):
        if isinstance(date[0], arrow.arrow.Arrow):
            s, e = list(map(arrow.get, [list(date)[0], list(date)[-1]]))
        else:
            s, e = list(map(arrow.get, [list(date)[0][:10], list(date)[-1][-10:]]))
        dates = arrow.Arrow.range('day', s, e)
        return [x.datetime for x in dates]

    date_ioi = list(zip(date, ioi))
    final_elem = []
    interp = []
    for s,e in zip(date_ioi, date_ioi[1:]):
        try:
            end_date, start_date = list(map(arrow.get, [e[0], s[0]]))
        except:
            end_date, start_date = list(map(arrow.get, [e[0][:10], s[0][:10]]))
            # [:10] to deal with weekly: '2010-10-10 - 2010-10-16'
        days = (end_date - start_date).days
        interp += list(linspace(s[1], e[1], days+1))[:-1]
        final_elem = e[1]

    if final_elem:
        interp += [float(final_elem)]

    date = date_range(date)
    return date, interp







def conform_interest_over_time(IoI):
    """ Removes 0's from a list of IoI to calculate percentage changes.
    Called by change_in_ioi(). """
    if not any(IoI):
        return IoI

    try:
        iIoI = iter(IoI)
        t1 = next(iIoI)
        t2 = next(iIoI)
    except StopIteration:
        return [t1]

    new_IoI = []
    new_IoI += [t1]

    for n in range(len(IoI)-2):
        if t2 != 0:
            new_IoI += [t2]
            t1 = t2
        else:
            new_IoI += [t1]
        t2 = next(iIoI)

    if t2 != 0:
        new_IoI += [t2]
    else:
        new_IoI += [t1]

    def average(list_ioi):
        return sum([float(s) for s in list_ioi])/len(list_ioi)

    avg = round(average(IoI))
    new_IoI = [avg if x==0 else x for x in new_IoI]
    return new_IoI






def change_in_ioi(date, IoI):
    """Computes changes in interest over time (IoI) (log base 10).
    date -- list of dates
    IoI  -- list of IoI values
    Returns a list of dates, and list of changes in IoI values. """

    from math import log10, log
    date, IoI = interpolate_ioi(date, IoI)
    IoI = conform_interest_over_time(IoI)
    delta_IoI = [1]

    for f1,f2 in zip(IoI, IoI[1:]):
        f1 = 1 + float(f1)
        f2 = 1 + float(f2)
        relative_effect = log10(f1/f2)
        # if relative_effect < 0:
        #     relative_effect = 0
        # Google Trends appears to scale interest on log base 10
        # natural log yields highly volatile time series
        try:
            delta_IoI.append(1+log10(1+relative_effect))
        except ValueError:
            from IPython import embed
            embed()

    return date, delta_IoI




# def plot_merged_IOI_data():


#     import pandas as pd
#     import matplotlib.pyplot as plt
#     from ggplot import ggplot, geom_line, ggtitle, ggsave, scale_colour_manual, ylab, xlab, aes

#     ydat = pd.DataFrame(list(zip(common_date, y_ioi)), columns=["Date", 'Weekly series'])
#     mdat = pd.DataFrame(list(zip(common_date, adj_IoI)), columns=['Date', 'Merged series'])
#     qdat = pd.DataFrame(list(zip(common_date, qdat_interp)), columns=['Date', 'Daily series'])
#     ddat = ydat.merge(mdat, on='Date').merge(qdat,on='Date')
#     ddat['Date'] = list(map(pd.to_datetime, ddat['Date']))

#     ydat['Date'] = list(map(pd.to_datetime, ydat['Date']))
#     mdat['Date'] = list(map(pd.to_datetime, mdat['Date']))
#     qdat['Date'] = list(map(pd.to_datetime, qdat['Date']))

#     newdat = pd.melt(ddat[['Date', 'Merged series', 'Daily series', 'Weekly series']], id_vars='Date')
#     newdat.sort('variable', inplace=True)

#     colors = [
#         (0.467, 0.745, 0.88), # blue
#         (0.706, 0.486, 0.78), # purple
#         (0.839, 0.373, 0.373) # red
#     ]

#     show = ggplot(aes(x='Date', y='value', color='variable'), data=newdat) + \
#         geom_line(aes(x='Date', y='Daily series'), data=qdat, alpha=0.5, color=colors[0]) + \
#         geom_line(aes(x='Date', y='Merged series'), data=mdat, alpha=0.9, color=colors[1]) + \
#         geom_line(aes(x='Date', y='Weekly series'), data=ydat, alpha=0.5, color=colors[2], size=1.5) + \
#         geom_line(aes(x='Date', y='value', color='variable'), data=newdat, alpha=0.0) +  scale_colour_manual(values=colors) + \
#         ggtitle("Interest over time for '{}'".format(keywords[0].keyword)) + \
#         ylab("Interest Over Time") + xlab("Date")

#     ggsave(filename='merged_{}'.format(keywords[0].keyword), width=15, height=4)

