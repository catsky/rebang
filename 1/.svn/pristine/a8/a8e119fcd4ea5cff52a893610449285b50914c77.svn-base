#-*- coding:utf-8 -*-
from datetime import datetime

def timesince(timestamp, default="刚才"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """
    dt = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    diff = now - dt
    
    periods = (
        (diff.days / 365, "年"),
        (diff.days / 30, "月"),
        (diff.days / 7, "星期"),
        (diff.days, "天"),
        (diff.seconds / 3600, "小时"),
        (diff.seconds / 60, "分钟"),
        (diff.seconds, "秒"),
    )

    for period, singular in periods:
        
        if period:
            return "%d %s之前" % (period, singular)

    return default

if __name__ == '__main__':
    ts = 1375103765
    result = timesince(ts)
    print result