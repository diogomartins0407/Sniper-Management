import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAÇÕES DO FUNDO ---
st.set_page_config(page_title="Sniper Quant Dashboard", layout="wide")

# ============================================================
# CSS GLOBAL - PADRAO DEEP QUANT (fonte padrao Streamlit + tema dark)
# ============================================================
DEEP_QUANT_CSS = """
<style>
/* === FUNDO E TEXTO (Deep Quant dark) === */
[data-testid="stAppViewContainer"] {
    background-color: #0D1117 !important;
}
[data-testid="stHeader"] {
    background-color: #0D1117 !important;
}
[data-testid="stSidebar"] {
    background-color: #161B22 !important;
    border-right: 1px solid #30363D;
}
.stMarkdown, .stText, p, span, div, label {
    color: #E6EDF3;
}
h1, h2, h3, h4, h5, h6 {
    color: #E6EDF3 !important;
    font-weight: bold !important;
}

/* === CARDS DE METRICAS (mantem setas ↑↓ do delta) === */
[data-testid="stMetric"] {
    background-color: transparent;
    padding: 8px 4px 4px 0;
}
[data-testid="stMetricLabel"] {
    color: #8B949E !important;
    font-size: 0.85em !important;
    font-weight: normal !important;
}
[data-testid="stMetricValue"] {
    color: #E6EDF3 !important;
    font-weight: bold !important;
    font-size: 2em !important;
}
[data-testid="stMetricDelta"] {
    font-weight: bold !important;
}

/* === DATAFRAMES / TABELAS === */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border-radius: 5px;
    border: 1px solid #30363D;
    overflow: hidden;
}
[data-testid="stDataFrame"] th {
    background-color: #161B22 !important;
    color: #8B949E !important;
    font-weight: bold !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-size: 0.75em;
}
[data-testid="stDataFrame"] td {
    color: #E6EDF3 !important;
    background-color: #0D1117 !important;
    border-bottom: 1px solid #21262D !important;
}

/* === BOTOES === */
.stButton > button {
    background-color: #161B22;
    color: #E6EDF3;
    border: 1px solid #30363D;
    border-radius: 5px;
    font-weight: bold;
}
.stButton > button:hover {
    border-color: #39FF14;
    color: #39FF14;
}

/* === INPUTS === */
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background-color: #161B22 !important;
    color: #E6EDF3 !important;
    border: 1px solid #30363D !important;
    border-radius: 5px !important;
}

/* === EXPANDERS === */
[data-testid="stExpander"] {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 5px;
}

/* === CAPTIONS E CODE === */
.stCaption {
    color: #8B949E !important;
    font-size: 0.85em;
}
code {
    background-color: #161B22 !important;
    color: #39FF14 !important;
    border: 1px solid #30363D;
    border-radius: 3px;
    padding: 2px 6px;
}

/* === DIVIDER === */
hr {
    border-color: #30363D !important;
    margin: 12px 0 !important;
}
</style>
"""
st.markdown(DEEP_QUANT_CSS, unsafe_allow_html=True)

# ============================================================
# CONFIGURACAO DE FASES DO FUNDO
# ============================================================
# FASE 1: Base original (encerrada). Capital R$ 5.000, 50 cotas.
CAPITAL_INICIAL_FASE1 = 5000.0
COTAS_INICIAIS_FASE1 = 50.0

# FASE 1: Encerrada em 10/06/2026
DATA_FIM_FASE1 = pd.Timestamp("2026-06-10")

# FASE 2: Recomeco em 17/07/2026 apos pausa. Herda patrimonio final da Fase 1.
# Mesmo numero de cotas -> valor da cota Fase 2 comeca com valor final da Fase 1.
COTAS_INICIAIS_FASE2 = 50.0
DATA_INICIO_FASE2 = pd.Timestamp("2026-07-17")

# URLs das abas publicadas em CSV
URL_GOOGLE_SHEETS_FASE1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSk4E78PHBBrCfP0_Ixd_GmhVBiN5dSgdR1dZU6mCXdbK28YPU4CvBut1CZxE9Q_1xLkJOGZe6xX13z/pub?gid=610498100&single=true&output=csv"

URL_GOOGLE_SHEETS_FASE2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSk4E78PHBBrCfP0_Ixd_GmhVBiN5dSgdR1dZU6mCXdbK28YPU4CvBut1CZxE9Q_1xLkJOGZe6xX13z/pub?gid=1751063052&single=true&output=csv"

# Retrocompat: mantido para nao quebrar codigo antigo
CAPITAL_INICIAL = CAPITAL_INICIAL_FASE1
COTAS_INICIAIS = COTAS_INICIAIS_FASE1

# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=300)  # Cache para deixar o painel rapido
def carregar_dados(url_planilha, _versao_cache="v2_fases"):
    """Le os dados de uma aba da planilha Google Sheets.
    url_planilha vira parte da chave do cache - alterna Fase 1/Fase 2 automaticamente.
    """
    URL_GOOGLE_SHEETS = url_planilha  # parametro dinamico
    try:
        # read_csv tolerante: engine python + skip de linhas mal-formadas
        # (algumas linhas do CSV podem ter mais colunas que o header, ex: virgulas
        # em campos de texto). engine="python" + on_bad_lines="skip" evita crash.
        df_gs = pd.read_csv(URL_GOOGLE_SHEETS, engine="python", on_bad_lines="skip")
        # Remove linhas vazias baseadas na Coluna Data e Ativo
        df_gs = df_gs.dropna(subset=[df_gs.columns[1], df_gs.columns[2]])
        
        trades_gs = []
        ano_atual = str(datetime.now().year)
        
        for i, row in df_gs.iterrows():
            try:
                data_str = str(row.iloc[1]).strip()
                if "/" not in data_str: continue # Pula linhas mortas
                
                ativo = str(row.iloc[2]).upper().strip()
                
                # Tratamento seguro do IFR
                ifr_str = str(row.iloc[3]).replace(',', '.').strip()
                ifr = float(ifr_str) if ifr_str and ifr_str.lower() != 'nan' else 0.0
                
                # 🛡️ A NOVA FUNÇÃO BLINDADA PARA LER DINHEIRO
                def limpa_moeda(val):
                    # Remove R$, espaços e caracteres invisíveis (resolve o erro do "- 50,40")
                    v = str(val).replace('R$', '').replace(' ', '').replace('\xa0', '').strip()
                    if not v or v == '-': return 0.0
                    # Converte milhar e decimal do padrão BR para EUA
                    v = v.replace('.', '').replace(',', '.')
                    try:
                        return float(v)
                    except:
                        return 0.0
                        
                preco_compra = limpa_moeda(row.iloc[4])
                
                # Tratamento seguro da Quantidade (BLINDADO contra bug x10)
                # Bug antigo: str(90.0).replace('.','')="900" -> quantidade x10
                # Fix: preserva ponto decimal quando nao ha virgula (formato EUA/pandas)
                qtd_raw = row.iloc[6]
                if pd.isna(qtd_raw):
                    qtd = 0
                else:
                    qtd_str = str(qtd_raw).replace(' ', '').replace('\xa0', '').strip()
                    if not qtd_str or qtd_str.lower() == 'nan':
                        qtd = 0
                    elif ',' in qtd_str:
                        # Formato BR: "1.500,00" -> milhar (ponto) + decimal (virgula)
                        qtd_str = qtd_str.replace('.', '').replace(',', '.')
                        qtd = int(float(qtd_str))
                    else:
                        # Formato EUA / pandas float: "90.0" ou "90" -> ponto e decimal
                        try:
                            qtd = int(float(qtd_str))
                        except ValueError:
                            qtd = 0
                
                # Data de Compra (Força padrão Dia/Mês/Ano)
                if len(data_str) <= 5: 
                    data_compra = pd.to_datetime(data_str + f"/{ano_atual}", format='%d/%m/%Y', errors='coerce')
                else:
                    data_compra = pd.to_datetime(data_str, dayfirst=True, errors='coerce')
                
                trades_gs.append({
                    "ID": i, "Data": data_compra, "Ticker": ativo, "Operacao": "Compra",
                    "Preco": preco_compra, "Qtd": qtd, "Resultado_R$": 0.0, "IFR_Entrada": ifr
                })
                
                # Tratamento de Data de Saída e Venda
                data_saida_str = str(row.iloc[13]).strip()
                if "/" in data_saida_str:
                    preco_venda = limpa_moeda(row.iloc[9])
                    lucro = limpa_moeda(row.iloc[10]) # Agora os prejuízos também passam!
                    
                    if len(data_saida_str) <= 5:
                        data_venda = pd.to_datetime(data_saida_str + f"/{ano_atual}", format='%d/%m/%Y', errors='coerce')
                    else:
                        data_venda = pd.to_datetime(data_saida_str, dayfirst=True, errors='coerce')
                        
                    trades_gs.append({
                        "ID": i + 10000, 
                        "Data": data_venda, "Ticker": ativo, "Operacao": "Venda",
                        "Preco": preco_venda, "Qtd": qtd, "Resultado_R$": lucro, "IFR_Entrada": ifr
                    })
            except Exception as e:
                # Opcional: imprimir erro no terminal se quiser debugar depois
                continue
        
        return pd.DataFrame(trades_gs)
    except Exception as e:
        st.error(f"Erro de conexão com o Sheets: {e}")
        return pd.DataFrame(columns=["ID", "Data", "Ticker", "Operacao", "Preco", "Qtd", "Resultado_R$", "IFR_Entrada"])


def calcular_patrimonio_final_fase1(df_trades_f1):
    """
    Calcula o patrimonio total ao final da Fase 1 para herdar como capital
    inicial da Fase 2. Usa a mesma logica de posicoes cronologicas + preco medio
    do dashboard principal.
    Se a Fase 1 estiver vazia, retorna o CAPITAL_INICIAL_FASE1.
    """
    if df_trades_f1.empty:
        return CAPITAL_INICIAL_FASE1

    # Lucro realizado (soma das vendas da Fase 1)
    lucro_realizado = df_trades_f1[df_trades_f1["Operacao"] == "Venda"]["Resultado_R$"].sum()

    # Lucro latente da Fase 1 (posicoes que ainda estavam abertas ao fim)
    lucro_latente = 0.0
    for ativo in df_trades_f1["Ticker"].unique():
        trades_ativo = df_trades_f1[df_trades_f1["Ticker"] == ativo].sort_values(["Data", "ID"])
        qtd_aberta = 0
        p_medio = 0.0
        for _, row in trades_ativo.iterrows():
            if row["Operacao"] == "Compra":
                nova_qtd = row["Qtd"]
                preco_compra = row["Preco"]
                if (qtd_aberta + nova_qtd) > 0:
                    p_medio = ((p_medio * qtd_aberta) + (preco_compra * nova_qtd)) / (qtd_aberta + nova_qtd)
                qtd_aberta += nova_qtd
            elif row["Operacao"] == "Venda":
                qtd_aberta -= row["Qtd"]
                if qtd_aberta <= 0:
                    qtd_aberta = 0
                    p_medio = 0.0

        if qtd_aberta > 0:
            # Marca a mercado com o ultimo preco disponivel
            preco_atual = obter_preco_atual(ativo)
            if preco_atual is None:
                preco_atual = p_medio
            lucro_latente += (preco_atual - p_medio) * qtd_aberta

    return CAPITAL_INICIAL_FASE1 + lucro_realizado + lucro_latente


@st.cache_data(ttl=300)
def obter_preco_atual(ticker):
    try:
        t = ticker if ".SA" in ticker or "-" in ticker else f"{ticker}.SA"
        data = yf.Ticker(t).history(period="1d")
        return data['Close'].iloc[-1]
    except: return None


@st.cache_data(ttl=3600)  # CDI muda 1x/dia, cache 1h e OK
def baixar_cdi_bcb(data_inicial, data_final=None):
    """
    Baixa serie diaria do CDI direto da API oficial do Banco Central do Brasil.
    Serie 12 = CDI (taxa diaria em % a.d.)
    Retorna DataFrame com Data + CDI_Acumulado (Base 100 no primeiro dia).
    """
    import urllib.request
    import json
    try:
        di = pd.to_datetime(data_inicial).strftime("%d/%m/%Y")
        df_final = pd.to_datetime(data_final or datetime.now()).strftime("%d/%m/%Y")
        url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
               f"?formato=json&dataInicial={di}&dataFinal={df_final}")
        with urllib.request.urlopen(url, timeout=15) as resp:
            data_bcb = json.loads(resp.read().decode("utf-8"))
        if not data_bcb:
            return pd.DataFrame()

        df_cdi = pd.DataFrame(data_bcb)
        df_cdi["Data"] = pd.to_datetime(df_cdi["data"], dayfirst=True)
        df_cdi["taxa_dia"] = df_cdi["valor"].astype(float) / 100.0
        # CDI acumulado (juros compostos) em Base 100
        df_cdi["fator"] = 1 + df_cdi["taxa_dia"]
        df_cdi["CDI_Acum"] = df_cdi["fator"].cumprod() * 100
        return df_cdi[["Data", "CDI_Acum"]].copy()
    except Exception as e:
        print(f"[BCB] Falha no fetch CDI: {e}")
        return pd.DataFrame()



def colorir_lucro_prejuizo(val):
    color = '#00FF00' if val > 0 else '#FF4B4B' if val < 0 else '#FFFFFF'
    return f'color: {color}'

def colorir_status(val):
    if val == "⚠️ PARCIAL": return 'color: #FFA500; font-weight: bold'
    return 'color: #58A6FF'

# --- ESTADO DA SESSÃO ---
if 'precos_manuais' not in st.session_state:
    st.session_state.precos_manuais = {}

# --- SIDEBAR ---
st.sidebar.title("🎯 Painel de Comando")

# === SELETOR DE FASE ===
st.sidebar.markdown("### 📊 Fase do Fundo")
fase_selecionada = st.sidebar.radio(
    "Selecione a fase:",
    options=["Fase 2 (ativa)", "Fase 1"],
    index=0,
    help="Fase 1: base original ate 10/06/2026. Fase 2: recomeco em 17/07/2026 herdando patrimonio final da Fase 1."
)
st.sidebar.markdown("---")

# Botão NOVO para atualizar a planilha do Google
if st.sidebar.button("🔄 Sincronizar Nuvem"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

with st.sidebar.expander("💲 Atualizar Preço Manual", expanded=False):
    t_manual = st.text_input("Ticker (Ex: EZTCB194)").upper().strip()
    p_manual = st.number_input("Preço Atual", min_value=0.0, format="%.2f", key="p_man")
    if st.button("Salvar Preço"):
        st.session_state.precos_manuais[t_manual] = p_manual
        st.rerun()


# --- PROCESSAMENTO ---
# Decide qual aba carregar + capital inicial de acordo com a fase
if fase_selecionada.startswith("Fase 1"):
    df_trades = carregar_dados(URL_GOOGLE_SHEETS_FASE1)
    # Filtra trades da Fase 1 ate a data de encerramento (10/06/2026)
    if not df_trades.empty:
        df_trades = df_trades[df_trades["Data"] <= DATA_FIM_FASE1].copy()
    CAPITAL_INICIAL = CAPITAL_INICIAL_FASE1
    COTAS_INICIAIS = COTAS_INICIAIS_FASE1
    _titulo_fase = f"Fase 1"
else:
    # Fase 2: le da nova aba + herda patrimonio final da Fase 1
    df_trades = carregar_dados(URL_GOOGLE_SHEETS_FASE2)
    # === DEBUG DA FASE 2 ===
    if df_trades.empty:
        st.warning(
            "⚠️ **Fase 2 vazia:** nenhum trade foi lido da planilha. "
            "Verifique se: (1) A URL da Fase 2 esta correta, "
            "(2) A planilha esta compartilhada como 'Qualquer pessoa com o link', "
            "(3) A aba tem trades apos 17/07/2026, "
            "(4) A estrutura de colunas e identica a Fase 1."
        )
        # Debug: mostra o CSV bruto para inspecao
        with st.expander("🔍 Debug: ver CSV bruto da Fase 2"):
            try:
                _raw = pd.read_csv(URL_GOOGLE_SHEETS_FASE2, engine="python",
                                   on_bad_lines="skip")
                st.write(f"Linhas brutas lidas: {len(_raw)}")
                st.write(f"Colunas: {list(_raw.columns)}")
                st.dataframe(_raw.head(10))
            except Exception as e:
                st.error(f"Falha ao baixar CSV bruto: {e}")
    else:
        # Filtra Fase 2 para trades a partir do inicio oficial (17/07/2026)
        antes = len(df_trades)
        df_trades = df_trades[df_trades["Data"] >= DATA_INICIO_FASE2].copy()
        if df_trades.empty:
            st.warning(
                f"⚠️ **Fase 2 vazia apos filtro de data:** "
                f"{antes} trades foram lidos, mas NENHUM tem data >= "
                f"{DATA_INICIO_FASE2.strftime('%d/%m/%Y')}."
            )
    # Herda o patrimonio final da Fase 1 como capital inicial
    _df_fase1 = carregar_dados(URL_GOOGLE_SHEETS_FASE1)
    # Considera apenas trades da Fase 1 ate o fim oficial (10/06/2026)
    if not _df_fase1.empty:
        _df_fase1 = _df_fase1[_df_fase1["Data"] <= DATA_FIM_FASE1].copy()
    CAPITAL_INICIAL = calcular_patrimonio_final_fase1(_df_fase1)
    # Cotas iniciais ajustadas para preservar BASE 100:
    # cota inicial = CAPITAL / cotas = 100  ->  cotas = CAPITAL / 100
    # Assim PL inicial = patrimonio herdado, mas cota comeca em 100
    COTAS_INICIAIS = CAPITAL_INICIAL / 100.0 if CAPITAL_INICIAL > 0 else COTAS_INICIAIS_FASE2
    _titulo_fase = f"Fase 2"

st.title(f"📈 Sniper Quant | Gestão de Fundo — {_titulo_fase}")

posicoes_list = []
if not df_trades.empty:
    ativos_unicos = df_trades['Ticker'].unique()
    
    for ativo in ativos_unicos:
        # Pega as operações do ativo em ordem cronológica (do mais antigo pro mais novo)
        trades_ativo = df_trades[df_trades['Ticker'] == ativo].sort_values(['Data', 'ID'])
        
        qtd_aberta = 0
        p_medio = 0.0
        teve_venda_parcial = False
        
        # MÁGICA AQUI: Simulação cronológica das posições para resetar o preço médio ao zerar
        for _, row in trades_ativo.iterrows():
            if row['Operacao'] == 'Compra':
                nova_qtd = row['Qtd']
                preco_compra = row['Preco']
                # Calcula novo preço médio ponderado
                p_medio = ((p_medio * qtd_aberta) + (preco_compra * nova_qtd)) / (qtd_aberta + nova_qtd)
                qtd_aberta += nova_qtd
            elif row['Operacao'] == 'Venda':
                nova_qtd = row['Qtd']
                qtd_aberta -= nova_qtd
                teve_venda_parcial = True
                
                # Zera o preço médio se fechar a posição inteira (Venda total)
                if qtd_aberta <= 0:
                    qtd_aberta = 0
                    p_medio = 0.0
                    teve_venda_parcial = False # Reseta a parcialidade para o próximo ciclo
        
        if qtd_aberta > 0:
            status_parcial = "⚠️ PARCIAL" if teve_venda_parcial else "INTEGRAL"
            
            # Obtém preço (Auto -> Manual -> Médio)
            preco_atual = obter_preco_atual(ativo)
            if ativo in st.session_state.precos_manuais:
                preco_atual = st.session_state.precos_manuais[ativo]
            if preco_atual is None:
                preco_atual = p_medio 
            
            lucro_r = (preco_atual - p_medio) * qtd_aberta
            lucro_p = ((preco_atual / p_medio) - 1) * 100 if p_medio > 0 else 0
            
            posicoes_list.append({
                "Ativo": ativo, "Status": status_parcial, "Qtd": qtd_aberta, 
                "P.Médio": p_medio, "Atual": preco_atual, "L/P R$": lucro_r, "L/P %": lucro_p
            })

    lucro_realizado = df_trades[df_trades['Operacao'] == "Venda"]['Resultado_R$'].sum()
    lucro_latente = sum(p['L/P R$'] for p in posicoes_list)
    patrimonio_total = CAPITAL_INICIAL + lucro_realizado + lucro_latente
    valor_cota = patrimonio_total / COTAS_INICIAIS

    # === Cards principais (linha 1): patrimonio ===
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valor da Cota", f"R$ {valor_cota:.2f}", f"{((valor_cota/100)-1)*100:.2f}%")
    c2.metric("Patrimônio", f"R$ {patrimonio_total:.2f}")
    c3.metric("L/P Latente", f"R$ {lucro_latente:.2f}")
    c4.metric("L/P Realizado", f"R$ {lucro_realizado:.2f}")

    # === Cards institucionais (linha 2): metricas quant vs benchmarks ===
    # Calculado apos gerar o df_chart (que ja existe abaixo). Guardamos para exibir depois.

    # --- GRÁFICO DE EVOLUÇÃO (DADOS CONSOLIDADOS E DIAS ÚTEIS) ---
    vendas_hist = df_trades[df_trades['Operacao'] == "Venda"].sort_values('Data')
    
    # Criamos o ponto inicial (Base 100)
    data_inicial = df_trades['Data'].min() - pd.Timedelta(days=1) if not df_trades.empty else datetime.now()
    df_chart = pd.DataFrame({'Data': [pd.to_datetime(data_inicial)], 'Cota': [100.0]})
    
    if not vendas_hist.empty:
        # Agrupamos vendas por dia para evitar múltiplos pontos
        vendas_diarias = vendas_hist.groupby(vendas_hist['Data'].dt.date)['Resultado_R$'].sum().reset_index()
        vendas_diarias['Cota_Acum'] = (CAPITAL_INICIAL + vendas_diarias['Resultado_R$'].cumsum()) / COTAS_INICIAIS
        vendas_diarias['Data'] = pd.to_datetime(vendas_diarias['Data'])
        df_chart = pd.concat([df_chart, vendas_diarias[['Data', 'Cota_Acum']].rename(columns={'Cota_Acum': 'Cota'})])

    # CORREÇÃO: Descobrir o último dia útil (Ignorar Sábado e Domingo)
    hoje = pd.to_datetime(datetime.now().date())
    if hoje.dayofweek == 5: # 5 = Sábado
        ultimo_dia_util = hoje - pd.Timedelta(days=1)
    elif hoje.dayofweek == 6: # 6 = Domingo
        ultimo_dia_util = hoje - pd.Timedelta(days=2)
    else:
        ultimo_dia_util = hoje

    # Se for FASE 1, gráfico deve terminar em DATA_FIM_FASE1 (encerramento oficial)
    if fase_selecionada.startswith("Fase 1"):
        ultimo_dia_util = min(ultimo_dia_util, DATA_FIM_FASE1)

    # Injetar a cota atual no último dia útil correspondente
    if not df_chart.empty and df_chart['Data'].iloc[-1].date() == ultimo_dia_util.date():
        df_chart.loc[df_chart.index[-1], 'Cota'] = valor_cota
    else:
        ponto_atual = pd.DataFrame({'Data': [ultimo_dia_util], 'Cota': [valor_cota]})
        df_chart = pd.concat([df_chart, ponto_atual], ignore_index=True)

    # Define data final dos benchmarks conforme a fase (Fase 1 encerra em 10/06)
    if fase_selecionada.startswith("Fase 1"):
        _bench_end = DATA_FIM_FASE1 + pd.Timedelta(days=1)  # +1 para incluir o dia 10/06
    else:
        _bench_end = datetime.now()

    # Download dos benchmarks: IBOV (Brasil) + S&P 500 (EUA)
    def _baixar_benchmark(ticker, nome_col):
        """Baixa e normaliza um benchmark em Base 100. Retorna DataFrame vazio se falhar."""
        try:
            raw = yf.download(ticker, start=df_chart['Data'].min(),
                              end=_bench_end, interval="1d", progress=False)
            if raw.empty:
                return pd.DataFrame()
            serie = raw['Close']
            # Lida com MultiIndex do yfinance recente
            if hasattr(serie, 'columns'):
                serie = serie.iloc[:, 0]
            serie_norm = (serie / serie.iloc[0]) * 100
            df_bench = serie_norm.reset_index()
            df_bench.columns = ['Data', nome_col]
            # Corta explicitamente na data final da fase (defesa dupla)
            if fase_selecionada.startswith("Fase 1"):
                df_bench = df_bench[df_bench['Data'] <= DATA_FIM_FASE1].copy()
            return df_bench
        except Exception:
            return pd.DataFrame()

    ibov_df = _baixar_benchmark("^BVSP", "IBOV")
    sp500_df = _baixar_benchmark("^GSPC", "SP500")
    # CDI direto da API oficial do BCB (serie 12) - respeita data final da fase
    cdi_df_raw = baixar_cdi_bcb(df_chart['Data'].min(), _bench_end)
    if not cdi_df_raw.empty:
        # Rebase para 100 no primeiro dia (alinhado com IBOV e S&P)
        base = cdi_df_raw['CDI_Acum'].iloc[0]
        cdi_df_raw['CDI'] = (cdi_df_raw['CDI_Acum'] / base) * 100
        cdi_df = cdi_df_raw[['Data', 'CDI']].copy()
    else:
        cdi_df = pd.DataFrame()

    fig = go.Figure()

    # === LINHA PRINCIPAL: Cota Sniper (verde neon grossa + fill) ===
    fig.add_trace(go.Scatter(
        x=df_chart['Data'], 
        y=df_chart['Cota'], 
        mode='lines+markers', 
        line=dict(color='#39FF14', width=3), 
        marker=dict(size=6, color='#39FF14', line=dict(color='#0D1117', width=1)),
        fill='tozeroy',
        fillcolor='rgba(57, 255, 20, 0.10)',
        name='Cota Sniper'
    ))
    
    # Benchmark 1: IBOVESPA (azul dashed 2px)
    if not ibov_df.empty:
        fig.add_trace(go.Scatter(
            x=ibov_df['Data'], 
            y=ibov_df['IBOV'], 
            mode='lines', 
            line=dict(color='#58A6FF', width=2, dash='dash'), 
            opacity=0.8,
            name='IBOVESPA'
        ))
    
    # Benchmark 2: S&P 500 (dourado dotted 1.5px - referencia internacional)
    if not sp500_df.empty:
        fig.add_trace(go.Scatter(
            x=sp500_df['Data'], 
            y=sp500_df['SP500'], 
            mode='lines', 
            line=dict(color='#FFD700', width=1.5, dash='dot'), 
            opacity=0.7,
            name='S&P 500'
        ))
    
    # Benchmark 3: CDI (roxo longdash 1.5px - piso risk-free BR)
    if not cdi_df.empty:
        fig.add_trace(go.Scatter(
            x=cdi_df['Data'], 
            y=cdi_df['CDI'], 
            mode='lines', 
            line=dict(color='#BF40BF', width=1.5, dash='longdash'), 
            opacity=0.7,
            name='CDI'
        ))

    # --- AJUSTE DE EIXO Y E EIXO X (OMITIR FINAIS DE SEMANA) ---
    max_val = max(
        df_chart['Cota'].max(),
        ibov_df['IBOV'].max() if not ibov_df.empty else 100,
        sp500_df['SP500'].max() if not sp500_df.empty else 100,
        cdi_df['CDI'].max() if not cdi_df.empty else 100,
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=450,
        hovermode='x unified',
        # Fundo 100% transparente - funde com o app
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#E6EDF3", size=12),
        margin=dict(l=50, r=20, t=30, b=40),
        yaxis=dict(
            title=dict(text="PERFORMANCE (BASE 100)", font=dict(size=11, color="#8B949E")),
            range=[90, max_val * 1.05],
            fixedrange=False,
            zeroline=False,
            # Grades sutis
            gridcolor='#30363D',
            gridwidth=1,
            showline=False,
            tickfont=dict(color="#E6EDF3")
        ),
        xaxis=dict(
            rangebreaks=[dict(bounds=["sat", "mon"])],
            gridcolor='#30363D',
            gridwidth=1,
            showline=False,
            tickfont=dict(color="#E6EDF3")
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, color="#E6EDF3"),
            bgcolor='rgba(0,0,0,0)',
        ),
        hoverlabel=dict(
            bgcolor="#161B22",
            font=dict(color="#E6EDF3", size=12),
            bordercolor="#30363D"
        )
    )

    # Base 100 - linha de referencia pontilhada branca opaca
    fig.add_hline(
        y=100, line_dash="dot", line_color="white", opacity=0.5, line_width=1
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Tabela
    st.subheader("Posições em Aberto")
    if posicoes_list:
        df_pos = pd.DataFrame(posicoes_list)
        st.dataframe(
            df_pos.style.format({"P.Médio": "R$ {:.2f}", "Atual": "R$ {:.2f}", "L/P R$": "R$ {:.2f}", "L/P %": "{:.2f}%"})
            .map(colorir_lucro_prejuizo, subset=['L/P R$', 'L/P %'])
            .map(colorir_status, subset=['Status']), 
            use_container_width=True
        )
    else: st.info("Nenhuma posição aberta.")

# --- MATRIZ DE PERFORMANCE COM REVELAÇÃO PROGRESSIVA ---
    st.subheader("📊 Matriz de Performance")
    
    # 🔘 Seletor de Nível de Detalhe
    modo_visao = st.radio(
        "Nível de Detalhe:",
        ["Resumido (Apenas %)", "Detalhado (Trades | WR)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if not vendas_hist.empty:
        df_m = vendas_hist.copy()
        df_m['Ano'] = df_m['Data'].dt.year
        df_m['Mês_Num'] = df_m['Data'].dt.month
        
        res_mensal = df_m.groupby(['Ano', 'Mês_Num']).agg(
            Lucro_Total=('Resultado_R$', 'sum'),
            Total_Trades=('ID', 'count'),
            Wins=('Resultado_R$', lambda x: (x > 0).sum())
        ).reset_index()
        
        res_mensal['WinRate'] = (res_mensal['Wins'] / res_mensal['Total_Trades']) * 100
        res_mensal['Retorno_%'] = (res_mensal['Lucro_Total'] / CAPITAL_INICIAL) * 100
        
        # 🪄 LÓGICA DE EXIBIÇÃO DINÂMICA
        if modo_visao == "Resumido (Apenas %)":
            res_mensal['Display'] = res_mensal['Retorno_%'].apply(lambda x: f"{x:.2f}%")
        else:
            res_mensal['Display'] = res_mensal.apply(
                lambda x: f"{x['Retorno_%']:.2f}% \n ({int(x['Total_Trades'])}t | {x['WinRate']:.0f}%)", axis=1
            )
        
        pivot_retorno = res_mensal.pivot(index='Ano', columns='Mês_Num', values='Display')
        meses_nomes = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun',
                       7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        pivot_retorno = pivot_retorno.rename(columns=meses_nomes)
        
        def colorir_matrix_string(val):
            if pd.isna(val) or val == "-": return 'color: #555555; text-align: center;' 
            if str(val).strip().startswith('-'):
                return 'background-color: rgba(255, 75, 75, 0.15); color: #ff4b4b; text-align: center; font-weight: bold;'
            return 'background-color: rgba(57, 255, 20, 0.15); color: #39ff14; text-align: center; font-weight: bold;'

        st.dataframe(pivot_retorno.style.map(colorir_matrix_string), use_container_width=True)
        st.caption(f"Visualização atual: {modo_visao}")
    else:
        st.info("Aguardando dados para gerar a matriz.")

    # Histórico
    with st.expander("🛠️ Ver Histórico Completo (Livro-Razão)"):
        df_hist_view = df_trades.copy()
        
        # Converte ID para número para evitar o bug de ordem alfabética
        df_hist_view['ID'] = pd.to_numeric(df_hist_view['ID'], errors='coerce')
        
        # Ordena cronologicamente pela Data (Mais recentes no topo)
        df_hist_view = df_hist_view.sort_values(by=['Data', 'Operacao'], ascending=[False, False])
        
        df_hist_view['Resultado %'] = df_hist_view.apply(lambda x: (x['Resultado_R$'] / ((x['Preco']*x['Qtd']) - x['Resultado_R$'])) * 100 if x['Operacao'] == "Venda" and (x['Preco']*x['Qtd'] - x['Resultado_R$']) != 0 else 0, axis=1)
        
        st.dataframe(df_hist_view.style.format({"Preco": "R$ {:.2f}", "Resultado_R$": "R$ {:.2f}", "Resultado %": "{:.2f}%"}).map(colorir_lucro_prejuizo, subset=['Resultado_R$', 'Resultado %']), use_container_width=True)
