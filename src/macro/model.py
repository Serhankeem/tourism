"""Calendar-aware comparisons. Missing/zero baselines never become invented rates."""
import datetime as dt

def month_before(period):
    year,month=map(int,period.split('-'));return f'{year-1:04}-12' if month==1 else f'{year:04}-{month-1:02}'
def months(start,end):
    y,m=map(int,start.split('-'));ey,em=map(int,end.split('-'));out=[]
    while (y,m)<=(ey,em):
        out.append(f'{y:04}-{m:02}');y,m=(y+1,1) if m==12 else (y,m+1)
    return out

def valid_period(period):
    if not isinstance(period,str) or len(period)!=7:raise ValueError('invalid_period')
    year,month=map(int,period.split('-'))
    if not 1900<=year<=2100 or not 1<=month<=12 or period!=f'{year:04}-{month:02}':raise ValueError('invalid_period')
    return period

def comparisons(observations,period):
    valid_period(period);year,month=map(int,period.split('-'))
    values={p:o['value'] for p,o in observations.items()}
    value=values.get(period)
    def rate(current,base):return round((current/base-1)*100,2) if current is not None and base is not None and base!=0 else None
    def ytd(y):
        keys=[f'{y:04}-{m:02}' for m in range(1,month+1)]
        return sum(values[p] for p in keys) if all(p in values for p in keys) else None
    total,previous=ytd(year),ytd(year-1)
    return dict(mom_pct=rate(value,values.get(month_before(period))),yoy_pct=rate(value,values.get(f'{year-1:04}-{month:02}')),ytd_value=total,ytd_yoy_pct=rate(total,previous),reference_period=period,mom_base_period=month_before(period),yoy_base_period=f'{year-1:04}-{month:02}',ytd_range=[f'{year:04}-01',period])
