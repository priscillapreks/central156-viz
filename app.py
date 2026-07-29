"""
app.py — Dashboard de Priorização Dinâmica · Central 156 Curitiba
Streamlit multi-aba com mapa coroplético, KPIs, série temporal,
ranking de assuntos, score composto e race chart animado.

Execução:
    streamlit run app.py
"""
import sys
from pathlib import Path

# Garante que o diretório do app está no path
sys.path.insert(0, str(Path(__file__).parent))

import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from config import MACROTEMA_LABELS
from data_loader import (
    load_slim, load_ts, load_bairro, load_bairro_summary,
    load_macrotema, load_assunto, load_scores, load_geojson,
    load_filter_vals,
    filter_slim, filter_scores,
    compute_kpis, compute_ts, compute_bairro_map,
    compute_macrotema, compute_assuntos, compute_orgaos,
    get_bairro_detail,
)
from charts import (
    mapa_coropletico, serie_temporal, barras_macrotema,
    barras_assuntos, barras_tmr_regional, barras_orgaos,
    race_chart_html, quadrante_risco,
    pizza_categoria,
)

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Central 156 · Curitiba",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Espaçamento geral ── */
/* O header do Streamlit tem ~58px de altura fixa; compensamos com padding-top */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}

/* Remove margem extra do primeiro elemento */
.block-container > div:first-child { margin-top: 0 !important; }

/* ── Header do dashboard ── */
.dash-header {
    background: linear-gradient(135deg, #1C3557 0%, #0D7377 100%);
    border-radius: 12px;
    padding: 14px 24px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.dash-header-title {
    font-size: 1.3rem; font-weight: 800; color: #FFFFFF;
    letter-spacing: -0.3px;
}
.dash-header-sub {
    font-size: .78rem; color: rgba(255,255,255,0.70); margin-top: 2px;
}

/* ── KPI bar ── */
.kpi-bar {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
    margin-bottom: 14px;
}
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    text-align: center;
    min-height: 80px;
    display: flex; flex-direction: column; justify-content: center;
}
.kpi-val  { font-size: 1.75rem; font-weight: 800; color: #1C3557; letter-spacing: -1px; line-height: 1.1; }
.kpi-lbl  { font-size: .74rem; color: #64748B; margin-bottom: 4px; font-weight: 500; }
.kpi-sub  { font-size: .68rem; color: #94A3B8; margin-top: 3px; }

/* ── Section headers ── */
.sec-header {
    font-size: .95rem; font-weight: 700; color: #1C3557;
    border-left: 4px solid #0D7377;
    padding-left: 10px; margin: 14px 0 8px 0;
    line-height: 1.3;
}

/* ── Bairro panel ── */
.bairro-panel {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 10px;
    padding: 14px 16px;
}
.bairro-title {
    font-size: 1rem; font-weight: 700; color: #1C3557;
    margin-bottom: 10px;
}
.bairro-row {
    display: flex; justify-content: space-between;
    font-size: .82rem; color: #374151;
    padding: 4px 0; border-bottom: 1px solid #D1FAE5;
}
.bairro-key { color: #6B7280; }
.bairro-val { font-weight: 600; color: #1C3557; }

/* ── Sidebar filter labels ── */
div[data-testid="stMultiSelect"] label,
div[data-testid="stSelectbox"] label {
    font-size: .8rem !important; color: #475569 !important;
}

/* ── Hide default Streamlit top decoration ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)


# ── Carga de dados ─────────────────────────────────────────────────────────────
with st.spinner("Carregando dados…"):
    df_slim  = load_slim()
    df_ts0   = load_ts()
    df_bai0  = load_bairro()
    df_bais  = load_bairro_summary()
    df_mac0  = load_macrotema()
    df_ass0  = load_assunto()
    scores0  = load_scores()
    geojson  = load_geojson()
    fv       = load_filter_vals()


# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Filtros globais
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:8px 0 14px'>"
        "<span style='font-size:1.15rem;font-weight:800;color:#1C3557'>📊 Central 156</span><br>"
        "<span style='font-size:.75rem;color:#64748B'>Painel de Priorização · Curitiba</span>"
        "</div>", unsafe_allow_html=True
    )
    st.divider()

    # ── Temporal ───────────────────────────────────────────────────────────────
    st.markdown("### 🗓 Período")

    sel_anos = st.multiselect(
        "Ano", fv['anos'],
        default=fv['anos'], key='anos',
    )

    sel_meses = st.multiselect(
        "Mês", list(range(1, 13)),
        format_func=lambda m: [
            'Jan','Fev','Mar','Abr','Mai','Jun',
            'Jul','Ago','Set','Out','Nov','Dez'][m-1],
        default=[], key='meses',
    )

    st.divider()
    # ── Territorial ────────────────────────────────────────────────────────────
    st.markdown("**🗺 Território**")
    sel_reg = st.multiselect("Regional", fv['regionais'], default=[], key='reg')
    sel_bai = st.multiselect("Bairro", fv['bairros'], default=[], key='bai')

    st.divider()
    # ── Temático ───────────────────────────────────────────────────────────────
    st.markdown("**📁 Temático**")
    sel_mac = st.multiselect(
        "Macrotema",
        fv['macrotemas'],
        format_func=lambda m: MACROTEMA_LABELS.get(m, m),
        default=[], key='mac',
    )
    sel_ass = st.multiselect("Assunto", fv['assuntos'], default=[], key='ass')
    sel_org = st.multiselect("Órgão", fv['orgaos'], default=[], key='org')

    st.divider()
    # ── Operacional ────────────────────────────────────────────────────────────
    st.markdown("**⚙ Operacional**")
    sel_cat = st.multiselect("Categoria", fv['categorias'], default=[], key='cat')
    sel_tip = st.multiselect("Tipo", fv['tipos'], default=[], key='tip')
    sel_sit = st.multiselect("Situação", fv['situacoes'], default=[], key='sit')

    st.divider()
    # ── Map metric selector ────────────────────────────────────────────────────
    st.markdown("**🗺 Métrica do mapa**")
    map_metric = st.selectbox(
        "Colorir por",
        options=['total', 'taxa_problema', 'taxa_conclusao', 'tmr'],
        format_func=lambda x: {
            'total':          'Volume total',
            'taxa_problema':  'Taxa Problema (%)',
            'taxa_conclusao': 'Taxa Conclusão (%)',
            'tmr':            'TMR mediano (dias)',
        }[x],
        key='map_metric',
    )


# ── Filtragem dinâmica ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_filtered(_df, anos, meses, regionais, bairros, macrotemas,
                 assuntos, orgaos, categorias, tipos, situacoes):
    return filter_slim(
        _df,
        anos=anos or None, meses=meses or None,
        regionais=regionais or None, bairros=bairros or None,
        macrotemas=macrotemas or None, assuntos=assuntos or None,
        orgaos=orgaos or None, categorias=categorias or None,
        tipos=tipos or None, situacoes=situacoes or None,
    )

df_f = get_filtered(
    df_slim,
    tuple(sel_anos), tuple(sel_meses), tuple(sel_reg), tuple(sel_bai),
    tuple(sel_mac), tuple(sel_ass), tuple(sel_org),
    tuple(sel_cat), tuple(sel_tip), tuple(sel_sit),
)


# ════════════════════════════════════════════════════════════════════════════════
# HEADER + KPIs TOPO
# ════════════════════════════════════════════════════════════════════════════════
kpis = compute_kpis(df_f)

def fmt_n(n):
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}k"
    return str(n)

# ── Banner de título ───────────────────────────────────────────────────────────
periodo_str = (
    f"{min(sel_anos)}–{max(sel_anos)}" if len(sel_anos) > 1
    else str(sel_anos[0]) if sel_anos else "todos os anos"
)
st.markdown(f"""
<div class="dash-header">
  <div>
    <div class="dash-header-title">📊 Painel de Priorização Dinâmica · Central 156 Curitiba</div>
    <div class="dash-header-sub">Período: {periodo_str} · {kpis['n_bairros']} bairros · filtros ativos na barra lateral</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI cards em grid ──────────────────────────────────────────────────────────
tmr_str   = f"{kpis['tmr_mediano']:.1f}d" if kpis['tmr_mediano'] else "—"
meses_str = "12 mês(es)" if not sel_meses else f"{len(sel_meses)} mês(es)"
anos_str  = f"{len(sel_anos)} ano{'s' if len(sel_anos) != 1 else ''}"

st.markdown(f"""
<div class="kpi-bar">
  <div class="kpi-card">
    <div class="kpi-lbl">📋 Manifestações</div>
    <div class="kpi-val">{fmt_n(kpis['total'])}</div>
    <div class="kpi-sub">&nbsp;</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-lbl">⚠️ Problemas</div>
    <div class="kpi-val" style="color:#C0392B">{fmt_n(kpis['n_problema'])}</div>
    <div class="kpi-sub">{kpis['taxa_problema']:.1%} do total</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-lbl">✅ Conclusão</div>
    <div class="kpi-val" style="color:#27AE60">{kpis['taxa_conclusao']:.1%}</div>
    <div class="kpi-sub">&nbsp;</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-lbl">⏱ TMR mediano</div>
    <div class="kpi-val">{tmr_str}</div>
    <div class="kpi-sub">dias</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-lbl">🏘 Bairros</div>
    <div class="kpi-val">{kpis['n_bairros']}</div>
    <div class="kpi-sub">com registros</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-lbl">📅 Período</div>
    <div class="kpi-val" style="font-size:1.3rem">{anos_str}</div>
    <div class="kpi-sub">{meses_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# Bloco reutilizável — Série Temporal (Volume mensal + Heatmap + Sumário anual)
# Usado dentro da aba "Mapa Territorial", com escopo consolidado ou por bairro.
# ════════════════════════════════════════════════════════════════════════════════
def render_bloco_serie_temporal(df_escopo: pd.DataFrame, escopo_label: str,
                                key_prefix: str = 'ts'):
    """Renderiza volume mensal + taxa de criticidade, heatmap ano×mês e
    sumário anual para o recorte de dados informado (todos os bairros ou
    apenas o bairro selecionado). Preserva integralmente os cálculos
    originais da antiga aba 'Série Temporal'."""
    ts_esc = compute_ts(df_escopo)
    if ts_esc.empty:
        st.warning("Sem dados para os filtros selecionados.")
        return

    st.markdown(
        f"<div class='sec-header'>Volume mensal e taxa de criticidade — {escopo_label}</div>",
        unsafe_allow_html=True,
    )
    show_cr = st.toggle(
        "Exibir taxa de Problema (eixo secundário)", value=True,
        key=f'{key_prefix}_show_crit',
    )
    st.plotly_chart(serie_temporal(ts_esc, show_crit=show_cr),
                    use_container_width=True)

    st.markdown(
        f"<div class='sec-header'>Heatmap ano × mês — {escopo_label}</div>",
        unsafe_allow_html=True,
    )
    if 'ano' in df_escopo.columns and 'mes' in df_escopo.columns:
        heat = (df_escopo.groupby(['ano', 'mes'])
                .size().reset_index(name='volume'))
        heat_piv = heat.pivot(index='ano', columns='mes', values='volume').fillna(0)
        heat_piv.columns = ['Jan','Fev','Mar','Abr','Mai','Jun',
                             'Jul','Ago','Set','Out','Nov','Dez']
        fig_heat = px.imshow(
            heat_piv, text_auto='.0f',
            color_continuous_scale='YlOrRd',
            aspect='auto',
        )
        fig_heat.update_traces(textfont_size=10)
        fig_heat.update_layout(
            height=340, margin=dict(t=12, b=30, l=50, r=10),
            template='plotly_white', paper_bgcolor='white',
            coloraxis_showscale=False,
            xaxis=dict(tickfont=dict(size=10)),
            yaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown(
        f"<div class='sec-header'>Sumário anual — {escopo_label}</div>",
        unsafe_allow_html=True,
    )
    yr_agg = (df_escopo.groupby('ano').agg(
        Total=('categoria_manifestacao', 'count'),
        Problemas=('categoria_manifestacao', lambda x: (x=='PROBLEMA').sum()),
        Concluídos=('situacao', lambda x: (x=='CONCLUIDO').sum()),
        TMR_mediano=('tempo_resposta_dias', 'median'),
    ).reset_index())
    yr_agg['Crit. %']  = (yr_agg['Problemas'] / yr_agg['Total'] * 100).round(1)
    yr_agg['Concl. %'] = (yr_agg['Concluídos'] / yr_agg['Total'] * 100).round(1)
    yr_agg['TMR_mediano'] = yr_agg['TMR_mediano'].round(1)
    yr_agg = yr_agg.rename(columns={'TMR_mediano': 'TMR (d)'})
    st.dataframe(
        yr_agg[['ano','Total','Problemas','Crit. %','Concl. %','TMR (d)']]
        .style.format({'Total': '{:,}', 'Problemas': '{:,}',
                       'Crit. %': '{:.1f}%', 'Concl. %': '{:.1f}%',
                       'TMR (d)': '{:.1f}'}),
        use_container_width=True, hide_index=True,
    )


# ════════════════════════════════════════════════════════════════════════════════
# ABAS
# ════════════════════════════════════════════════════════════════════════════════
tab_geral, tab_mapa, tab_temas, tab_prio = st.tabs([
    "📊 Visão Geral",
    "🗺️ Mapa Territorial",
    "🏷️ Temas & Órgãos",
    "🎯 Priorização",
])


# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — VISÃO GERAL  (grade 2×2: Composição | TMR Regional / Macrotema | Assuntos)
# ══════════════════════════════════════════════════════════════════════════════
with tab_geral:
    ALTURA_LINHA1 = 320   # altura comum da 1ª linha (rosca + TMR regional)
    ALTURA_LINHA2 = 480   # altura comum da 2ª linha (macrotema + top assuntos)

    col_esquerda, col_direita = st.columns(2, gap="large")

    with col_esquerda:
        st.markdown("<div class='sec-header'>Composição por Categoria</div>",
                    unsafe_allow_html=True)
        st.plotly_chart(pizza_categoria(df_f, height=ALTURA_LINHA1),
                        use_container_width=True)

        st.markdown("<div class='sec-header'>Volume por Macrotema</div>",
                    unsafe_allow_html=True)
        df_mac_f = compute_macrotema(df_f)
        st.plotly_chart(
            barras_macrotema(df_mac_f, height=ALTURA_LINHA2),
            use_container_width=True,
        )

    with col_direita:
        st.markdown("<div class='sec-header'>TMR Mediano por Regional</div>",
                    unsafe_allow_html=True)
        st.plotly_chart(
            barras_tmr_regional(df_f, height=ALTURA_LINHA1),
            use_container_width=True,
        )

        st.markdown("<div class='sec-header'>Top Assuntos por Volume</div>",
                    unsafe_allow_html=True)
        df_ass_f = compute_assuntos(df_f, top_n=20)
        st.plotly_chart(
            barras_assuntos(df_ass_f, height=ALTURA_LINHA2),
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — MAPA TERRITORIAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_mapa:
    map_col, panel_col = st.columns([1.65, 1], gap="medium")

    with map_col:
        st.markdown("<div class='sec-header'>Mapa Coroplético por Bairro</div>",
                    unsafe_allow_html=True)
        st.caption(
            "Selecione um bairro no mapa clicando sobre ele — "
            "o painel lateral exibirá o resumo territorial detalhado."
        )

        # Agrega mapa
        df_bai_f = compute_bairro_map(df_f)
        metric_label = {
            'total':          'Volume total',
            'taxa_problema':  'Taxa Problema (%)',
            'taxa_conclusao': 'Taxa Conclusão (%)',
            'tmr':            'TMR mediano (dias)',
        }[map_metric]

        # Bairro selecionado via state
        if 'sel_bairro' not in st.session_state:
            st.session_state['sel_bairro'] = None

        fig_map = mapa_coropletico(
            df_bai_f, geojson,
            metric=map_metric,
            metric_label=metric_label,
            selected=st.session_state['sel_bairro'],
        )
        sel_event = st.plotly_chart(
            fig_map, use_container_width=True,
            key='mapa_chart', on_select='rerun',
        )

        # Captura clique no mapa
        if sel_event and sel_event.get('selection', {}).get('points'):
            pt = sel_event['selection']['points'][0]
            clicked = pt.get('location') or pt.get('text')
            if clicked:
                st.session_state['sel_bairro'] = clicked

        # Selector manual (fallback)
        bairros_disp = sorted(df_bai_f['bairro_geo'].dropna().unique().tolist())
        sel_manual = st.selectbox(
            "Ou selecione um bairro diretamente:",
            options=[''] + bairros_disp,
            index=0,
            format_func=lambda x: '— Escolha um bairro —' if x == '' else x,
            key='sel_manual',
        )
        if sel_manual:
            st.session_state['sel_bairro'] = sel_manual

    with panel_col:
        st.markdown("<div class='sec-header'>Resumo Territorial</div>",
                    unsafe_allow_html=True)
        sel_b = st.session_state.get('sel_bairro')

        if not sel_b:
            st.info("👆 Clique em um bairro no mapa ou use o seletor para ver o resumo detalhado.")
        else:
            det = get_bairro_detail(sel_b, df_f)
            if not det:
                st.warning(f"Sem dados para **{sel_b}** com os filtros atuais.")
            else:
                # Card de resumo
                tmr_str = f"{det['tmr_mediano']:.1f} dias" if det['tmr_mediano'] else "—"
                mac_lbl = MACROTEMA_LABELS.get(det['macrotema_top'], det['macrotema_top'])
                st.markdown(f"""
<div class='bairro-panel'>
  <div class='bairro-title'>📍 {det['bairro']}</div>
  <div class='bairro-row'><span class='bairro-key'>Regional</span>
      <span class='bairro-val'>{det['regional']}</span></div>
  <div class='bairro-row'><span class='bairro-key'>Total de manifestações</span>
      <span class='bairro-val'>{det['total']:,}</span></div>
  <div class='bairro-row'><span class='bairro-key'>Taxa de Problema</span>
      <span class='bairro-val' style='color:#C0392B'>{det['taxa_problema']:.1%}</span></div>
  <div class='bairro-row'><span class='bairro-key'>TMR mediano</span>
      <span class='bairro-val'>{tmr_str}</span></div>
  <div class='bairro-row'><span class='bairro-key'>Taxa de Conclusão</span>
      <span class='bairro-val' style='color:#27AE60'>{det['taxa_conclusao']:.1%}</span></div>
  <div class='bairro-row'><span class='bairro-key'>Principal macrotema</span>
      <span class='bairro-val'>{mac_lbl}</span></div>
  <div class='bairro-row'><span class='bairro-key'>Principal Demanda</span>
      <span class='bairro-val'>{det['demanda_top']}</span></div>
  <div class='bairro-row'><span class='bairro-key'>Principal Problema</span>
      <span class='bairro-val' style='color:#C0392B'>{det['problema_top']}</span></div>
</div>
""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Top 5 assuntos neste bairro**")
                st.dataframe(
                    det['top5'].style.format({'Volume': '{:,}', 'Criticidade %': '{:.1f}%'}),
                    use_container_width=True, hide_index=True,
                )

    # ── Série Temporal (transferida da antiga aba "Série Temporal") ────────────
    # Ocupa a largura completa da página, abaixo do mapa/resumo territorial.
    # Respeita a seleção de bairro feita no mapa OU no seletor manual:
    # sem bairro selecionado → série consolidada de todos os bairros;
    # com bairro selecionado → série recalculada apenas para aquele bairro.
    st.markdown("---")
    sel_b_ts     = st.session_state.get('sel_bairro')
    df_ts_escopo = df_f[df_f['bairro_geo'] == sel_b_ts] if sel_b_ts else df_f
    escopo_label = sel_b_ts if sel_b_ts else "Todos os bairros"

    render_bloco_serie_temporal(df_ts_escopo, escopo_label, key_prefix='mapa_ts')


# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — TEMAS & ÓRGÃOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_temas:
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        st.markdown("<div class='sec-header'>Macrotemas — Criticidade (%)</div>",
                    unsafe_allow_html=True)
        df_mac_f2 = compute_macrotema(df_f)
        st.plotly_chart(
            barras_macrotema(df_mac_f2, col='crit_pct', label='Criticidade (%)'),
            use_container_width=True,
        )

    with c2:
        st.markdown("<div class='sec-header'>Órgãos responsáveis</div>",
                    unsafe_allow_html=True)
        df_org_f = compute_orgaos(df_f, top_n=15)
        st.plotly_chart(barras_orgaos(df_org_f), use_container_width=True)

    st.markdown("<div class='sec-header'>Top 20 Assuntos — Detalhe</div>",
                unsafe_allow_html=True)
    df_ass_f2 = compute_assuntos(df_f, top_n=20)
    df_table = df_ass_f2.copy()
    df_table.columns = [c.replace('_',' ').title() for c in df_table.columns]
    st.dataframe(
        df_table.style.format({
            'Total': '{:,}', 'N Prob': '{:,}',
            'Crit Pct': '{:.1f}%', 'Tmr': '{:.1f}',
        }),
        use_container_width=True, hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ABA 4 — PRIORIZAÇÃO
# ══════════════════════════════════════════════════════════════════════════════
with tab_prio:

    # ── Base de scores filtrada exclusivamente pelos filtros globais ───────────
    # A base de scores (scores0) é pré-computada por assunto × regional × mês,
    # com normalização MinMax mensal sobre TODOS os pares (metodologia
    # documentada na seção 5.2 do artigo) — por isso ela não é recalculada
    # aqui, apenas filtrada, preservando a comparabilidade da escala 0–100.
    # As colunas disponíveis nessa base são: ano, mês, regional, macrotema e
    # assunto — os filtros globais de Bairro e Órgão não se aplicam a essa
    # granularidade (a base de scores não possui essas colunas).
    scores_f = filter_scores(
        scores0,
        anos=sel_anos or None,
        meses=sel_meses or None,
        regionais=sel_reg or None,
        macrotemas=sel_mac or None,
        assuntos=sel_ass or None,
    )

    if sel_bai or sel_org:
        st.caption(
            "ℹ️ Os filtros de Bairro e Órgão da barra lateral não se aplicam "
            "a esta página: o modelo de priorização é calculado na "
            "granularidade assunto × regional × mês, sem essas dimensões."
        )

    if scores_f.empty:
        st.warning(
            "Não há dados suficientes para calcular a priorização com os "
            "filtros selecionados. Amplie o período ou remova filtros na "
            "barra lateral."
        )
    else:
        # ── 5.1 Quadrante de Risco ───────────────────────────────────────────
        st.markdown("<div class='sec-header'>Quadrante de Risco: Criticidade × SLA</div>",
                    unsafe_allow_html=True)
        st.caption("Tamanho = volume · cor = macrotema · SLA limitado em 120 dias")
        st.plotly_chart(quadrante_risco(scores_f), use_container_width=True)

        st.markdown("---")

        # ── 5.2 Race Chart ────────────────────────────────────────────────────
        st.markdown("<div class='sec-header'>🏁 Ranking Animado por Score (2020–2025)</div>",
                    unsafe_allow_html=True)
        st.caption(
            "Top 15 assuntos por score composto mês a mês · "
            "use os controles para Play, avançar/recuar ou arrastar o slider"
        )
        race_top = st.slider("Top N no race chart", 5, 20, 15, key='race_top')
        race_html = race_chart_html(scores_f, top_n=race_top)
        components.html(race_html, height=race_top * 36 + 140, scrolling=False)