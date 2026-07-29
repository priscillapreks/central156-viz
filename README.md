# Dashboard de Priorização Dinâmica · Central 156 Curitiba

Painel Streamlit para exploração interativa dos dados da Central 156 de Curitiba.

## Estrutura

```
dashboard156/
├── app.py              # Aplicação principal Streamlit
├── config.py           # Constantes, paletas e mapeamentos
├── data_loader.py      # Carga com cache, filtragem e agregações
├── charts.py           # Todos os componentes visuais (Plotly + D3)
├── prepare_cache.py    # Geração do cache pré-agregado (rodar 1x)
├── requirements.txt
├── data/
│   ├── cache_slim.parquet       ← versão slim do gold para filtragem
│   ├── cache_ts.parquet         ← série temporal mensal
│   ├── cache_bairro.parquet     ← métricas por bairro (mapa)
│   ├── cache_bairro_summary.parquet ← resumo territorial por bairro
│   ├── cache_macrotema.parquet  ← por macrotema × regional
│   ├── cache_assunto.parquet    ← por assunto padronizado
│   ├── cache_scores.parquet     ← scores mensais geo (priority model)
│   └── filter_vals.json         ← valores únicos para os filtros
└── assets/
    └── bairros_geo.json         ← GeoJSON dos 75 bairros
```

## Execução

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Gerar cache pré-agregado (UMA VEZ — ~3 min na primeira vez)
python prepare_cache.py \
  --gold   /caminho/para/central156_gold.parquet \
  --scores /caminho/para/geo_scores_monthly.parquet

# 3. Iniciar dashboard
streamlit run app.py
```

## Abas do Dashboard

| Aba | Conteúdo |
|-----|----------|
| 📊 Visão Geral | Macrotemas, TMR por regional, categoria, top assuntos |
| 🗺️ Mapa Territorial | Choropleth + painel lateral por bairro |
| 📈 Série Temporal | Volume mensal, heatmap ano×mês, tabela anual |
| 🏷️ Temas & Órgãos | Criticidade por macrotema, top órgãos, tabela de assuntos |
| 🎯 Priorização | Ranking global, score timeline, quadrante de risco, race chart |

## Filtros disponíveis

- Período: Ano(s) / Mês(es)
- Território: Regional / Bairro
- Temático: Macrotema / Assunto / Órgão
- Operacional: Categoria / Tipo / Situação

## Score composto

```
priority = 0.35 × criticidade + 0.25 × log(volume) + 0.25 × SLA + 0.15 × (1 − encerramento)
```
Normalizado mensalmente via MinMaxScaler → escala 0–100.
