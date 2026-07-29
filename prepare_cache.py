"""
prepare_cache.py — Pré-agrega o gold.parquet em caches menores.
Execute UMA VEZ antes de iniciar o dashboard.

Uso:
    python prepare_cache.py --gold caminho/para/central156_gold.parquet
                            --scores caminho/para/geo_scores_monthly.parquet
"""
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    DATA_DIR, BAIRRO_MAP, REGIONAL_MAP, P99_TMR,
    CACHE_TS, CACHE_BAIRRO, CACHE_BAIRRO_S, CACHE_MAC,
    CACHE_ASS, CACHE_SLIM, CACHE_SCORES, FILTER_VALS,
)


def main(gold_path: Path, scores_path: Path):
    t0 = time.time()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[1/7] Lendo {gold_path} …")
    cols = ['ano','mes','ano_mes','bairro','regional','macrotema',
            'assunto_padronizado','orgao_padronizado','categoria_manifestacao',
            'tipo','situacao','tempo_resposta_dias']
    df = pd.read_parquet(gold_path, columns=cols)
    df = df[df['categoria_manifestacao'] != 'OUTROS'].copy()
    df['bairro_geo']     = df['bairro'].map(BAIRRO_MAP).fillna(df['bairro'])
    df['regional_label'] = df['regional'].map(REGIONAL_MAP).fillna(df['regional'])
    mask = df['tempo_resposta_dias'].notna() & (df['tempo_resposta_dias'] >= 0)
    df.loc[mask & (df['tempo_resposta_dias'] > P99_TMR), 'tempo_resposta_dias'] = np.nan
    print(f"  → {len(df):,} registros")

    print("[2/7] Série temporal mensal …")
    ts = df.groupby('ano_mes').agg(
        total =('categoria_manifestacao', 'count'),
        n_prob=('categoria_manifestacao', lambda x: (x=='PROBLEMA').sum()),
        n_conc=('situacao', lambda x: (x=='CONCLUIDO').sum()),
        tmr   =('tempo_resposta_dias', 'median'),
    ).reset_index()
    ts.to_parquet(CACHE_TS, index=False)

    print("[3/7] Agregação por bairro …")
    bb = df.groupby(['bairro_geo','regional_label']).agg(
        total =('categoria_manifestacao', 'count'),
        n_prob=('categoria_manifestacao', lambda x: (x=='PROBLEMA').sum()),
        n_conc=('situacao', lambda x: (x=='CONCLUIDO').sum()),
        tmr   =('tempo_resposta_dias', 'median'),
    ).reset_index()
    bb['taxa_problema']  = (bb['n_prob'] / bb['total'] * 100).round(1)
    bb['taxa_conclusao'] = (bb['n_conc'] / bb['total'] * 100).round(1)
    bb['tmr'] = bb['tmr'].round(1)
    bb.to_parquet(CACHE_BAIRRO, index=False)

    print("[4/7] Sumário por bairro (para painel lateral) …")
    rows = []
    for bairro, grp in df.groupby('bairro_geo'):
        n = len(grp)
        np_ = (grp['categoria_manifestacao']=='PROBLEMA').sum()
        nc  = (grp['situacao']=='CONCLUIDO').sum()
        tmr = grp['tempo_resposta_dias'].median()
        reg = grp['regional_label'].mode().iloc[0] if not grp['regional_label'].empty else ''
        mac = grp['macrotema'].value_counts().index[0] if n else ''
        dem = grp.loc[grp['categoria_manifestacao']=='DEMANDA','assunto_padronizado'].value_counts()
        prb = grp.loc[grp['categoria_manifestacao']=='PROBLEMA','assunto_padronizado'].value_counts()
        rows.append({
            'bairro_geo':     bairro,
            'regional':       reg,
            'total':          int(n),
            'n_problema':     int(np_),
            'n_concluido':    int(nc),
            'tmr_mediano':    float(round(tmr,1)) if pd.notna(tmr) else None,
            'taxa_problema':  round(np_/n,4) if n else 0,
            'taxa_conclusao': round(nc/n,4) if n else 0,
            'macrotema_top':  mac,
            'demanda_top':    dem.index[0] if len(dem) else '',
            'problema_top':   prb.index[0] if len(prb) else '',
        })
    pd.DataFrame(rows).to_parquet(CACHE_BAIRRO_S, index=False)

    print("[5/7] Agregação macrotema e assunto …")
    mac = df.groupby(['macrotema','regional_label']).agg(
        total  = ('categoria_manifestacao', 'count'),
        n_prob = ('categoria_manifestacao', lambda x: (x=='PROBLEMA').sum()),
        tmr    = ('tempo_resposta_dias', 'median'),
    ).reset_index()
    mac['crit_pct'] = (mac['n_prob'] / mac['total'] * 100).round(1)
    mac.to_parquet(CACHE_MAC, index=False)

    ass = df.groupby(['assunto_padronizado','macrotema','orgao_padronizado']).agg(
        total  = ('categoria_manifestacao', 'count'),
        n_prob = ('categoria_manifestacao', lambda x: (x=='PROBLEMA').sum()),
        tmr    = ('tempo_resposta_dias', 'median'),
    ).reset_index()
    ass['crit_pct'] = (ass['n_prob'] / ass['total'] * 100).round(1)
    ass.to_parquet(CACHE_ASS, index=False)

    print("[6/7] Cache slim para filtragem dinâmica …")
    slim = df[['ano','mes','ano_mes','bairro_geo','regional_label','macrotema',
            'assunto_padronizado','orgao_padronizado','categoria_manifestacao',
            'tipo','situacao','tempo_resposta_dias']].copy()

    # Converte colunas de texto repetitivo para category — reduz uso de RAM
    # em runtime (Streamlit Cloud tem limite de 2.7GB no plano gratuito).
    cat_cols = ['bairro_geo','regional_label','macrotema','assunto_padronizado',
                'orgao_padronizado','categoria_manifestacao','tipo','situacao']
    for c in cat_cols:
        slim[c] = slim[c].astype('category')

    slim.to_parquet(CACHE_SLIM, index=False)

    print("[7/7] Scores mensais e valores de filtro …")
    if scores_path.exists():
        pd.read_parquet(scores_path).to_parquet(CACHE_SCORES, index=False)
    else:
        print(f"  ⚠ {scores_path} não encontrado — scores não serão disponíveis.")

    import json
    fv = {
        'anos':      sorted(df['ano'].dropna().unique().tolist()),
        'meses':     sorted(df['mes'].dropna().unique().tolist()),
        'regionais': sorted(df['regional_label'].dropna().unique().tolist()),
        'bairros':   sorted(df['bairro_geo'].dropna().unique().tolist()),
        'macrotemas':sorted(df['macrotema'].dropna().unique().tolist()),
        'assuntos':  sorted(df['assunto_padronizado'].dropna().unique().tolist()),
        'orgaos':    sorted(df['orgao_padronizado'].dropna().unique().tolist()),
        'categorias':sorted(df['categoria_manifestacao'].dropna().unique().tolist()),
        'tipos':     sorted(df['tipo'].dropna().unique().tolist()),
        'situacoes': sorted(df['situacao'].dropna().unique().tolist()),
    }
    with open(FILTER_VALS, 'w', encoding='utf-8') as f:
        json.dump(fv, f, ensure_ascii=False)

    elapsed = time.time() - t0
    print(f"\n✓ Cache gerado em {elapsed:.1f}s → {DATA_DIR}/")
    for p in sorted(DATA_DIR.glob('*.parquet')):
        print(f"  {p.name:40s} {p.stat().st_size/1024:.0f} KB")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--gold',   type=Path,
                    default=Path('data/central156_gold.parquet'))
    ap.add_argument('--scores', type=Path,
                    default=Path('data/geo_scores_monthly.parquet'))
    args = ap.parse_args()
    main(args.gold, args.scores)
