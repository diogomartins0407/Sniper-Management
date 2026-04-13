import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAÇÕES DO FUNDO ---
st.set_page_config(page_title="Sniper Quant Dashboard", layout="wide")

CAPITAL_INICIAL = 5000.0
COTAS_INICIAIS = 50.0 

# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=300) # Cache para deixar o painel rápido
def carregar_dados():
    """Lê os dados 100% da nuvem (Google Sheets)"""
    
    # ⚠️ MANTENHA O SEU LINK DA PLANILHA AQUI:
    URL_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSk4E78PHBBrCfP0_Ixd_GmhVBiN5dSgdR1dZU6mCXdbK28YPU4CvBut1CZxE9Q_1xLkJOGZe6xX13z/pub?gid=610498100&single=true&output=csv" 
    
    try:
        df_gs = pd.read_csv(URL_GOOGLE_SHEETS)
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
                
                # Tratamento seguro da Quantidade
                qtd_str = str(row.iloc[6]).replace('.', '').replace(' ', '').strip()
                qtd = int(float(qtd_str)) if qtd_str and qtd_str.lower() != 'nan' else 0
                
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


@st.cache_data(ttl=300)
def obter_preco_atual(ticker):
    try:
        t = ticker if ".SA" in ticker or "-" in ticker else f"{ticker}.SA"
        data = yf.Ticker(t).history(period="1d")
        return data['Close'].iloc[-1]
    except: return None

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
df_trades = carregar_dados()
st.title("📈 Sniper Quant | Gestão de Fundo")

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

    # Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valor da Cota", f"R$ {valor_cota:.2f}", f"{((valor_cota/100)-1)*100:.2f}%")
    c2.metric("Patrimônio", f"R$ {patrimonio_total:.2f}")
    c3.metric("L/P Latente", f"R$ {lucro_latente:.2f}")
    c4.metric("L/P Realizado", f"R$ {lucro_realizado:.2f}")

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

    # Injetar a cota atual no último dia útil correspondente
    if not df_chart.empty and df_chart['Data'].iloc[-1].date() == ultimo_dia_util.date():
        df_chart.loc[df_chart.index[-1], 'Cota'] = valor_cota
    else:
        ponto_atual = pd.DataFrame({'Data': [ultimo_dia_util], 'Cota': [valor_cota]})
        df_chart = pd.concat([df_chart, ponto_atual], ignore_index=True)

    # Download do IBOV
    try:
        ibov_raw = yf.download("^BVSP", start=df_chart['Data'].min(), end=datetime.now(), interval="1d", progress=False)
        ibov = ibov_raw['Close']
        ibov_norm = (ibov / ibov.iloc[0]) * 100
        ibov_df = ibov_norm.reset_index()
        ibov_df.columns = ['Data', 'IBOV']
    except:
        ibov_df = pd.DataFrame()

    fig = go.Figure()

    # Linha do Fundo Sniper
    fig.add_trace(go.Scatter(
        x=df_chart['Data'], 
        y=df_chart['Cota'], 
        mode='lines+markers', 
        line=dict(color='#39FF14', width=3), 
        name='Cota Sniper'
    ))
    
    # Linha do IBOVESPA
    if not ibov_df.empty:
        fig.add_trace(go.Scatter(
            x=ibov_df['Data'], 
            y=ibov_df['IBOV'], 
            mode='lines', 
            line=dict(color='#58A6FF', width=2, dash='dash'), 
            name='IBOVESPA'
        ))

    # --- AJUSTE DE EIXO Y E EIXO X (OMITIR FINAIS DE SEMANA) ---
    max_val = max(df_chart['Cota'].max(), ibov_df['IBOV'].max() if not ibov_df.empty else 100)
    
    fig.update_layout(
        template="plotly_dark", 
        height=450, 
        hovermode='x unified',
        yaxis=dict(
            title="Performance (Base 100)",
            range=[90, max_val * 1.05],
            fixedrange=False,
            zeroline=False
        ),
        xaxis=dict(
            rangebreaks=[
                dict(bounds=["sat", "mon"]) # Corta o espaço vazio entre Sábado e Segunda-feira
            ]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.add_hline(y=100, line_dash="dot", line_color="white", opacity=0.5)
    
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

    # Histórico
    with st.expander("🛠️ Ver Histórico Completo (Livro-Razão)"):
        df_hist_view = df_trades.copy()
        
        # Converte ID para número para evitar o bug de ordem alfabética
        df_hist_view['ID'] = pd.to_numeric(df_hist_view['ID'], errors='coerce')
        
        # Ordena cronologicamente pela Data (Mais recentes no topo)
        df_hist_view = df_hist_view.sort_values(by=['Data', 'Operacao'], ascending=[False, False])
        
        df_hist_view['Resultado %'] = df_hist_view.apply(lambda x: (x['Resultado_R$'] / ((x['Preco']*x['Qtd']) - x['Resultado_R$'])) * 100 if x['Operacao'] == "Venda" and (x['Preco']*x['Qtd'] - x['Resultado_R$']) != 0 else 0, axis=1)
        
        st.dataframe(df_hist_view.style.format({"Preco": "R$ {:.2f}", "Resultado_R$": "R$ {:.2f}", "Resultado %": "{:.2f}%"}).map(colorir_lucro_prejuizo, subset=['Resultado_R$', 'Resultado %']), use_container_width=True)