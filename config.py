"""
config.py — Constantes, paletas e mapeamentos do Dashboard Central 156.
Centraliza tudo o que é reutilizado em múltiplos módulos.
"""
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DATA_DIR   = ROOT / "data"
ASSETS_DIR = ROOT / "assets"

# Cache files (gerados por prepare_cache.py)
CACHE_TS       = DATA_DIR / "cache_ts.parquet"
CACHE_BAIRRO   = DATA_DIR / "cache_bairro.parquet"
CACHE_BAIRRO_S = DATA_DIR / "cache_bairro_summary.parquet"
CACHE_MAC      = DATA_DIR / "cache_macrotema.parquet"
CACHE_ASS      = DATA_DIR / "cache_assunto.parquet"
CACHE_SLIM     = DATA_DIR / "cache_slim.parquet"
CACHE_SCORES   = DATA_DIR / "cache_scores.parquet"
FILTER_VALS    = DATA_DIR / "filter_vals.json"
GEOJSON_PATH   = ASSETS_DIR / "bairros_geo.json"

# ── Mappings ───────────────────────────────────────────────────────────────────
BAIRRO_MAP: dict[str, str] = {
    'AGUA VERDE':'ÁGUA VERDE','JARDIM DAS AMERICAS':'JARDIM DAS AMÉRICAS',
    'GUAIRA':'GUAÍRA','SAO FRANCISCO':'SÃO FRANCISCO','ALTO DA GLORIA':'ALTO DA GLÓRIA',
    'LINDOIA':'LINDÓIA','CENTRO CIVICO':'CENTRO CÍVICO','JUVEVE':'JUVEVÊ',
    'CAPAO DA IMBUIA':'CAPÃO DA IMBUIA','SEMINARIO':'SEMINÁRIO','PORTAO':'PORTÃO',
    'AHU':'AHÚ','REBOUCAS':'REBOUÇAS','MOSSUNGUE':'MOSSUNGUÊ',
    'JARDIM BOTANICO':'JARDIM BOTÂNICO','BOQUEIRAO':'BOQUEIRÃO',
    'SITIO CERCADO':'SÍTIO CERCADO','TARUMA':'TARUMÃ','SAO LOURENCO':'SÃO LOURENÇO',
    'CAPAO RASO':'CAPÃO RASO','SANTA QUITERIA':'SANTA QUITÉRIA','SAO MIGUEL':'SÃO MIGUEL',
    'ALTO BOQUEIRAO':'ALTO BOQUEIRÃO','UMBARA':'UMBARÁ','TABOAO':'TABOÃO',
    'SANTA CANDIDA':'SANTA CÂNDIDA','CIDADE INDUSTRIAL':'CIDADE INDUSTRIAL DE CURITIBA',
    'MERCES':'MERCÊS','SANTO INACIO':'SANTO INÁCIO','SAO BRAZ':'SÃO BRAZ',
    'SAO JOAO':'SÃO JOÃO',
}

REGIONAL_MAP: dict[str, str] = {
    'UNIDADE REGIONAL MATRIZ':'Matriz',
    'UNIDADE REGIONAL BOA VISTA':'Boa Vista',
    'UNIDADE REGIONAL PORTAO':'Portão',
    'UNIDADE REGIONAL CAJURU':'Cajuru',
    'UNIDADE REGIONAL BOQUEIRAO':'Boqueirão',
    'UNIDADE REGIONAL PINHEIRINHO':'Pinheirinho',
    'UNIDADE REGIONAL SANTA FELICIDADE':'Santa Felicidade',
    'UNIDADE REGIONAL CIC':'CIC',
    'UNIDADE REGIONAL BAIRRO NOVO':'Bairro Novo',
    'UNIDADE REGIONAL TATUQUARA':'Tatuquara',
}

# ── Paletas ────────────────────────────────────────────────────────────────────
MACROTEMA_COLORS: dict[str, str] = {
    'SAUDE':'#E74C3C','TRANSPORTE_COLETIVO':'#C0392B',
    'EDUCACAO':'#E67E22','LIMPEZA_URBANA':'#27AE60',
    'INFRAESTRUTURA_URBANA':'#2980B9','MOBILIDADE_TRANSITO':'#8E44AD',
    'MEIO_AMBIENTE':'#16A085','ASSISTENCIA_SOCIAL_DIREITOS':'#F39C12',
    'TRIBUTOS_FINANCAS_JURIDICO':'#5D6D7E','SEGURANCA_PUBLICA':'#2C3E50',
    'SEGURANCA_ALIMENTAR_ABASTECIMENTO':'#D35400','URBANISMO_FISCALIZACAO':'#1ABC9C',
    'ADMINISTRATIVO_RH':'#95A5A6','TECNOLOGIA_CANAIS_DIGITAIS':'#3498DB',
    'CULTURA_LAZER_TURISMO':'#9B59B6','ATENDIMENTO_INFORMACAO':'#48C9B0',
    'HABITACAO':'#A04000','EMPREGO_DESENVOLVIMENTO':'#839192','OUTROS':'#BDC3C7',
}

MACROTEMA_LABELS: dict[str, str] = {
    'SAUDE':'Saúde','TRANSPORTE_COLETIVO':'Transporte Coletivo',
    'EDUCACAO':'Educação','LIMPEZA_URBANA':'Limpeza Urbana',
    'INFRAESTRUTURA_URBANA':'Infraestrutura Urbana','MOBILIDADE_TRANSITO':'Mobilidade e Trânsito',
    'MEIO_AMBIENTE':'Meio Ambiente','ASSISTENCIA_SOCIAL_DIREITOS':'Assistência Social e Direitos',
    'TRIBUTOS_FINANCAS_JURIDICO':'Tributos / Jurídico','SEGURANCA_PUBLICA':'Segurança Pública',
    'SEGURANCA_ALIMENTAR_ABASTECIMENTO':'Seg. Alimentar e Abastecimento',
    'URBANISMO_FISCALIZACAO':'Urbanismo / Fiscalização','ADMINISTRATIVO_RH':'Administrativo / RH',
    'TECNOLOGIA_CANAIS_DIGITAIS':'Tecnologia e Canais Digitais',
    'CULTURA_LAZER_TURISMO':'Cultura, Lazer e Turismo','ATENDIMENTO_INFORMACAO':'Atendimento / Informação',
    'HABITACAO':'Habitação','EMPREGO_DESENVOLVIMENTO':'Emprego e Desenvolvimento','OUTROS':'Outros',
}

REGIONAL_COLORS: dict[str, str] = {
    'Matriz':'#0D7377','Boa Vista':'#14A085','Portão':'#1B6CA8','Cajuru':'#E67E22',
    'Boqueirão':'#8E44AD','Pinheirinho':'#C0392B','Santa Felicidade':'#2980B9',
    'CIC':'#7F8C8D','Bairro Novo':'#E74C3C','Tatuquara':'#922B21',
}

# ── UI tokens ──────────────────────────────────────────────────────────────────
PRIMARY   = '#0D7377'
DANGER    = '#C0392B'
WARNING   = '#E67E22'
SUCCESS   = '#27AE60'
NEUTRAL   = '#64748B'

# ── Padrão visual unificado (rosca / barras) ────────────────────────────────────
# Cores fixas por categoria de manifestação — usadas no gráfico de rosca da
# "Visão Geral". A ordem do dict reflete a ordem lógica desejada na legenda:
# Demanda, Problema, Elogio, Outros.
CORES_CATEGORIAS: dict[str, str] = {
    'DEMANDA':  '#3184bb',
    'PROBLEMA': '#cd6155',
    'ELOGIO':   '#45b39d',
    'OUTROS':   '#cccccc',
}
CATEGORIA_ORDEM: list[str] = ['DEMANDA', 'PROBLEMA', 'ELOGIO', 'OUTROS']

# Cor sólida padrão para gráficos de barras + cor de destaque (seleção/realce)
COR_BARRA_PADRAO   = '#004561'
COR_BARRA_DESTAQUE = '#e36414'

# Paleta de referência geral do dashboard
CORES_DASHBOARD: dict[str, str] = {
    'azul_escuro': '#004561',
    'azul':        '#3184bb',
    'laranja':     '#e36414',
    'vermelho':    '#cd6155',
    'verde':       '#45b39d',
    'cinza':       '#cccccc',
}

# ── Thresholds ─────────────────────────────────────────────────────────────────
P99_TMR   = 464   # corte de outlier TMR (dias)
VOL_MIN   = 30    # volume mínimo para incluir no score/race chart
