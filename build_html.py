# -*- coding: utf-8 -*-
"""Генератор итоговой HTML-страницы: читает data/data.json, пишет index.html."""
import json

D = json.load(open('data/data.json', encoding='utf-8'))
YEARS = D['meta']['years']
S = D['series']
REG = D['regions']

# ---------- SVG helpers ----------
PALETTE = ['#2b6cb0', '#2c7a7b', '#b7791f', '#c53030', '#6b46c1', '#c05621', '#276749', '#97266d']

def fmt(v):
    return f'{v:,.1f}'.replace(',', ' ').replace('.', ',')

def bar_chart(series, labels, colors, title, unit='млрд руб.', w=860, h=340, stacked=False, pct=False):
    """series: list of lists (per layer), labels: x labels"""
    pad_l, pad_b, pad_t = 60, 46, 40
    cw, ch = w - pad_l - 20, h - pad_b - pad_t
    n = len(labels)
    totals = [sum(s[i] for s in series if s[i] is not None) for i in range(n)]
    vmax = max(totals) if not pct else 100.0
    svg = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    svg.append(f'<text x="{pad_l}" y="24" class="chart-title">{title}</text>')
    for g in range(5):
        y = pad_t + ch - ch * g / 4
        val = vmax * g / 4
        svg.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-20}" y2="{y:.1f}" class="grid"/>')
        svg.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" class="axis">{val:.0f}</text>')
    slot = cw / n
    bw = slot * 0.55
    for i in range(n):
        x = pad_l + slot * i + (slot - bw) / 2
        base = pad_t + ch
        for li, s in enumerate(series):
            v = s[i]
            if v is None:
                continue
            hh = ch * v / vmax
            if stacked:
                base -= hh
                y = base
            else:
                y = pad_t + ch - hh
            svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(hh,0.5):.1f}" fill="{colors[li]}"><title>{labels[i]}: {fmt(v)} {unit}</title></rect>')
        if stacked:
            svg.append(f'<text x="{x+bw/2:.1f}" y="{pad_t + ch - ch*totals[i]/vmax - 6:.1f}" text-anchor="middle" class="barlabel">{fmt(totals[i]) if not pct else f"{totals[i]:.0f}%"}</text>')
        else:
            for li, s in enumerate(series):
                v = s[i]
                if v is None: continue
                y = pad_t + ch - ch * v / vmax
                svg.append(f'<text x="{x+bw/2:.1f}" y="{y-6:.1f}" text-anchor="middle" class="barlabel">{fmt(v)}</text>')
        svg.append(f'<text x="{x+bw/2:.1f}" y="{pad_t+ch+18:.1f}" text-anchor="middle" class="axis">{labels[i]}</text>')
    svg.append('</svg>')
    return ''.join(svg)

def line_chart(series, names, colors, title, w=860, h=340, unit='млрд руб.'):
    pad_l, pad_b, pad_t = 60, 46, 40
    cw, ch = w - pad_l - 20, h - pad_b - pad_t
    n = len(YEARS)
    flat = [v for s in series for v in s if v is not None]
    vmax = max(flat); vmin = min(0, min(flat))
    rng = vmax - vmin or 1
    svg = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    svg.append(f'<text x="{pad_l}" y="24" class="chart-title">{title}</text>')
    for g in range(5):
        y = pad_t + ch - ch * g / 4
        svg.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-20}" y2="{y:.1f}" class="grid"/>')
        svg.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" class="axis">{vmin + rng*g/4:.0f}</text>')
    def xy(i, v):
        return (pad_l + cw * i / (n - 1), pad_t + ch - ch * (v - vmin) / rng)
    for i, yr in enumerate(YEARS):
        x, _ = xy(i, vmin)
        svg.append(f'<text x="{x:.1f}" y="{pad_t+ch+18:.1f}" text-anchor="middle" class="axis">{yr}</text>')
    for si, s in enumerate(series):
        pts = [(xy(i, v), v) for i, v in enumerate(s) if v is not None]
        path = 'M' + ' L'.join(f'{p[0][0]:.1f} {p[0][1]:.1f}' for p in pts)
        svg.append(f'<path d="{path}" fill="none" stroke="{colors[si]}" stroke-width="2.5"/>')
        for (x, y), v in pts:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{colors[si]}"><title>{names[si]}, {fmt(v)} {unit}</title></circle>')
            svg.append(f'<text x="{x:.1f}" y="{y-9:.1f}" text-anchor="middle" class="barlabel">{fmt(v)}</text>')
    lx = pad_l + 6
    for si, nm in enumerate(names):
        svg.append(f'<rect x="{lx}" y="{h-16}" width="11" height="11" fill="{colors[si]}"/>')
        svg.append(f'<text x="{lx+16}" y="{h-6}" class="axis">{nm}</text>')
        lx += 16 + 8.2 * len(nm) + 26
    svg.append('</svg>')
    return ''.join(svg)

def hbar(items, title, w=860, unit='млрд руб.', color='#2b6cb0'):
    """items: [(name, value)]"""
    pad_l, pad_r, pad_t = 320, 70, 40
    row_h = 30
    h = pad_t + row_h * len(items) + 30
    vmax = max(v for _, v in items) or 1
    svg = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    svg.append(f'<text x="{pad_l}" y="24" class="chart-title">{title}</text>')
    for i, (nm, v) in enumerate(items):
        y = pad_t + i * row_h
        bw = (w - pad_l - pad_r) * v / vmax
        svg.append(f'<text x="{pad_l-10}" y="{y+16}" text-anchor="end" class="axis">{nm}</text>')
        svg.append(f'<rect x="{pad_l}" y="{y+3}" width="{max(bw,1):.1f}" height="20" fill="{color}"><title>{nm}: {fmt(v)} {unit}</title></rect>')
        svg.append(f'<text x="{pad_l+max(bw,1)+8:.1f}" y="{y+17}" class="barlabel">{fmt(v)}</text>')
    svg.append('</svg>')
    return ''.join(svg)

def donut(items, title, w=600, h=300):
    """items: [(name, value)]"""
    import math
    cx, cy, r, ir = 150, 160, 105, 58
    total = sum(v for _, v in items) or 1
    svg = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">']
    svg.append(f'<text x="20" y="24" class="chart-title">{title}</text>')
    a0 = -math.pi / 2
    for i, (nm, v) in enumerate(items):
        frac = v / total
        a1 = a0 + 2 * math.pi * frac
        large = 1 if frac > 0.5 else 0
        x0o, y0o = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1o, y1o = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x0i, y0i = cx + ir * math.cos(a1), cy + ir * math.sin(a1)
        x1i, y1i = cx + ir * math.cos(a0), cy + ir * math.sin(a0)
        svg.append(f'<path d="M{x0o:.1f} {y0o:.1f} A{r} {r} 0 {large} 1 {x1o:.1f} {y1o:.1f} L{x0i:.1f} {y0i:.1f} A{ir} {ir} 0 {large} 0 {x1i:.1f} {y1i:.1f} Z" fill="{PALETTE[i % len(PALETTE)]}"><title>{nm}: {fmt(v)} млрд руб. ({frac*100:.1f}%)</title></path>')
        a0 = a1
    ly = 70
    for i, (nm, v) in enumerate(items):
        frac = v / total
        svg.append(f'<rect x="300" y="{ly-11}" width="11" height="11" fill="{PALETTE[i % len(PALETTE)]}"/>')
        svg.append(f'<text x="317" y="{ly}" class="axis">{nm} — {frac*100:.1f}%</text>')
        ly += 24
    svg.append('</svg>')
    return ''.join(svg)

# ---------- charts ----------
YRLBL = [str(y) for y in YEARS]

ch_total = bar_chart([S['total']], YRLBL, ['#2b6cb0'],
    'Совокупная задолженность по налогам, сборам, пеням и налоговым санкциям, 2018–2022')

ch_struct = bar_chart([S['arrears'], S['penalty']], YRLBL, ['#2b6cb0', '#b7791f'],
    'Структура задолженности: недоимка и пени с налоговыми санкциями', stacked=True)

ch_budget = bar_chart([S['federal'], S['regional'], S['local']], YRLBL,
    ['#2b6cb0', '#2c7a7b', '#b7791f'],
    'Задолженность по уровням бюджета (с пенями и санкциями)', stacked=True)

ch_taxes_dyn = line_chart(
    [S['nds'], S['insurance'], S['ndfl'], S['profit'], S['ndpi']],
    ['НДС', 'Страховые взносы', 'НДФЛ', 'Налог на прибыль', 'НДПИ'],
    ['#c53030', '#2b6cb0', '#2c7a7b', '#6b46c1', '#b7791f'],
    'Динамика задолженности по ключевым видам платежей')

tax_items_2022 = [
    ('НДС', S['nds'][-1]), ('Страховые взносы', S['insurance'][-1]),
    ('Транспортный налог (орг.)', S['transport_org'][-1]), ('Налог на прибыль', S['profit'][-1]),
    ('Акцизы', S['excise'][-1]), ('Налог на имущество (орг.)', S['property_org'][-1]),
    ('НДФЛ', S['ndfl'][-1]), ('НДПИ', S['ndpi'][-1]),
]
tax_items_2022.sort(key=lambda x: -x[1])
ch_taxes_2022 = hbar(tax_items_2022, 'Задолженность по видам налогов и взносов, 2022 год')

fiz_years = ['2020', '2021', '2022']
fiz_idx = [YRLBL.index(y) for y in fiz_years]
ch_fiz = bar_chart(
    [[S['trans_fiz'][i] for i in fiz_idx], [S['prop_fiz'][i] for i in fiz_idx],
     [S['land_fiz'][i] for i in fiz_idx], [S['ndfl_fiz'][i] for i in fiz_idx]],
    fiz_years, ['#2b6cb0', '#2c7a7b', '#b7791f', '#c53030'],
    'Задолженность физических лиц по налогам, уплачиваемым самостоятельно', stacked=True)

def norm_name(n):
    n = n.strip()
    return n[0] + n[1:].lower() if n.isupper() else n

REG_NAMED = {norm_name(k): v for k, v in REG.items()}
REG_SUBJ = {k: v for k, v in REG_NAMED.items() if 'федеральный округ' not in k.lower()}
top10 = sorted(REG_SUBJ.items(), key=lambda kv: -(kv[1][-1] or 0))[:10]
ch_regions = hbar([(k, v[-1]) for k, v in top10],
    'Топ-10 регионов по сумме задолженности, 2022 год', color='#2c7a7b')
top10_share = sum(v[-1] for _, v in top10) / S['total'][-1] * 100

ch_fiz_donut = donut(
    [('Транспортный налог', S['trans_fiz'][-1]), ('Налог на имущество', S['prop_fiz'][-1]),
     ('Земельный налог', S['land_fiz'][-1]), ('НДФЛ (ст. 228 НК)', S['ndfl_fiz'][-1])],
    'Структура долга физических лиц, 2022 год')

HTML = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Налоговая задолженность в РФ, 2018–2022 — Архинчеев Владислав</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; color: #1a202c; background: #f7fafc; }}
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 24px 28px 64px; }}
  header {{ background: #1a365d; color: #fff; padding: 30px 28px; }}
  header .wrap {{ padding-bottom: 0; }}
  h1 {{ margin: 0 0 6px; font-size: 26px; }}
  h2 {{ color: #1a365d; border-bottom: 2px solid #1a365d; padding-bottom: 5px; margin-top: 44px; font-size: 20px; }}
  h3 {{ color: #2d4a73; font-size: 16px; margin-bottom: 6px; }}
  .sub {{ color: #cbd5e0; font-size: 14px; }}
  .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px 20px; margin: 22px 0; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
  svg {{ width: 100%; height: auto; }}
  .chart-title {{ font-size: 15px; font-weight: 600; fill: #1a365d; }}
  .axis {{ font-size: 12px; fill: #4a5568; }}
  .barlabel {{ font-size: 11px; fill: #2d3748; }}
  .grid {{ stroke: #e2e8f0; stroke-width: 1; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border: 1px solid #cbd5e0; padding: 7px 10px; text-align: right; }}
  th {{ background: #edf2f7; }}
  td:first-child, th:first-child {{ text-align: left; }}
  .kpi {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 20px 0; }}
  .kpi div {{ flex: 1 1 150px; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px; }}
  .kpi b {{ display: block; font-size: 22px; color: #1a365d; }}
  .kpi span {{ font-size: 12px; color: #718096; }}
  ul {{ padding-left: 22px; }}
  li {{ margin: 6px 0; line-height: 1.55; }}
  a {{ color: #2b6cb0; }}
  .note {{ font-size: 13px; color: #718096; }}
  .rec {{ border-left: 4px solid #2c7a7b; background: #f0fff4; padding: 12px 16px; margin: 14px 0; }}
  .rec b {{ color: #22543d; }}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>Налоговая задолженность в Российской Федерации, 2018–2022</h1>
  <div class="sub">Аналитическая записка по открытым данным ФНС России (через ЕМИСС) · Выполнил: Архинчеев Владислав · {''}</div>
  <div class="sub">Единица измерения: млрд руб. · Состояние задолженности на конец января каждого года (сопоставимые срезы)</div>
</div></header>
<div class="wrap">

<div class="kpi">
  <div><b>{fmt(S['total'][-1])}</b><span>млрд руб. — совокупная задолженность на конец января 2022 г.</span></div>
  <div><b>+{S['total'][-1]/S['total'][-2]*100-100:.1f}%</b><span>рост к аналогичному срезу 2021 г. после трёх лет снижения</span></div>
  <div><b>{S['arrears'][-1]/S['total'][-1]*100:.0f}%</b><span>доля недоимки в совокупной задолженности (2022)</span></div>
  <div><b>{fmt(S['uncollectible'][-1])}</b><span>млрд руб. признано невозможным к взысканию (2022)</span></div>
</div>

<h2>1. Данные</h2>
<div class="card"><p>Использованы официальные открытые данные ФНС России, опубликованные в Единой межведомственной
информационно-статистической системе (ЕМИСС), показатель 42549 «Задолженность по налогам и сборам, пеням и налоговым
санкциям». Показатель формируется ФНС ежемесячно; для сопоставимости по годам взяты срезы на конец января
2018–2022 гг. Все значения приведены в млрд руб.</p>
<p>Сверка: срез на конец января 2019 г. (926,8 млрд руб.) совпадает с опубликованной ФНС суммой задолженности
по налогам и сборам, пеням и санкциям на 01.01.2019 (~0,93 трлн руб.).</p>
<table>
<tr><th>Показатель</th>{''.join(f'<th>{y}</th>' for y in YRLBL)}</tr>
<tr><td>Совокупная задолженность</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['total'])}</tr>
<tr><td>в т.ч. недоимка</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['arrears'])}</tr>
<tr><td>пени и налоговые санкции</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['penalty'])}</tr>
<tr><td>НДС</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['nds'])}</tr>
<tr><td>Страховые взносы</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['insurance'])}</tr>
<tr><td>НДФЛ</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['ndfl'])}</tr>
<tr><td>Налог на прибыль организаций</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['profit'])}</tr>
<tr><td>Транспортный налог (организации)</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['transport_org'])}</tr>
<tr><td>Налог на имущество организаций</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['property_org'])}</tr>
<tr><td>Акцизы</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['excise'])}</tr>
<tr><td>НДПИ</td>{''.join(f'<td>{fmt(v)}</td>' for v in S['ndpi'])}</tr>
</table>
<p class="note">Источник: <a href="https://www.fedstat.ru/indicator/42549">ЕМИСС, показатель 42549</a> (ответственный — ФНС России).</p></div>

<h2>2. Динамика</h2>
<div class="card">{ch_total}</div>
<div class="card">{ch_struct}</div>
<div class="card">{ch_budget}</div>

<h2>3. Анализ</h2>
<div class="card">
<ul>
<li><b>Тренд 2018–2021 — устойчивое снижение:</b> с 1 169,9 до 809,1 млрд руб. (−31%). Снижение идёт и по недоимке
(903,2 → 637,9 млрд руб.), и по пеням с санкциями (266,7 → 171,2 млрд руб.). Это результат работы ФНС с
задолженностью: массовая инвентаризация, взыскание за счёт денежных средств и имущества, списание безнадёжной
задолженности (в 2021 г. урегулировано 204,3 млрд руб. — максимум за пять лет).</li>
<li><b>Аномалия 2022 года — резкий рост на 36%</b> (809,1 → 1 103,2 млрд руб.). Рост концентрирован в федеральных
платежах (+55%, с 380,5 до 588,1 млрд руб.) и носит «крупноплательщиковый» характер: НДС +43% (248,9 → 355,0),
налог на прибыль +103% (65,8 → 133,6), НДПИ +167% (9,8 → 26,2). Наиболее вероятные причины — переход крупных
компаний (нефтегазовый сектор) на авансовые платежи при спорах по НДПИ/НДС, изменение сроков уплаты для
крупнейших налогоплательщиков (с 2022 г. — до 28-го числа) и общий шок ликвидности у компаний после начала
санкций. Региональные и местные платежи при этом выросли умеренно (+14% и +8%), что подтверждает точечный,
а не массовый характер аномалии.</li>
<li><b>Структура почти не меняется:</b> недоимка стабильно ~78–79% совокупной задолженности, пени и санкции —
~21–22%. Значит, проблема в первую очередь в неуплате самих налогов, а не в росте пеней.</li>
<li><b>Долг физических лиц — отдельная зона внимания.</b> С 2020 г. (когда ФНС стала публиковать этот разрез) он
стабилен на уровне ~215–220 млрд руб., при этом почти 55% — транспортный налог. В отличие от общего долга, он
не снижается: у физлиц нет оборотных средств для «взыскания», а рост кадастровой стоимости поддерживает рост
начислений по имущественным налогам.</li>
<li><b>Концентрация по территориям:</b> топ-10 регионов дают {top10_share:.0f}% всей задолженности. Лидеры —
крупнейшие налоговые базы (Москва, Московская область, Санкт-Петербург, Краснодарский край, Татарстан),
что отражает концентрацию крупного бизнеса и обособленных подразделений.</li>
<li><b>Безнадёжная задолженность мала, но волатильна</b> (4–12 млрд руб. в год против поступлений ~30 трлн руб.):
выборочные списания, в основном по ликвидированным/банкротам.</li>
</ul>
</div>

<h2>4. Предложения по повышению эффективности взыскания</h2>
<div class="card">
<div class="rec"><b>1. Целевой мониторинг крупнейших должников по НДС и налогу на прибыль.</b>
Логика: аномалия 2022 г. (+36% задолженности) сформирована федеральными платежами крупных компаний; рост НДС
на 106 млрд руб. за год — это до 25–30% годовых поступлений НДС. Предложение: ежемесячный «дорожный контроль»
дебиторки топ-1000 плательщиков с автоматической рассылкой требований при просрочке >5 рабочих дней и
превентивным информированием о ближайших сроках уплаты. Опирается на данные п. 3 (рост НДС/прибыли/НДПИ в 2022 г.).</div>
<div class="rec"><b>2. Отдельная ветка работы с долгом физических лиц по транспортному налогу.</b>
Логика: ~118 млрд руб. (54% долга физлиц) — транспортный налог; он не снижается три года, хотя механизм
ограничения на регистрационные действия по ТС давно существует. Предложение: массовая рассылка
предупреждений владельцам ТС о предстоящем ограничении через ГИБДД, оплата «в один клик» из уведомления,
автоматическая рассрочка для многодетных и пенсионеров. Опирается на данные раздела «Долг физлиц».</div>
<div class="rec"><b>3. Ускорение инкассового взыскания за счёт денежных средств.</b>
Логика: при недоимке 859 млрд руб. (2022) самый дешёвый способ взыскания — инкассовое поручение по счетам;
средства на счетах у большинства «живых» должников есть. Предложение: сокращение срока от просрочки до
направления поручения в банк с 15 до 5 рабочих дней для должников с подтверждёнными остатками
(данные ЕПГУ/ГИС «Налог-3»), приоритет — по федеральным платежам с наибольшей ставкой пени.</div>
<div class="rec"><b>4. Расширение урегулирования задолженности через банкротство физлиц и реструктуризацию.</b>
Логика: в 2021 г. урегулировано 204,3 млрд руб., в 2022-м — только 39,5 млрд руб.; часть долга «зависает»
вечным балластом. Предложение: активнее направлять требования кредиторов в процедуры банкротства физлиц,
продвигать реструктуризацию для юрлиц с временными трудностями (п. 5 ст. 46 НК), чтобы конвертировать
безнадёжный долг в реальные поступления.</div>
<div class="rec"><b>5. Региональное выравнивание: кураторство для «хвоста» субъектов с аномально высоким долгом.</b>
Логика: {top10_share:.0f}% задолженности — топ-10 регионов; у остальных долг невелик, но там часто слабее
кадровый потенциал службы взыскания. Предложение: межрегиональные бригады МИ ФНС по управлению долгом
для сопровождения крупных дел в регионах-хвосте и передача лучших практик (единый реестр обращений
взыскания на недвижимость).</div>
</div>

<h2>5. Визуализация: виды налогов и территории</h2>
<div class="card">{ch_taxes_dyn}</div>
<div class="card">{ch_taxes_2022}</div>
<div class="card">{ch_fiz}</div>
<div class="card">{ch_fiz_donut}</div>
<div class="card">{ch_regions}</div>

<h2>6. Источники</h2>
<div class="card"><ul>
<li><a href="https://www.fedstat.ru/indicator/42549">ЕМИСС (fedstat.ru), показатель 42549</a> — «Задолженность по налогам и сборам, пеням и налоговым санкциям»: все ряды динамики, разбивки по видам платежей, уровням бюджета, физическим лицам и регионам (ответственный орган — ФНС России).</li>
<li><a href="https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/">ФНС России, «Данные по формам статистической налоговой отчётности»</a> — форма №4-НМ «Отчет о задолженности по налогам и сборам, пеням и налоговым санкциям» (сверка сводных значений).</li>
<li><a href="https://www.nalog.gov.ru/opendata/7707329152-poved/">Открытые данные ФНС, набор 7707329152-poved</a> — «О начислении и поступлении налогов, сборов и иных обязательных платежей» (форма №1-НМ), машиночитаемые CSV за 2019–2023 гг.</li>
<li><a href="https://www.nalog.gov.ru/opendata/7707329152-debtam/">Открытые данные ФНС, набор 7707329152-debtam</a> — «Данные о сумме задолженности по налогам и сборам, пеням и налоговым санкциям» в разрезе субъектов РФ.</li>
<li><a href="https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/">ФНС России, «Статистика и аналитика»</a> — бюллетени о состоянии расчётов по налогам и сборам.</li>
</ul>
<p class="note">Страница самодостаточна: все диаграммы построены встроенным SVG, внешних файлов и зависимостей нет.</p>
</div>

</div>
</body>
</html>"""

open('index.html', 'w', encoding='utf-8').write(HTML)
print('index.html written,', len(HTML), 'bytes')
