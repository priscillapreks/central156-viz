"""
charts.py — Todos os componentes visuais do Dashboard Central 156.
Cada função recebe um DataFrame já filtrado e retorna uma fig Plotly.
"""
import json
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import (
    MACROTEMA_COLORS, MACROTEMA_LABELS,
    PRIMARY, DANGER, WARNING, SUCCESS, NEUTRAL, VOL_MIN,
    CORES_CATEGORIAS, CATEGORIA_ORDEM, COR_BARRA_PADRAO, COR_BARRA_DESTAQUE,
)

_TPL  = 'plotly_white'
_GRID = 'rgba(226,232,240,0.8)'
_TF   = dict(size=14, color='#1C3557', family='Arial')  # title font
_AF   = dict(size=11, color='#64748B', family='Arial')   # axis font


def _base(fig: go.Figure, h: int = 360, t: int = 12,
          margin: dict = None) -> go.Figure:
    fig.update_layout(
        template=_TPL, height=h,
        margin=margin or dict(t=t, b=36, l=8, r=8),
        font=dict(family='Arial'),
        plot_bgcolor='white', paper_bgcolor='white',
        hoverlabel=dict(bgcolor='white', font_size=12),
    )
    fig.update_xaxes(gridcolor=_GRID, linecolor='#E2E8F0')
    fig.update_yaxes(gridcolor=_GRID, linecolor='#E2E8F0')
    return fig


def _mac_color(m: str) -> str:
    return MACROTEMA_COLORS.get(m, '#BDC3C7')


def _mac_label(m: str) -> str:
    return MACROTEMA_LABELS.get(m, m)


def _cores_destaque(labels, destaque: Optional[str] = None,
                    cor_padrao: str = COR_BARRA_PADRAO,
                    cor_destaque: str = COR_BARRA_DESTAQUE) -> list:
    """Retorna lista de cores sólidas: cor_padrao para todas as barras,
    exceto a barra cujo label == destaque, que recebe cor_destaque.
    Se destaque for None (sem seleção), todas as barras ficam com cor_padrao."""
    if not destaque:
        return [cor_padrao] * len(labels)
    return [cor_destaque if lbl == destaque else cor_padrao for lbl in labels]


# ══════════════════════════════════════════════════════════════════════════════
# 0. Composição por categoria (rosca) — cores fixas
# ══════════════════════════════════════════════════════════════════════════════

def pizza_categoria(df: pd.DataFrame, height: int = 320) -> go.Figure:
    """Gráfico de rosca 'Composição por Categoria' com paleta fixa
    (CORES_CATEGORIAS) e legenda na ordem lógica Demanda/Problema/Elogio/Outros."""
    cat_agg = df['categoria_manifestacao'].value_counts().reset_index()
    cat_agg.columns = ['Categoria', 'Volume']

    # Ordena conforme CATEGORIA_ORDEM, preservando qualquer categoria extra ao final
    ordem_idx = {c: i for i, c in enumerate(CATEGORIA_ORDEM)}
    cat_agg['_ordem'] = cat_agg['Categoria'].map(
        lambda c: ordem_idx.get(c, len(CATEGORIA_ORDEM)))
    cat_agg = cat_agg.sort_values('_ordem').drop(columns='_ordem')

    fig = px.pie(
        cat_agg, values='Volume', names='Categoria',
        color='Categoria',
        category_orders={'Categoria': CATEGORIA_ORDEM},
        color_discrete_map=CORES_CATEGORIAS,
        hole=0.46,
    )
    fig.update_traces(
        textposition='outside', textfont_size=11,
        hovertemplate='<b>%{label}</b><br>Volume: %{value:,}<br>%{percent}<extra></extra>',
    )
    fig.update_layout(
        height=height, margin=dict(t=8, b=8, l=8, r=8),
        template=_TPL, plot_bgcolor='white', paper_bgcolor='white',
        showlegend=True,
        legend=dict(orientation='h', y=-0.14, font=dict(size=10)),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 1. Mapa coroplético
# ══════════════════════════════════════════════════════════════════════════════

def mapa_coropletico(
    bairro_df: pd.DataFrame,
    geojson: dict,
    metric: str = 'total',
    metric_label: str = 'Volume total',
    selected: Optional[str] = None,
) -> go.Figure:
    """
    Choropleth mapbox por bairro.
    metric: 'total' | 'taxa_problema' | 'taxa_conclusao' | 'tmr'
    """
    cs = 'YlOrRd' if metric in ('total', 'taxa_problema', 'tmr') else 'RdYlGn'
    fmt = '.1f' if metric in ('taxa_problema', 'taxa_conclusao') else ','

    # Normalise column names before using
    _bdf = bairro_df.copy()
    if 'taxa_problema' not in _bdf.columns:
        _bdf['taxa_problema'] = (_bdf['n_prob'] / _bdf['total'] * 100).round(1)
    if 'taxa_conclusao' not in _bdf.columns:
        _bdf['taxa_conclusao'] = (_bdf['n_conc'] / _bdf['total'] * 100).round(1)
    if 'tmr' not in _bdf.columns and 'tmr_mediano' in _bdf.columns:
        _bdf['tmr'] = _bdf['tmr_mediano']
    if metric not in _bdf.columns:
        metric = 'total'

    z_vals = _bdf[metric].copy()

    fig = go.Figure(go.Choroplethmapbox(
        geojson=geojson,
        featureidkey='properties.nome',
        locations=_bdf['bairro_geo'],
        z=z_vals,
        colorscale=cs,
        reversescale=(metric == 'taxa_conclusao'),
        marker_opacity=0.72,
        marker_line_width=0.9,
        marker_line_color='white',
        colorbar=dict(
            title=dict(text=metric_label, font=dict(size=11)),
            thickness=14, len=0.72, tickfont=dict(size=10),
        ),
        text=bairro_df['bairro_geo'],
        customdata=_bdf[
            ['bairro_geo', 'regional_label', 'total',
             'taxa_problema', 'tmr', 'taxa_conclusao']
        ].values,
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            'Regional: %{customdata[1]}<br>'
            'Volume: <b>%{customdata[2]:,}</b><br>'
            'Taxa Problema: %{customdata[3]:.1f}%<br>'
            'TMR mediano: %{customdata[4]:.1f} dias<br>'
            'Taxa Conclusão: %{customdata[5]:.1f}%'
            '<extra></extra>'
        ),
        name='',
    ))

    if selected and selected in _bdf['bairro_geo'].values:
        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson, featureidkey='properties.nome',
            locations=[selected], z=[1],
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
            showscale=False, marker_line_width=3.5,
            marker_line_color='#0D7377', name='Selecionado', hoverinfo='skip',
        ))

    fig.update_layout(
        mapbox=dict(style='carto-positron', zoom=10.4,
                    center=dict(lat=-25.428, lon=-49.271)),
        height=480, margin=dict(t=0, b=0, l=0, r=0),
        template=_TPL, paper_bgcolor='white',
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 2. Série temporal
# ══════════════════════════════════════════════════════════════════════════════

def serie_temporal(ts: pd.DataFrame, show_crit: bool = True) -> go.Figure:
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Bar(
        x=ts['ano_mes_dt'], y=ts['total'],
        name='Volume', marker_color=PRIMARY, opacity=0.72,
        hovertemplate='%{x|%b/%Y}: <b>%{y:,}</b><extra></extra>',
    ), secondary_y=False)
    if show_crit and 'taxa_problema' in ts.columns:
        fig.add_trace(go.Scatter(
            x=ts['ano_mes_dt'], y=ts['taxa_problema'] * 100,
            name='% Problema', mode='lines',
            line=dict(color=DANGER, width=2.2),
            hovertemplate='%{x|%b/%Y}: <b>%{y:.1f}%</b><extra></extra>',
        ), secondary_y=True)
    fig.update_yaxes(title_text='Volume mensal',  secondary_y=False,
                     tickfont=_AF, gridcolor=_GRID)
    fig.update_yaxes(title_text='% Problema', secondary_y=True,
                     tickfont=_AF, showgrid=False, ticksuffix='%',
                     range=[0, ts['taxa_problema'].max() * 120 if show_crit and len(ts) else 20])
    fig.update_xaxes(tickformat='%b/%Y', tickangle=-30, tickfont=_AF)
    _base(fig, h=300, margin=dict(t=8, b=50, l=10, r=55))
    fig.update_layout(legend=dict(orientation='h', y=-0.22, x=0, font=dict(size=11)))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 3. Barras macrotema
# ══════════════════════════════════════════════════════════════════════════════

def barras_macrotema(df_mac: pd.DataFrame, col: str = 'total',
                     label: str = 'Volume', height: Optional[int] = None) -> go.Figure:
    """Barras horizontais por macrotema, coloridas conforme MACROTEMA_COLORS
    (cada macrotema mantém sua cor de identidade em todo o dashboard)."""
    df_p = df_mac.sort_values(col, ascending=True).tail(15)
    ylabs = [_mac_label(m) for m in df_p['macrotema']]
    cols = [_mac_color(m) for m in df_p['macrotema']]
    fig = go.Figure(go.Bar(
        y=ylabs, x=df_p[col], orientation='h',
        marker_color=cols, opacity=0.88,
        text=df_p[col].apply(
            lambda v: f'{v:,.0f}' if col == 'total' else f'{v:.1f}%'),
        textposition='outside', textfont=dict(size=9.5),
        customdata=df_p[['crit_pct', 'total']].values,
        hovertemplate=(
            '<b>%{y}</b><br>'
            f'{label}: %{{x:,}}<br>'
            'Criticidade: %{customdata[0]:.1f}%'
            '<extra></extra>'
        ),
    ))
    h = height or max(260, len(df_p) * 26 + 50)
    _base(fig, h=h, margin=dict(t=8, b=28, l=8, r=65))
    fig.update_xaxes(title_text=label, tickfont=_AF)
    fig.update_yaxes(tickfont=dict(size=10))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 4. Barras assuntos (top-N)
# ══════════════════════════════════════════════════════════════════════════════

def barras_assuntos(df_ass: pd.DataFrame, height: Optional[int] = None) -> go.Figure:
    """Barras horizontais 'Top Assuntos por Volume', coloridas conforme o
    macrotema de cada assunto (mesma paleta MACROTEMA_COLORS do dashboard)."""
    df_p = df_ass.sort_values('total', ascending=True)
    cols = [_mac_color(m) for m in df_p['macrotema']]
    fig = go.Figure(go.Bar(
        y=df_p['assunto_padronizado'].str[:44],
        x=df_p['total'], orientation='h',
        marker_color=cols, opacity=0.88,
        text=df_p['total'].apply(lambda v: f'{v:,}'),
        textposition='outside', textfont=dict(size=9),
        customdata=df_p[['macrotema', 'crit_pct', 'tmr']].values,
        hovertemplate=(
            '<b>%{y}</b><br>Volume: %{x:,}<br>'
            'Macrotema: %{customdata[0]}<br>'
            'Criticidade: %{customdata[1]:.1f}%<br>'
            'TMR mediano: %{customdata[2]:.1f} dias'
            '<extra></extra>'
        ),
    ))
    h = height or max(300, len(df_p) * 28 + 50)
    _base(fig, h=h, margin=dict(t=8, b=28, l=8, r=70))
    fig.update_xaxes(title_text='Volume', tickfont=_AF)
    fig.update_yaxes(tickfont=dict(size=9))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 5. TMR por regional
# ══════════════════════════════════════════════════════════════════════════════

def barras_tmr_regional(df: pd.DataFrame, height: int = 320) -> go.Figure:
    """Barras verticais 'TMR Mediano por Regional', na mesma cor sólida
    usada em 'Órgãos responsáveis' (PRIMARY)."""
    agg = (df.groupby('regional_label')['tempo_resposta_dias']
             .median().reset_index()
             .rename(columns={'tempo_resposta_dias': 'tmr'})
             .sort_values('tmr'))
    fig = go.Figure(go.Bar(
        x=agg['regional_label'], y=agg['tmr'],
        marker_color=PRIMARY, opacity=0.75,
        text=agg['tmr'].round(1), textposition='outside',
        textfont=dict(size=10),
        hovertemplate='<b>%{x}</b><br>TMR mediano: %{y:.1f} dias<extra></extra>',
    ))
    _base(fig, h=height, margin=dict(t=8, b=65, l=10, r=8))
    fig.update_xaxes(tickangle=-30, tickfont=dict(size=10))
    fig.update_yaxes(title_text='TMR mediano (dias)', tickfont=_AF)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 6. Órgãos responsáveis
# ══════════════════════════════════════════════════════════════════════════════

def barras_orgaos(df_org: pd.DataFrame) -> go.Figure:
    df_p = df_org.sort_values('total', ascending=True)
    # Nomes curtos (remove prefixo 'SECRETARIA MUNICIPAL')
    short = df_p['orgao_padronizado'].str.replace(
        'SECRETARIA MUNICIPAL', 'SM', regex=False
    ).str.replace('FUNDACAO', 'FND', regex=False).str[:50]

    fig = go.Figure(go.Bar(
        y=short, x=df_p['total'], orientation='h',
        marker_color=PRIMARY, opacity=0.75,
        text=df_p['total'].apply(lambda v: f'{v:,}'),
        textposition='outside', textfont=dict(size=9),
        customdata=df_p[['crit_pct', 'tmr', 'taxa_conclusao']].values,
        hovertemplate=(
            '<b>%{y}</b><br>Volume: %{x:,}<br>'
            'Criticidade: %{customdata[0]:.1f}%<br>'
            'TMR mediano: %{customdata[1]:.1f} dias<br>'
            'Taxa conclusão: %{customdata[2]:.1f}%'
            '<extra></extra>'
        ),
    ))
    _base(fig, h=max(280, len(df_p) * 28 + 50),
          margin=dict(t=8, b=28, l=8, r=80))
    fig.update_xaxes(title_text='Volume', tickfont=_AF)
    fig.update_yaxes(tickfont=dict(size=9))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 7. Score timeline (scores_monthly)
# ══════════════════════════════════════════════════════════════════════════════

def score_timeline(
    scores: pd.DataFrame,
    top_n: int = 8,
    highlight: Optional[str] = None,
) -> go.Figure:
    """Evolução mensal do score composto para os top-N assuntos."""
    # Top assuntos por score médio
    top = (scores.groupby('assunto_padronizado')['priority_score']
                 .mean().nlargest(top_n).index.tolist())
    if highlight and highlight not in top:
        top = [highlight] + top[:top_n - 1]

    palette = (px.colors.qualitative.Bold + px.colors.qualitative.Safe)
    color_map = {a: palette[i % len(palette)] for i, a in enumerate(top)}

    fig = go.Figure()
    for assunto in top:
        sub = (scores[scores['assunto_padronizado'] == assunto]
               .groupby('ano_mes')
               .agg(score_med=('priority_score', 'mean'),
                    score_min=('priority_score', 'min'),
                    score_max=('priority_score', 'max'),
                    crit_pct =('score_critico',  'mean'))
               .reset_index()
               .sort_values('ano_mes'))
        sub['dt'] = pd.to_datetime(sub['ano_mes'] + '-01')
        col = color_map[assunto]
        lw  = 3 if assunto == highlight else 2

        # Banda min/max
        fig.add_trace(go.Scatter(
            x=pd.concat([sub['dt'], sub['dt'][::-1]]),
            y=pd.concat([sub['score_max'], sub['score_min'][::-1]]),
            fill='toself', showlegend=False, hoverinfo='skip',
            fillcolor=col.replace('rgb', 'rgba').replace(')', ',0.10)')
                       if col.startswith('rgb') else col + '18',
            line=dict(color='rgba(0,0,0,0)'), name=assunto + '_band',
        ))

        fig.add_trace(go.Scatter(
            x=sub['dt'], y=sub['score_med'],
            mode='lines', name=assunto[:45],
            line=dict(color=col, width=lw),
            customdata=sub[['score_min', 'score_max', 'crit_pct']].values,
            hovertemplate=(
                f'<b>{assunto[:45]}</b><br>'
                'Mês: %{x|%b/%Y}<br>'
                'Score: <b>%{y:.1f}</b><br>'
                'Faixa: %{customdata[0]:.1f}–%{customdata[1]:.1f}<br>'
                'Criticidade: %{customdata[2]:.1%}'
                '<extra></extra>'
            ),
        ))

    # Marcos pandêmicos
    for ds, lbl, lc in [
        ('2020-03-01', 'COVID-19', '#94A3B8'),
        ('2021-03-01', 'Lockdown', '#64748B'),
    ]:
        fig.add_shape(type='line', x0=ds, x1=ds, y0=0, y1=1,
                      xref='x', yref='paper',
                      line=dict(color=lc, width=1, dash='dot'))
        fig.add_annotation(x=ds, y=1.01, xref='x', yref='paper',
                           text=lbl, showarrow=False,
                           font=dict(size=9, color=lc),
                           xanchor='left', yanchor='bottom')

    _base(fig, h=380, margin=dict(t=30, b=70, l=10, r=18))
    fig.update_xaxes(tickformat='%b/%Y', tickangle=-30, tickfont=_AF)
    fig.update_yaxes(title_text='Score composto (0–100)', range=[0, 105],
                     tickfont=_AF)
    fig.update_layout(
        legend=dict(orientation='h', y=-0.28, x=0,
                    font=dict(size=10),
                    title=dict(text='Assunto · banda=faixa regional',
                               font=dict(size=9))),
        hovermode='x unified',
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 8. Ranking global (bubble chart)
# ══════════════════════════════════════════════════════════════════════════════

def ranking_global(scores: pd.DataFrame, top_n: int = 15,
                   vol_min: int = VOL_MIN) -> go.Figure:
    """Bubble chart horizontal: score × assunto, tamanho=volume, cor=criticidade."""
    latest = scores['ano_mes'].max()
    df_mes = (scores[scores['ano_mes'] == latest]
              .groupby(['assunto_padronizado', 'macrotema'])
              .agg(
                  priority_score  = ('priority_score',   'mean'),
                  score_critico   = ('score_critico',     'mean'),
                  volume          = ('volume',            'sum'),
                  sla_mediano     = ('sla_mediano',       'mean'),
                  taxa_enc        = ('taxa_encerramento', 'mean'),
                  rank_global_min = ('rank_global',       'min'),
              ).reset_index())
    df_mes = df_mes[df_mes['volume'] >= vol_min].nlargest(top_n, 'priority_score')
    df_mes = df_mes.sort_values('priority_score')
    df_mes['crit_pct']  = (df_mes['score_critico'] * 100).round(1)
    df_mes['vol_k']     = (df_mes['volume'] / 1000).round(1)
    df_mes['enc_pct']   = (df_mes['taxa_enc'] * 100).round(1)
    df_mes['assunto_s'] = df_mes['assunto_padronizado'].str[:44]

    fig = go.Figure()
    for _, row in df_mes.iterrows():
        norm = min(row['score_critico'], 1.0)
        col  = f'rgb({int(160+95*norm)},{int(30+40*(1-norm))},{int(30+30*(1-norm))})'
        sz   = float(np.clip(row['vol_k'] * 0.35 + 14, 10, 52))

        fig.add_trace(go.Scatter(
            x=[row['priority_score']], y=[row['assunto_s']],
            mode='markers+text',
            marker=dict(size=sz, color=col, opacity=0.87,
                        line=dict(color='white', width=1.5)),
            text=[f"#{int(row['rank_global_min'])}"],
            textfont=dict(size=8, color='white'),
            textposition='middle center',
            name=row['macrotema'],
            showlegend=False,
            customdata=[[row['macrotema'], row['crit_pct'], row['vol_k'],
                         row['sla_mediano'], row['enc_pct'],
                         int(row['rank_global_min']), int(row['volume'])]],
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Score: <b>%{x:.1f}</b><br>'
                'Macrotema: %{customdata[0]}<br>'
                'Criticidade: %{customdata[1]}%<br>'
                'Volume: %{customdata[6]:,}<br>'
                'SLA: %{customdata[3]:.0f} dias<br>'
                'Encerrados: %{customdata[4]}%<br>'
                'Rank global: <b>#%{customdata[5]}</b>'
                '<extra></extra>'
            ),
        ))

    # Zona crítica
    fig.add_shape(type='line', x0=70, x1=70, y0=0, y1=1,
                  xref='x', yref='paper',
                  line=dict(color='rgba(180,0,0,0.30)', width=1, dash='dot'))
    fig.add_annotation(x=70, y=1.01, xref='x', yref='paper',
                       text='Score ≥ 70 (crítico)', showarrow=False,
                       font=dict(size=9, color='#B22222'),
                       xanchor='right', yanchor='bottom')

    _base(fig, h=max(360, top_n * 34 + 80),
          margin=dict(t=28, b=50, l=16, r=16))
    fig.update_xaxes(title_text='Score composto (0–100)',
                     range=[0, 105], tickfont=_AF)
    fig.update_yaxes(tickfont=dict(size=10))
    fig.add_annotation(
        text=f'● tamanho=volume · cor: vermelho=alta criticidade ·  mês: {latest}',
        xref='paper', yref='paper', x=0, y=-0.09,
        showarrow=False, font=dict(size=9, color='#94A3B8'),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 9. Race chart (D3 embutido em HTML — retorna string)
# ══════════════════════════════════════════════════════════════════════════════

def race_chart_html(
    scores: pd.DataFrame,
    top_n: int = 15,
    vol_min: int = VOL_MIN,
) -> str:
    """
    Retorna HTML do animated bar chart race para uso em st.components.v1.html().
    Usa D3.js v7 via CDN; dados embutidos como JSON inline.
    """
    import json

    agg = (scores.groupby(['ano_mes', 'assunto_padronizado', 'macrotema'])
           .agg(priority_score=('priority_score', 'mean'),
                score_critico =('score_critico',  'mean'),
                volume        =('volume',          'sum'))
           .reset_index())
    agg = agg[agg['volume'] >= vol_min]
    agg['crit_pct']   = (agg['score_critico'] * 100).round(1)
    agg['assunto_s']  = agg['assunto_padronizado'].str[:40]

    months = sorted(agg['ano_mes'].unique().tolist())
    all_data = {}
    for m in months:
        top = (agg[agg['ano_mes'] == m]
               .nlargest(top_n, 'priority_score')
               .sort_values('priority_score', ascending=True))
        all_data[m] = top[['assunto_s', 'assunto_padronizado',
                             'macrotema', 'priority_score',
                             'crit_pct', 'volume']].to_dict('records')

    data_js      = json.dumps(all_data, ensure_ascii=False, separators=(',', ':'))
    months_js    = json.dumps(months)
    mac_colors_js = json.dumps(MACROTEMA_COLORS)

    return f"""<!DOCTYPE html><html lang="pt-BR">
<head><meta charset="UTF-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#fff;color:#1E293B;overflow-x:hidden;}}
.ctrl{{display:flex;align-items:center;gap:10px;padding:10px 14px;background:#f8fafc;
       border-bottom:1px solid #e2e8f0;flex-wrap:wrap;}}
.btn{{padding:6px 16px;border-radius:7px;border:1.5px solid #cbd5e1;background:#fff;
      color:#1C3557;font-size:.82rem;font-weight:600;cursor:pointer;transition:all .15s;}}
.btn:hover{{background:#f1f5f9;}}
.btn.on{{background:#0D7377;border-color:#0D7377;color:#fff;}}
.spd{{font-size:.8rem;color:#64748b;}}
.spd select{{padding:4px 7px;border-radius:6px;border:1.5px solid #cbd5e1;
             font-size:.8rem;background:#fff;cursor:pointer;}}
.badge{{font-size:1.8rem;font-weight:800;color:#1C3557;letter-spacing:-1px;margin-left:auto;}}
.srow{{display:flex;align-items:center;gap:10px;padding:6px 14px 10px;}}
.slabel{{font-size:.75rem;color:#94a3b8;white-space:nowrap;}}
#sl{{flex:1;height:5px;border-radius:3px;cursor:pointer;accent-color:#0D7377;}}
#chart{{padding:0 14px 8px;}}
.note{{font-size:.72rem;color:#94a3b8;padding:4px 14px 8px;}}
</style></head>
<body>
<div class="ctrl">
  <button class="btn" id="pb" onclick="tog()">▶ Play</button>
  <button class="btn" onclick="mv(-1)">◀</button>
  <button class="btn" onclick="mv(1)">▶</button>
  <div class="spd"><label>Velocidade:</label>
    <select id="sp" onchange="spd=+this.value;restart()">
      <option value="1200">Lenta</option>
      <option value="800" selected>Normal</option>
      <option value="400">Rápida</option>
      <option value="180">Turbo</option>
    </select>
  </div>
  <div class="badge" id="mb">jan/2020</div>
</div>
<div class="srow">
  <span class="slabel" id="s0">{months[0]}</span>
  <input type="range" id="sl" min="0" max="{len(months)-1}" value="0"
         oninput="onsl(+this.value)">
  <span class="slabel" id="se">{months[-1]}</span>
</div>
<div id="chart"></div>
<div class="note">● tamanho da barra = score 0–100 · % dentro da barra = criticidade · volume entre parênteses · vol ≥ {vol_min} chamados/mês</div>
<script>
const D={data_js},M={months_js},MC={mac_colors_js};
const TN={top_n};
let ci=0,play=false,iv=null,spd=800;
const MN=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];

const W=document.getElementById('chart').parentElement.clientWidth-28;
const MG={{t:4,r:110,b:28,l:220}};
const BH=34,IH=TN*BH+MG.t+MG.b;
const IW=W-MG.l-MG.r;

const svg=d3.select('#chart').append('svg').attr('width',W).attr('height',IH);
const g=svg.append('g').attr('transform',`translate(${{MG.l}},${{MG.t}})`);
g.append('g').attr('class','grid');
const bG=g.append('g'),lG=g.append('g'),rG=g.append('g');
const xA=g.append('g').attr('transform',`translate(0,${{TN*BH}})`);
const xS=d3.scaleLinear().domain([0,100]).range([0,IW]);
xA.call(d3.axisBottom(xS).ticks(5).tickSize(-TN*BH));
xA.select('.domain').attr('stroke','#E2E8F0');
xA.selectAll('.tick line').attr('stroke','#F1F5F9');
xA.selectAll('.tick text').attr('fill','#94A3B8').attr('font-size','10px');

function upd(idx,anim){{
  const rows=D[M[idx]]||[];
  const n=rows.length;
  const dur=anim?Math.min(spd*.7,550):0;
  const ease=d3.easeCubicInOut;

  const bars=bG.selectAll('rect.b').data(rows,d=>d.assunto_padronizado);
  bars.enter().append('rect').attr('class','b').attr('x',0).attr('rx',5)
      .attr('y',(d,i)=>(n-1-i)*BH+4).attr('height',BH-8)
      .attr('fill',d=>MC[d.macrotema]||'#BDC3C7').attr('opacity',0).attr('width',0)
    .merge(bars).transition().duration(dur).ease(ease)
      .attr('y',(d,i)=>(n-1-i)*BH+4)
      .attr('width',d=>Math.max(2,xS(d.priority_score)))
      .attr('fill',d=>MC[d.macrotema]||'#BDC3C7').attr('opacity',.87);
  bars.exit().transition().duration(dur).attr('opacity',0).attr('width',0).remove();

  const labs=lG.selectAll('text.ln').data(rows,d=>d.assunto_padronizado);
  labs.enter().append('text').attr('class','ln').attr('x',-8)
      .attr('text-anchor','end').attr('dominant-baseline','middle')
      .attr('font-size','11px').attr('font-weight','500').attr('opacity',0)
      .attr('y',(d,i)=>(n-1-i)*BH+BH/2).text(d=>d.assunto_s)
    .merge(labs).transition().duration(dur).ease(ease)
      .attr('y',(d,i)=>(n-1-i)*BH+BH/2)
      .attr('fill',d=>MC[d.macrotema]||'#475569').attr('opacity',1)
      .text(d=>d.assunto_s);
  labs.exit().transition().duration(dur).attr('opacity',0).remove();

  const scr=rG.selectAll('text.rs').data(rows,d=>d.assunto_padronizado);
  scr.enter().append('text').attr('class','rs').attr('dominant-baseline','middle')
      .attr('font-size','10px').attr('fill','#475569').attr('opacity',0)
      .attr('x',d=>xS(d.priority_score)+5).attr('y',(d,i)=>(n-1-i)*BH+BH/2)
    .merge(scr).transition().duration(dur).ease(ease)
      .attr('x',d=>Math.max(2,xS(d.priority_score))+5)
      .attr('y',(d,i)=>(n-1-i)*BH+BH/2).attr('opacity',1)
      .text(d=>`${{d.priority_score.toFixed(1)}} (${{d.volume.toLocaleString('pt-BR')}})`);
  scr.exit().transition().duration(dur).attr('opacity',0).remove();

  // inner criticidade
  const inn=bG.selectAll('text.ic').data(rows.filter(d=>xS(d.priority_score)>36),d=>d.assunto_padronizado);
  inn.enter().append('text').attr('class','ic').attr('dominant-baseline','middle')
      .attr('font-size','9.5px').attr('font-weight','700').attr('fill','white')
      .attr('opacity',0).attr('x',d=>xS(d.priority_score)-30)
      .attr('y',(d,i)=>(n-1-i)*BH+BH/2)
    .merge(inn).transition().duration(dur).ease(ease)
      .attr('x',d=>Math.max(2,xS(d.priority_score))-30)
      .attr('y',(d,i)=>(n-1-i)*BH+BH/2).attr('opacity',.9)
      .text(d=>`${{d.crit_pct}}%`);
  inn.exit().transition().duration(dur).attr('opacity',0).remove();

  const [yr,mo]=M[idx].split('-');
  document.getElementById('mb').textContent=`${{MN[+mo-1]}}/${{yr}}`;
  document.getElementById('sl').value=idx;
}}

function tog(){{
  play=!play;
  const b=document.getElementById('pb');
  if(play){{b.textContent='⏸ Pausar';b.classList.add('on');
    iv=setInterval(()=>{{ci=ci>=M.length-1?0:ci+1;upd(ci,true);}},spd);}}
  else{{b.textContent='▶ Play';b.classList.remove('on');clearInterval(iv);}}
}}
function mv(d){{if(play)tog();ci=Math.max(0,Math.min(M.length-1,ci+d));upd(ci,true);}}
function onsl(v){{if(play)tog();ci=v;upd(ci,false);}}
function restart(){{if(play){{clearInterval(iv);iv=setInterval(()=>{{ci=ci>=M.length-1?0:ci+1;upd(ci,true);}},spd);}}}}
upd(0,false);
</script></body></html>"""


# ══════════════════════════════════════════════════════════════════════════════
# 10. Score vs criticidade scatter (quadrante)
# ══════════════════════════════════════════════════════════════════════════════

def quadrante_risco(scores: pd.DataFrame, vol_min: int = VOL_MIN) -> go.Figure:
    """Scatter criticidade × SLA mediano por macrotema. Tamanho = volume."""
    latest = scores['ano_mes'].max()
    df = (scores[scores['ano_mes'] == latest]
          .groupby(['assunto_padronizado', 'macrotema'])
          .agg(crit =('score_critico', 'mean'),
               sla  =('sla_mediano',   'mean'),
               vol  =('volume',         'sum'),
               score=('priority_score', 'mean'))
          .reset_index())
    df = df[df['vol'] >= vol_min]
    df['crit_pct'] = (df['crit'] * 100).round(1)
    df['sla_clip'] = df['sla'].clip(upper=120)
    df['vol_sz']   = np.log1p(df['vol'])

    fig = go.Figure()
    for mac in df['macrotema'].unique():
        s = df[df['macrotema'] == mac]
        fig.add_trace(go.Scatter(
            x=s['sla_clip'], y=s['crit_pct'],
            mode='markers', name=_mac_label(mac),
            legendgroup=mac,
            marker=dict(size=s['vol_sz'] * 4 + 5, color=_mac_color(mac),
                        opacity=0.80, line=dict(color='white', width=0.7)),
            customdata=s[['assunto_padronizado', 'vol', 'score']].values,
            hovertemplate=(
                '<b>%{customdata[0]}</b><br>'
                'Criticidade: %{y:.1f}%<br>'
                'SLA mediano: %{x:.0f} dias<br>'
                'Volume: %{customdata[1]:,}<br>'
                'Score: %{customdata[2]:.1f}'
                '<extra></extra>'
            ),
        ))

    cm = df['crit_pct'].median()
    sm = df['sla_clip'].median()
    for lbl, val, axis in [
        (f'Median crit. ({cm:.0f}%)', cm, 'y'),
        (f'Median SLA ({sm:.0f} d)', sm, 'x'),
    ]:
        if axis == 'y':
            fig.add_shape(type='line', x0=0, x1=1, y0=val, y1=val,
                          xref='paper', yref='y',
                          line=dict(color='rgba(100,116,139,0.35)', width=1, dash='dot'))
            fig.add_annotation(x=1, y=val, xref='paper', yref='y',
                               text=lbl, showarrow=False,
                               font=dict(size=9, color='#64748B'),
                               xanchor='right', yanchor='bottom')
        else:
            fig.add_shape(type='line', x0=val, x1=val, y0=0, y1=1,
                          xref='x', yref='paper',
                          line=dict(color='rgba(100,116,139,0.35)', width=1, dash='dot'))

    ym, xm = df['crit_pct'].max(), df['sla_clip'].max()
    for qx, qy, txt, qc in [
        (xm*.75, ym*.92, '⚠ EMERGÊNCIA', DANGER),
        (xm*.05, ym*.92, '⚡ CRÍTICO ÁGIL', WARNING),
        (xm*.75, ym*.10, '⏳ GARGALO', NEUTRAL),
        (xm*.05, ym*.10, '✓ EFICIENTE', SUCCESS),
    ]:
        fig.add_annotation(x=qx, y=qy, text=txt, showarrow=False,
                           font=dict(size=9, color=qc), align='center',
                           bgcolor='rgba(255,255,255,0.78)')

    _base(fig, h=400, margin=dict(t=12, b=40, l=10, r=160))
    fig.update_xaxes(title_text='SLA mediano (dias, clip=120)', tickfont=_AF)
    fig.update_yaxes(title_text='Criticidade (%PROBLEMA)', tickfont=_AF)
    fig.update_layout(legend=dict(
        title=dict(text='Macrotema', font=dict(size=10)),
        font=dict(size=9), orientation='v',
        yanchor='top', y=1, xanchor='right', x=1.18,
    ))
    return fig
