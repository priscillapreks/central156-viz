"""
data_loader.py — Carga com cache Streamlit e filtragem dinâmica.

Estratégia de performance:
- Dados pré-agregados (cache_*.parquet) são carregados uma vez por sessão
- Para filtros ad-hoc, usa cache_slim.parquet (28 MB vs 190 MB do gold)
- Filtros vetorizados com pandas booleanos evitam loops
"""
import json
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st

from config import (
    CACHE_TS, CACHE_BAIRRO, CACHE_BAIRRO_S, CACHE_MAC,
    CACHE_ASS, CACHE_SLIM, CACHE_SCORES, FILTER_VALS,
    GEOJSON_PATH, P99_TMR,
)


# ── Cargas com cache ───────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_slim() -> pd.DataFrame:
    """Versão slim do gold: apenas colunas necessárias para filtragem."""
    df = pd.read_parquet(CACHE_SLIM)
    # TMR clip
    mask = df['tempo_resposta_dias'].notna() & (df['tempo_resposta_dias'] >= 0)
    df.loc[mask & (df['tempo_resposta_dias'] > P99_TMR), 'tempo_resposta_dias'] = np.nan
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def load_ts() -> pd.DataFrame:
    df = pd.read_parquet(CACHE_TS)
    df['ano_mes_dt'] = pd.to_datetime(df['ano_mes'] + '-01')
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def load_bairro() -> pd.DataFrame:
    return pd.read_parquet(CACHE_BAIRRO)

@st.cache_data(ttl=3600, show_spinner=False)
def load_bairro_summary() -> pd.DataFrame:
    return pd.read_parquet(CACHE_BAIRRO_S)

@st.cache_data(ttl=3600, show_spinner=False)
def load_macrotema() -> pd.DataFrame:
    return pd.read_parquet(CACHE_MAC)

@st.cache_data(ttl=3600, show_spinner=False)
def load_assunto() -> pd.DataFrame:
    return pd.read_parquet(CACHE_ASS)

@st.cache_data(ttl=3600, show_spinner=False)
def load_scores() -> pd.DataFrame:
    df = pd.read_parquet(CACHE_SCORES)
    df['ano']  = df['ano_mes'].str[:4].astype(int)
    df['mes']  = df['ano_mes'].str[5:7].astype(int)
    from config import REGIONAL_MAP
    df['regional_label'] = df['regional'].map(REGIONAL_MAP).fillna(df['regional'])
    return df

@st.cache_data(ttl=None, show_spinner=False)
def load_geojson() -> dict:
    with open(GEOJSON_PATH, encoding='utf-8') as f:
        return json.load(f)

@st.cache_data(ttl=None, show_spinner=False)
def load_filter_vals() -> dict:
    with open(FILTER_VALS, encoding='utf-8') as f:
        return json.load(f)


# ── Filtragem dinâmica ─────────────────────────────────────────────────────────

def filter_slim(
    df: pd.DataFrame,
    anos: Optional[list] = None,
    meses: Optional[list] = None,
    regionais: Optional[list] = None,
    bairros: Optional[list] = None,
    macrotemas: Optional[list] = None,
    assuntos: Optional[list] = None,
    orgaos: Optional[list] = None,
    categorias: Optional[list] = None,
    tipos: Optional[list] = None,
    situacoes: Optional[list] = None,
) -> pd.DataFrame:
    """Aplica filtros vetorizados ao slim parquet."""
    mask = pd.Series(True, index=df.index)
    if anos:       mask &= df['ano'].isin(anos)
    if meses:      mask &= df['mes'].isin(meses)
    if regionais:  mask &= df['regional_label'].isin(regionais)
    if bairros:    mask &= df['bairro_geo'].isin(bairros)
    if macrotemas: mask &= df['macrotema'].isin(macrotemas)
    if assuntos:   mask &= df['assunto_padronizado'].isin(assuntos)
    if orgaos:     mask &= df['orgao_padronizado'].isin(orgaos)
    if categorias: mask &= df['categoria_manifestacao'].isin(categorias)
    if tipos:      mask &= df['tipo'].isin(tipos)
    if situacoes:  mask &= df['situacao'].isin(situacoes)
    return df[mask]


def filter_scores(
    scores: pd.DataFrame,
    anos: Optional[list] = None,
    meses: Optional[list] = None,
    regionais: Optional[list] = None,
    macrotemas: Optional[list] = None,
    assuntos: Optional[list] = None,
    vol_min: int = 30,
) -> pd.DataFrame:
    """Filtra a base pré-computada de scores (assunto × regional × mês).
    Aceita apenas os recortes cujas colunas existem nessa base — ano, mês,
    regional, macrotema e assunto. Bairro e órgão não existem nessa
    granularidade (o score é calculado por assunto × regional × mês, ver
    metodologia na seção 5.2 do artigo) e por isso não são parâmetros aqui."""
    mask = scores['volume'] >= vol_min
    if anos:       mask &= scores['ano'].isin(anos)
    if meses:      mask &= scores['mes'].isin(meses)
    if regionais:  mask &= scores['regional_label'].isin(regionais)
    if macrotemas: mask &= scores['macrotema'].isin(macrotemas)
    if assuntos:   mask &= scores['assunto_padronizado'].isin(assuntos)
    return scores[mask]


# ── Agregações sob demanda ─────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    total   = len(df)
    n_prob  = (df['categoria_manifestacao'] == 'PROBLEMA').sum()
    n_conc  = (df['situacao'] == 'CONCLUIDO').sum()
    tmr_med = df['tempo_resposta_dias'].median()
    return {
        'total':          int(total),
        'n_problema':     int(n_prob),
        'taxa_problema':  round(n_prob / total, 4) if total else 0,
        'taxa_conclusao': round(n_conc / total, 4) if total else 0,
        'tmr_mediano':    float(round(tmr_med, 1)) if pd.notna(tmr_med) else None,
        'n_bairros':      int(df['bairro_geo'].nunique()),
    }


def compute_ts(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby('ano_mes').agg(
        total  = ('categoria_manifestacao', 'count'),
        n_prob = ('categoria_manifestacao', lambda x: (x == 'PROBLEMA').sum()),
        n_conc = ('situacao', lambda x: (x == 'CONCLUIDO').sum()),
        tmr    = ('tempo_resposta_dias', 'median'),
    ).reset_index()
    agg['taxa_problema']  = agg['n_prob'] / agg['total']
    agg['taxa_conclusao'] = agg['n_conc'] / agg['total']
    agg['ano_mes_dt'] = pd.to_datetime(agg['ano_mes'] + '-01')
    return agg.sort_values('ano_mes_dt')


def compute_bairro_map(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega por bairro para o mapa coroplético.

    IMPORTANTE: agrupamos apenas por 'bairro_geo' (não por regional_label
    também). Alguns bairros têm registros sob mais de um regional (erro de
    cadastro/endereço) — agrupar pelos dois campos gera linhas duplicadas
    para o mesmo bairro, e o Plotly (que casa por nome via featureidkey)
    passa a exibir hover inconsistente/errado para esses casos. Aqui
    calculamos o regional predominante (moda) apenas para exibição.
    """
    agg = df.groupby('bairro_geo').agg(
        total          = ('categoria_manifestacao', 'count'),
        n_prob         = ('categoria_manifestacao', lambda x: (x == 'PROBLEMA').sum()),
        n_conc         = ('situacao', lambda x: (x == 'CONCLUIDO').sum()),
        tmr            = ('tempo_resposta_dias', 'median'),
        regional_label = ('regional_label',
                           lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]),
    ).reset_index()
    agg['taxa_problema']  = (agg['n_prob'] / agg['total'] * 100).round(1)
    agg['taxa_conclusao'] = (agg['n_conc'] / agg['total'] * 100).round(1)
    agg['tmr']            = agg['tmr'].round(1)
    return agg


def compute_macrotema(df: pd.DataFrame, top_n: int = 18) -> pd.DataFrame:
    agg = df.groupby('macrotema').agg(
        total  = ('categoria_manifestacao', 'count'),
        n_prob = ('categoria_manifestacao', lambda x: (x == 'PROBLEMA').sum()),
        tmr    = ('tempo_resposta_dias', 'median'),
    ).reset_index()
    agg['crit_pct'] = (agg['n_prob'] / agg['total'] * 100).round(1)
    return agg.nlargest(top_n, 'total')


def compute_assuntos(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    agg = df.groupby(['assunto_padronizado', 'macrotema', 'orgao_padronizado']).agg(
        total  = ('categoria_manifestacao', 'count'),
        n_prob = ('categoria_manifestacao', lambda x: (x == 'PROBLEMA').sum()),
        tmr    = ('tempo_resposta_dias', 'median'),
    ).reset_index()
    agg['crit_pct'] = (agg['n_prob'] / agg['total'] * 100).round(1)
    return agg.nlargest(top_n, 'total')


def compute_orgaos(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    agg = df.groupby('orgao_padronizado').agg(
        total  = ('categoria_manifestacao', 'count'),
        n_prob = ('categoria_manifestacao', lambda x: (x == 'PROBLEMA').sum()),
        tmr    = ('tempo_resposta_dias', 'median'),
        n_conc = ('situacao', lambda x: (x == 'CONCLUIDO').sum()),
    ).reset_index()
    agg['crit_pct']       = (agg['n_prob'] / agg['total'] * 100).round(1)
    agg['taxa_conclusao'] = (agg['n_conc'] / agg['total'] * 100).round(1)
    return agg.nlargest(top_n, 'total')


def get_bairro_detail(bairro_geo: str, df: pd.DataFrame) -> dict:
    """Resumo territorial detalhado para o painel lateral."""
    sub = df[df['bairro_geo'] == bairro_geo]
    if sub.empty:
        return {}
    total   = len(sub)
    n_prob  = (sub['categoria_manifestacao'] == 'PROBLEMA').sum()
    n_conc  = (sub['situacao'] == 'CONCLUIDO').sum()
    tmr_med = sub['tempo_resposta_dias'].median()
    regional = sub['regional_label'].mode().iloc[0] if not sub['regional_label'].empty else '—'

    mac_vc   = sub['macrotema'].value_counts()
    dem_vc   = sub.loc[sub['categoria_manifestacao']=='DEMANDA', 'assunto_padronizado'].value_counts()
    prob_vc  = sub.loc[sub['categoria_manifestacao']=='PROBLEMA', 'assunto_padronizado'].value_counts()

    top5 = sub['assunto_padronizado'].value_counts().head(5).reset_index()
    top5.columns = ['Assunto', 'Volume']
    top5['Criticidade %'] = top5['Assunto'].map(
        lambda a: round(
            (sub[(sub['assunto_padronizado']==a) & (sub['categoria_manifestacao']=='PROBLEMA')].shape[0]
             / max(sub[sub['assunto_padronizado']==a].shape[0], 1)) * 100, 1
        )
    )

    return {
        'bairro':          bairro_geo,
        'regional':        regional,
        'total':           int(total),
        'n_problema':      int(n_prob),
        'taxa_problema':   round(n_prob / total, 4) if total else 0,
        'tmr_mediano':     float(round(tmr_med, 1)) if pd.notna(tmr_med) else None,
        'taxa_conclusao':  round(n_conc / total, 4) if total else 0,
        'macrotema_top':   mac_vc.index[0] if len(mac_vc) else '—',
        'demanda_top':     dem_vc.index[0] if len(dem_vc) else '—',
        'problema_top':    prob_vc.index[0] if len(prob_vc) else '—',
        'top5':            top5,
    }
