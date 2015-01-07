
import arrow
try:
	from IPython import embed
except:
	pass




def interpolate_ioi(dates, IoT):
    """ takes a list of dates and interest-over-time and
    interpolates IoT between the dates. Called by change_in_ioi()"""

    def linspace(start, stop, n):
        start, stop = float(start), float(stop)
        if n == 1:
            yield start
            return
        h = (stop - start) / (n - 1)
        for i in range(n):
            yield start + h * i

    def date_range(dates):
        if isinstance(dates[0], str):
            s = arrow.get(dates[0][:10])
        else:
            s = dates[0]

        if isinstance(dates[-1], str):
            e = arrow.get(dates[-1][-10:])
        else:
            e = dates[-1]

        return [x.datetime for x in arrow.Arrow.range('day', s, e)]

    # embed()
    dates_ioi = list(zip(dates, IoT))
    final_elem = []
    interp = []
    count = 1

    for s, e in zip(dates_ioi, dates_ioi[1:]):
        s = list(s)
        e = list(e)

        if isinstance(s[0], arrow.Arrow) and isinstance(e[0], str):
            s[0] = s[0].strftime('%Y-%m-%d')
            # Bad data: when google returns mix of weekly and monthly data:
            # (<Arrow [2013-10-01T00:00:00+00:00]>, 0),
            # ('2013-10-06 - 2013-10-12', '100'),

        if isinstance(s[0], str) and isinstance(e[0], arrow.Arrow):
            e[0] = e[0].strftime('%Y-%m-%d')
            # Bad data: Dealing with entries like:
            #  ('2014-06-29 - 2014-07-05', '0'),
            #  (<Arrow [2014-07-01T00:00:00+00:00]>, 0),

        if isinstance(s[0], str) and isinstance(e[0], str):
            # weekly IoT data gotcha:
            # last weekly obs e.g. '2010-10-10 - 2010-10-16' will be truncated
            if count == len(dates_ioi) - 1: # If final weekly observation
                start_date = arrow.get(s[0][:10])
                end_date   = arrow.get(e[0][-10:])
                # [:10] to deal with weekly: '2010-10-10 - 2010-10-16'
                # [-10:] to get last day of last week
            else:
                start_date = arrow.get(s[0][:10])
                end_date   = arrow.get(e[0][:10])

        elif isinstance(s[0], arrow.Arrow):
            start_date, end_date = s[0], e[0]

        days = (end_date - start_date).days
        interp += list(linspace(s[1], e[1], days+1))[:-1]
        final_elem = e[1]
        count += 1

    if final_elem:
        interp += [float(final_elem)]

    return date_range(dates), interp






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
        return sum(float(s) for s in list_ioi) / len(list_ioi)

    avg = round(average(IoI))
    new_IoI = [avg if x==0 else x for x in new_IoI]
    return new_IoI






def change_in_ioi(dates, IoT):
    """Computes changes in interest over time (IoT) (log base 10).

    dates -- list of dates
    IoT   -- list of IoT values
    Returns a list of dates, and list of changes in IoT values. """

    from math import log10, log

    dates_new, IoT = interpolate_ioi(dates, IoT)
    IoT = conform_interest_over_time(IoT)
    delta_IoT = [1]

    for f1,f2 in zip(IoT, IoT[1:]):
        f1 = 1 + float(f1)
        f2 = 1 + float(f2)
        relative_effect = log10(f2/f1)
        # Google Trends appears to scale interest on log base 10
        # natural log yields highly volatile time series
        if relative_effect < -0.9:
            relative_effect = -0.9
            # log10(0.1) = 0, meaning zero interest
        try:
            delta_IoT.append(1+log10(1+relative_effect))
        except ValueError:
            from IPython import embed; embed()

    return dates_new, delta_IoT


