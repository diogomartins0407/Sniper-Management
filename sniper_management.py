import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- CONFIGURAÇÕES DO FUNDO ---
st.set_page_config(page_title="Sniper Quant Terminal", layout="wide", page_icon="📈")

# ============================================================
# TEMA GLOBAL - ESTILO TRADINGVIEW (dark terminal)
# Paleta validada (CVD + contraste): Cota #16c88a, IBOV #3b82f6,
# S&P #e0a92e, CDI #a855f7. Negativo #ea3943.
# ============================================================
TV_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

:root{
    --bg:#0e1017; --panel:#161b26; --panel2:#1b2030; --border:#2a2e39;
    --ink:#d1d4dc; --ink-strong:#eaecef; --muted:#787b86;
    --up:#16c88a; --down:#ea3943; --blue:#3b82f6; --gold:#e0a92e; --purple:#a855f7;
}

/* Canvas */
[data-testid="stAppViewContainer"], .stApp { background: var(--bg) !important; }
header[data-testid="stHeader"]{ height:0; background:transparent; }
[data-testid="stToolbar"]{ display:none; }
#MainMenu, footer { visibility:hidden; }
.block-container{ padding-top:1.1rem; padding-bottom:2.5rem; max-width:1420px; }
html, body, [class*="css"]{ font-family:'Inter',-apple-system,Segoe UI,sans-serif; }

/* UI em Inter (sans-serif) — sobrepõe o tema do Streamlit */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
p, span, div, label, li, input, button, textarea, select,
h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] {
    font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif !important;
}
/* Exceção: ícones do Streamlit (Material Symbols) mantêm sua fonte própria */
[data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"],
.material-icons, .material-symbols-rounded, span[class*="material-"], i[class*="material-"]{
    font-family:'Material Symbols Rounded','Material Symbols Outlined','Material Icons' !important;
}

.stApp, .stMarkdown, p, span, div, label, li { color: var(--ink); }
h1,h2,h3,h4,h5,h6{ color:var(--ink-strong) !important; font-weight:700 !important; letter-spacing:-.2px; }

/* Números em mono tabular (JetBrains Mono) — vence a regra acima por especificidade */
.tv-price-val, .tv-price-chg, .kpi .v{
    font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace !important;
    font-variant-numeric:tabular-nums;
}

/* Sidebar */
[data-testid="stSidebar"]{ background:var(--panel) !important; border-right:1px solid var(--border); }
[data-testid="stSidebar"] * { color:var(--ink); }

/* ===== HERO / HEADER ===== */
.tv-head{ display:flex; justify-content:space-between; align-items:flex-end;
    border-bottom:1px solid var(--border); padding-bottom:12px; margin:2px 0 14px; }
.tv-sym-name{ font-size:23px; font-weight:700; color:var(--ink-strong); }
.tv-badge{ font-size:11px; background:rgba(22,200,138,.13); color:var(--up);
    border:1px solid rgba(22,200,138,.35); padding:2px 9px; border-radius:999px;
    margin-left:9px; vertical-align:middle; font-weight:600; letter-spacing:.4px; }
.tv-sym-sub{ color:var(--muted); font-size:12px; margin-top:4px; }
.tv-price{ text-align:right; }
.tv-price-val{ font-family:'JetBrains Mono',monospace; font-size:31px; font-weight:700;
    color:var(--ink-strong); line-height:1; }
.tv-price-chg{ font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:600; margin-top:5px; }

/* ===== KPI TILES ===== */
.kpi-row{ display:flex; gap:10px; flex-wrap:wrap; margin:0 0 16px; }
.kpi{ flex:1 1 150px; background:linear-gradient(180deg,var(--panel2),var(--panel));
    border:1px solid var(--border); border-radius:11px; padding:12px 15px; }
.kpi .l{ color:var(--muted); font-size:10.5px; text-transform:uppercase;
    letter-spacing:.7px; font-weight:600; margin-bottom:7px; }
.kpi .v{ color:var(--ink-strong); font-family:'JetBrains Mono',monospace; font-size:19px;
    font-weight:600; font-variant-numeric:tabular-nums; }
.kpi .s{ color:var(--muted); font-size:11px; margin-top:3px; }
.pos{ color:var(--up) !important; } .neg{ color:var(--down) !important; }

/* Rótulo de seção */
.sec-label{ color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:1.2px;
    font-weight:700; margin:6px 0 10px; display:flex; align-items:center; gap:8px; }
.sec-label::after{ content:''; flex:1; height:1px; background:var(--border); }

/* Edge por faixa de IFR */
.edge-wrap{ background:linear-gradient(180deg,var(--panel2),var(--panel)); border:1px solid var(--border);
    border-radius:11px; padding:16px 18px; margin-bottom:6px; }
.edge-row{ display:flex; align-items:center; gap:14px; padding:9px 0; border-bottom:1px solid #20242e; }
.edge-row:last-child{ border-bottom:none; }
.edge-faixa{ width:92px; color:var(--ink-strong); font-weight:600; font-size:13px; font-family:'JetBrains Mono',monospace; }
.edge-track{ flex:1; height:22px; background:#10141d; border-radius:6px; overflow:hidden; position:relative; }
.edge-fill{ height:100%; border-radius:6px; display:flex; align-items:center; justify-content:flex-end;
    padding-right:8px; color:#0e1017; font-size:11px; font-weight:700; font-family:'JetBrains Mono',monospace;
    min-width:34px; transition:width .5s ease; }
.edge-ret{ width:84px; text-align:right; font-family:'JetBrains Mono',monospace; font-weight:700; font-size:13px; }
.edge-n{ width:74px; text-align:right; color:var(--muted); font-size:11px; }
.edge-head{ color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.6px; }

/* ===== DATAFRAMES ===== */
[data-testid="stDataFrame"]{ border-radius:10px; border:1px solid var(--border); overflow:hidden; }
[data-testid="stDataFrame"] th{ background:var(--panel) !important; color:var(--muted) !important;
    font-weight:600 !important; letter-spacing:.5px; text-transform:uppercase; font-size:.72em; }
[data-testid="stDataFrame"] td{ color:var(--ink) !important; background:var(--bg) !important;
    border-bottom:1px solid #20242e !important; font-variant-numeric:tabular-nums; }

/* ===== BOTÕES ===== */
.stButton > button{ background:var(--panel2); color:var(--ink); border:1px solid var(--border);
    border-radius:8px; font-weight:600; transition:.15s; }
.stButton > button:hover{ border-color:var(--up); color:var(--up); }

/* Inputs / expanders */
.stTextInput input, .stNumberInput input{ background:var(--panel) !important; color:var(--ink) !important;
    border:1px solid var(--border) !important; border-radius:8px !important; }
[data-testid="stExpander"]{ background:var(--panel); border:1px solid var(--border); border-radius:10px; }
.stRadio [role="radiogroup"]{ gap:4px; }
hr{ border-color:var(--border) !important; margin:10px 0 !important; }
code{ background:var(--panel) !important; color:var(--up) !important;
    border:1px solid var(--border); border-radius:3px; padding:2px 6px; }
</style>
"""
st.markdown(TV_CSS, unsafe_allow_html=True)

# ============================================================
# CONFIGURACAO DO FUNDO (FASE 1)
# ============================================================
CAPITAL_INICIAL = 5000.0
COTAS_INICIAIS = 50.0
URL_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSk4E78PHBBrCfP0_Ixd_GmhVBiN5dSgdR1dZU6mCXdbK28YPU4CvBut1CZxE9Q_1xLkJOGZe6xX13z/pub?gid=610498100&single=true&output=csv"

# Cores (iguais ao tema / validadas)
C_UP, C_DOWN = "#16c88a", "#ea3943"
C_IBOV, C_SP500, C_CDI = "#3b82f6", "#e0a92e", "#a855f7"


# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=300)
def carregar_dados(url_planilha, _versao_cache="v4_tv"):
    """Le os dados da aba da planilha Google Sheets."""
    try:
        df_gs = pd.read_csv(url_planilha, engine="python", on_bad_lines="skip")
        df_gs = df_gs.dropna(subset=[df_gs.columns[1], df_gs.columns[2]])

        trades_gs = []
        ano_atual = str(datetime.now().year)

        def limpa_moeda(val):
            v = str(val).replace('R$', '').replace(' ', '').replace('\xa0', '').strip()
            if not v or v == '-':
                return 0.0
            v = v.replace('.', '').replace(',', '.')
            try:
                return float(v)
            except Exception:
                return 0.0

        for i, row in df_gs.iterrows():
            try:
                data_str = str(row.iloc[1]).strip()
                if "/" not in data_str:
                    continue

                ativo = str(row.iloc[2]).upper().strip()

                ifr_str = str(row.iloc[3]).replace(',', '.').strip()
                ifr = float(ifr_str) if ifr_str and ifr_str.lower() != 'nan' else 0.0

                preco_compra = limpa_moeda(row.iloc[4])
                risco_trade = limpa_moeda(row.iloc[7])   # Risco (R$) por trade
                alvo_trade = limpa_moeda(row.iloc[5])    # Alvo (R$)

                # Quantidade (blindada contra bug x10)
                qtd_raw = row.iloc[6]
                if pd.isna(qtd_raw):
                    qtd = 0
                else:
                    qtd_str = str(qtd_raw).replace(' ', '').replace('\xa0', '').strip()
                    if not qtd_str or qtd_str.lower() == 'nan':
                        qtd = 0
                    elif ',' in qtd_str:
                        qtd_str = qtd_str.replace('.', '').replace(',', '.')
                        qtd = int(float(qtd_str))
                    else:
                        try:
                            qtd = int(float(qtd_str))
                        except ValueError:
                            qtd = 0

                if len(data_str) <= 5:
                    data_compra = pd.to_datetime(data_str + f"/{ano_atual}", format='%d/%m/%Y', errors='coerce')
                else:
                    data_compra = pd.to_datetime(data_str, dayfirst=True, errors='coerce')

                trades_gs.append({
                    "ID": i, "Data": data_compra, "Ticker": ativo, "Operacao": "Compra",
                    "Preco": preco_compra, "Qtd": qtd, "Resultado_R$": 0.0, "IFR_Entrada": ifr,
                    "Alvo": alvo_trade, "Risco": risco_trade, "Retorno_pct": 0.0, "DiasUteis": 0
                })

                data_saida_str = str(row.iloc[13]).strip()
                if "/" in data_saida_str:
                    preco_venda = limpa_moeda(row.iloc[9])
                    lucro = limpa_moeda(row.iloc[10])

                    # % de retorno do trade (col 11) e dias uteis (col 14)
                    retorno_pct = limpa_moeda(str(row.iloc[11]).replace('%', ''))
                    try:
                        dias_uteis = int(float(str(row.iloc[14]).replace(',', '.').strip()))
                    except (ValueError, TypeError):
                        dias_uteis = 0

                    if len(data_saida_str) <= 5:
                        data_venda = pd.to_datetime(data_saida_str + f"/{ano_atual}", format='%d/%m/%Y', errors='coerce')
                    else:
                        data_venda = pd.to_datetime(data_saida_str, dayfirst=True, errors='coerce')

                    trades_gs.append({
                        "ID": i + 10000,
                        "Data": data_venda, "Ticker": ativo, "Operacao": "Venda",
                        "Preco": preco_venda, "Qtd": qtd, "Resultado_R$": lucro, "IFR_Entrada": ifr,
                        "Alvo": alvo_trade, "Risco": risco_trade,
                        "Retorno_pct": retorno_pct, "DiasUteis": dias_uteis
                    })
            except Exception:
                continue

        return pd.DataFrame(trades_gs)
    except Exception as e:
        st.error(f"Erro de conexão com o Sheets: {e}")
        return pd.DataFrame(columns=["ID", "Data", "Ticker", "Operacao", "Preco", "Qtd",
                                     "Resultado_R$", "IFR_Entrada", "Alvo", "Risco",
                                     "Retorno_pct", "DiasUteis"])


@st.cache_data(ttl=300)
def obter_preco_atual(ticker):
    try:
        t = ticker if ".SA" in ticker or "-" in ticker else f"{ticker}.SA"
        data = yf.Ticker(t).history(period="1d")
        return data['Close'].iloc[-1]
    except Exception:
        return None


@st.cache_data(ttl=3600)
def baixar_cdi_bcb(data_inicial, data_final=None):
    """Serie diaria do CDI (SGS 12) do Banco Central, acumulada Base 100."""
    import urllib.request
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
        df_cdi["fator"] = 1 + df_cdi["taxa_dia"]
        df_cdi["CDI_Acum"] = df_cdi["fator"].cumprod() * 100
        return df_cdi[["Data", "CDI_Acum"]].copy()
    except Exception as e:
        print(f"[BCB] Falha no fetch CDI: {e}")
        return pd.DataFrame()


# --- Formatação BR ---
def fmt_brl(x):
    try:
        s = f"{float(x):,.2f}"
    except Exception:
        return "R$ 0,00"
    return "R$ " + s.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_num(x, dec=2):
    return f"{float(x):,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def serie_para_json(df, col):
    """Converte um DataFrame (Data + col) em lista [{time, value}] p/ lightweight-charts."""
    if df is None or df.empty or col not in df.columns:
        return []
    tmp = df[['Data', col]].dropna().copy()
    tmp['Data'] = pd.to_datetime(tmp['Data'])
    tmp = tmp.groupby(tmp['Data'].dt.date)[col].last().reset_index()
    tmp = tmp.sort_values('Data')
    out = []
    for d, v in zip(tmp['Data'], tmp[col]):
        try:
            out.append({"time": pd.Timestamp(d).strftime('%Y-%m-%d'), "value": round(float(v), 4)})
        except Exception:
            continue
    return out


def colorir_lucro_prejuizo(val):
    color = C_UP if val > 0 else C_DOWN if val < 0 else '#d1d4dc'
    return f'color: {color}'


def colorir_status(val):
    if val == "⚠️ PARCIAL":
        return f'color: {C_GOLD}; font-weight: bold'
    return f'color: {C_IBOV}'


C_GOLD = C_SP500  # alias legibilidade


# ============================================================
# COMPONENTE: GRÁFICO ESTILO TRADINGVIEW (lightweight-charts)
# ============================================================
def render_tradingview_chart(cota, ibov, sp500, cdi, altura=470):
    template = r"""
<div id="wrap" style="position:relative;width:100%;height:__H__px;background:#131722;
     border:1px solid #2a2e39;border-radius:11px;overflow:hidden;
     font-family:Inter,-apple-system,Segoe UI,sans-serif;">
  <div id="legend" style="position:absolute;z-index:4;top:11px;left:14px;
       background:rgba(19,23,34,.55);backdrop-filter:blur(4px);
       border:1px solid rgba(42,46,57,.6);border-radius:8px;padding:8px 11px;"></div>
  <div id="toolbar" style="position:absolute;z-index:4;top:11px;right:14px;display:flex;gap:4px;"></div>
  <div id="chart" style="position:absolute;inset:0;"></div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
(function(){
  const COTA=__COTA__, IBOV=__IBOV__, SP500=__SP500__, CDI=__CDI__;
  const el=document.getElementById('chart');
  if(!window.LightweightCharts || !COTA.length){ el.innerHTML='<div style="color:#787b86;padding:20px;font-family:Inter">Sem dados para exibir.</div>'; return; }

  const chart=LightweightCharts.createChart(el,{
    width:el.clientWidth, height:el.clientHeight,
    layout:{ background:{type:'solid',color:'transparent'}, textColor:'#787b86', fontSize:11,
             fontFamily:"'JetBrains Mono',monospace" },
    grid:{ vertLines:{color:'rgba(42,46,57,.45)'}, horzLines:{color:'rgba(42,46,57,.45)'} },
    rightPriceScale:{ borderColor:'#2a2e39', scaleMargins:{top:0.14,bottom:0.08} },
    timeScale:{ borderColor:'#2a2e39', rightOffset:3, fixLeftEdge:true, fixRightEdge:true,
                timeVisible:false, secondsVisible:false },
    crosshair:{ mode:LightweightCharts.CrosshairMode.Normal,
      vertLine:{color:'rgba(120,123,134,.55)',width:1,style:2,labelBackgroundColor:'#2a2e39'},
      horzLine:{color:'rgba(120,123,134,.55)',width:1,style:2,labelBackgroundColor:'#2a2e39'} },
    localization:{ locale:'pt-BR', priceFormatter:v=>v.toFixed(2) },
  });

  const series=[];
  const cota=chart.addAreaSeries({ lineColor:'#16c88a', topColor:'rgba(22,200,138,.30)',
     bottomColor:'rgba(22,200,138,.015)', lineWidth:3, priceLineVisible:false,
     crosshairMarkerRadius:5, crosshairMarkerBorderColor:'#131722', lastValueVisible:true });
  cota.setData(COTA);
  series.push({name:'Cota Sniper', color:'#16c88a', s:cota, arr:COTA});
  cota.createPriceLine({ price:100, color:'rgba(255,255,255,.26)', lineWidth:1, lineStyle:2,
     axisLabelVisible:true, title:'Base 100' });

  function addLine(data,color,name){
    if(!data||!data.length) return;
    const ls=chart.addLineSeries({ color:color, lineWidth:2, priceLineVisible:false,
        lastValueVisible:true, crosshairMarkerRadius:4 });
    ls.setData(data);
    series.push({name:name, color:color, s:ls, arr:data});
  }
  addLine(IBOV,'#3b82f6','IBOV');
  addLine(SP500,'#e0a92e','S&P 500');
  addLine(CDI,'#a855f7','CDI');

  chart.timeScale().fitContent();

  // ===== Legenda viva (crosshair) =====
  const legend=document.getElementById('legend');
  function paint(vals){
    legend.innerHTML = series.map((it,i)=>
      `<div style="display:flex;align-items:center;gap:8px;line-height:1.65">
         <span style="width:10px;height:10px;border-radius:2px;background:${it.color};display:inline-block"></span>
         <span style="color:#9aa0ac;font-size:11px;min-width:72px">${it.name}</span>
         <span style="color:#eaecef;font-size:12.5px;font-weight:600;font-family:'JetBrains Mono',monospace;font-variant-numeric:tabular-nums">${vals[i]!=null?vals[i].toFixed(2):'—'}</span>
       </div>`).join('');
  }
  function lastVals(){ return series.map(it=> it.arr.length? it.arr[it.arr.length-1].value : null); }
  paint(lastVals());
  chart.subscribeCrosshairMove(param=>{
    if(!param.time){ paint(lastVals()); return; }
    const vals=series.map(it=>{ const d=param.seriesData.get(it.s); return d? (d.value!==undefined?d.value:d.close) : null; });
    paint(vals);
  });

  // ===== Botões de período =====
  const bar=document.getElementById('toolbar');
  const lastT=COTA[COTA.length-1].time;
  function setRange(opt){
    try{
      if(opt===null){ chart.timeScale().fitContent(); return; }
      const from=new Date(lastT+'T00:00:00');
      if(opt==='ytd'){ from.setMonth(0); from.setDate(1); }
      else { from.setMonth(from.getMonth()-opt); }
      const f=from.toISOString().slice(0,10);
      chart.timeScale().setVisibleRange({from:f, to:lastT});
    }catch(e){ chart.timeScale().fitContent(); }
  }
  const btns=[['1M',1],['3M',3],['6M',6],['Ano','ytd'],['Tudo',null]];
  btns.forEach(([label,opt],idx)=>{
    const b=document.createElement('button');
    b.textContent=label;
    b.style.cssText="background:#1b2030;color:#9aa0ac;border:1px solid #2a2e39;border-radius:6px;"+
      "padding:3px 9px;font-size:11px;font-weight:600;cursor:pointer;font-family:Inter;transition:.12s";
    b.onmouseenter=()=>{ if(!b.dataset.active){ b.style.color='#d1d4dc'; } };
    b.onmouseleave=()=>{ if(!b.dataset.active){ b.style.color='#9aa0ac'; } };
    b.onclick=()=>{
      Array.from(bar.children).forEach(c=>{ c.dataset.active=''; c.style.background='#1b2030'; c.style.color='#9aa0ac'; c.style.borderColor='#2a2e39'; });
      b.dataset.active='1'; b.style.background='rgba(22,200,138,.14)'; b.style.color='#16c88a'; b.style.borderColor='rgba(22,200,138,.5)';
      setRange(opt);
    };
    if(label==='Tudo'){ b.dataset.active='1'; b.style.background='rgba(22,200,138,.14)'; b.style.color='#16c88a'; b.style.borderColor='rgba(22,200,138,.5)'; }
    bar.appendChild(b);
  });

  // ===== Responsivo =====
  new ResizeObserver(()=>chart.applyOptions({width:el.clientWidth,height:el.clientHeight})).observe(el);
})();
</script>
"""
    html = (template
            .replace("__H__", str(altura))
            .replace("__COTA__", json.dumps(cota))
            .replace("__IBOV__", json.dumps(ibov))
            .replace("__SP500__", json.dumps(sp500))
            .replace("__CDI__", json.dumps(cdi)))
    components.html(html, height=altura + 6, scrolling=False)


# --- ESTADO DA SESSÃO ---
if 'precos_manuais' not in st.session_state:
    st.session_state.precos_manuais = {}

# --- SIDEBAR ---
st.sidebar.title("🎯 Painel de Comando")
if st.sidebar.button("🔄 Sincronizar Nuvem", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
st.sidebar.markdown("---")
with st.sidebar.expander("💲 Atualizar Preço Manual", expanded=False):
    t_manual = st.text_input("Ticker (Ex: EZTCB194)").upper().strip()
    p_manual = st.number_input("Preço Atual", min_value=0.0, format="%.2f", key="p_man")
    if st.button("Salvar Preço"):
        st.session_state.precos_manuais[t_manual] = p_manual
        st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("Sniper Quant Terminal · Fase 1\nGráfico: TradingView lightweight-charts")

# --- PROCESSAMENTO ---
df_trades = carregar_dados(URL_GOOGLE_SHEETS)

if df_trades.empty:
    st.markdown("<div class='tv-head'><div class='tv-sym'><div class='tv-sym-name'>SNIPER QUANT "
                "<span class='tv-badge'>FASE 1</span></div></div></div>", unsafe_allow_html=True)
    st.warning("Nenhum trade foi lido da planilha. Clique em **🔄 Sincronizar Nuvem** ou verifique a URL/compartilhamento do Google Sheets.")
    st.stop()

# ===== Posições em aberto (preço médio cronológico) =====
posicoes_list = []
for ativo in df_trades['Ticker'].unique():
    trades_ativo = df_trades[df_trades['Ticker'] == ativo].sort_values(['Data', 'ID'])
    qtd_aberta, p_medio, teve_venda_parcial = 0, 0.0, False
    for _, row in trades_ativo.iterrows():
        if row['Operacao'] == 'Compra':
            nova_qtd, preco_compra = row['Qtd'], row['Preco']
            if (qtd_aberta + nova_qtd) > 0:
                p_medio = ((p_medio * qtd_aberta) + (preco_compra * nova_qtd)) / (qtd_aberta + nova_qtd)
            qtd_aberta += nova_qtd
        elif row['Operacao'] == 'Venda':
            qtd_aberta -= row['Qtd']
            teve_venda_parcial = True
            if qtd_aberta <= 0:
                qtd_aberta, p_medio, teve_venda_parcial = 0, 0.0, False
    if qtd_aberta > 0:
        status_parcial = "⚠️ PARCIAL" if teve_venda_parcial else "INTEGRAL"
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

# ===== Métricas principais =====
vendas_hist = df_trades[df_trades['Operacao'] == "Venda"].sort_values('Data')
lucro_realizado = vendas_hist['Resultado_R$'].sum()
lucro_latente = sum(p['L/P R$'] for p in posicoes_list)
patrimonio_total = CAPITAL_INICIAL + lucro_realizado + lucro_latente
valor_cota = patrimonio_total / COTAS_INICIAIS
var_cota_pct = ((valor_cota / 100) - 1) * 100

n_trades = len(vendas_hist)
wins = int((vendas_hist['Resultado_R$'] > 0).sum()) if n_trades else 0
win_rate = (wins / n_trades * 100) if n_trades else 0.0

# ===== MÉTRICAS QUANT (sobre trades fechados) =====
_res = vendas_hist['Resultado_R$']
_ganhos = _res[_res > 0]
_perdas = _res[_res < 0]
gross_win = float(_ganhos.sum())
gross_loss = float(abs(_perdas.sum()))
profit_factor = (gross_win / gross_loss) if gross_loss > 0 else float('inf')
expectancy = float(_res.mean()) if n_trades else 0.0
avg_win = float(_ganhos.mean()) if len(_ganhos) else 0.0
avg_loss = float(abs(_perdas.mean())) if len(_perdas) else 0.0
payoff = (avg_win / avg_loss) if avg_loss > 0 else float('inf')
melhor_trade = float(_res.max()) if n_trades else 0.0
pior_trade = float(_res.min()) if n_trades else 0.0

# R-múltiplo médio (resultado / risco), ignorando risco zero/NaN
if 'Risco' in vendas_hist.columns:
    _rm = vendas_hist[vendas_hist['Risco'] > 0].copy()
    r_multiplo = float((_rm['Resultado_R$'] / _rm['Risco']).mean()) if len(_rm) else 0.0
    risco_medio = float(vendas_hist['Risco'].replace(0, pd.NA).dropna().mean() or 0.0)
else:
    r_multiplo, risco_medio = 0.0, 0.0

# Média de dias por trade
dias_medios = float(vendas_hist['DiasUteis'].replace(0, pd.NA).dropna().mean() or 0.0) if 'DiasUteis' in vendas_hist.columns else 0.0

# Maior sequência de wins / losses (cronológico)
streak_w = streak_l = cur_w = cur_l = 0
for _v in _res.tolist():
    if _v > 0:
        cur_w += 1; cur_l = 0
    elif _v < 0:
        cur_l += 1; cur_w = 0
    else:
        cur_w = cur_l = 0
    streak_w = max(streak_w, cur_w)
    streak_l = max(streak_l, cur_l)


def fmt_ratio(x):
    return "∞" if x == float('inf') else fmt_num(x, 2)


# ===== EDGE POR FAIXA DE IFR =====
def calcular_edge_ifr(vh):
    if vh.empty or 'IFR_Entrada' not in vh.columns:
        return []
    faixas = [(0, 5, "IFR 0–5"), (5, 10, "IFR 5–10"), (10, 15, "IFR 10–15"), (15, 1e9, "IFR 15+")]
    out = []
    base = vh[vh['IFR_Entrada'] > 0]  # ignora trades sem IFR registrado
    for lo, hi, nome in faixas:
        bloco = base[(base['IFR_Entrada'] >= lo) & (base['IFR_Entrada'] < hi)]
        n = len(bloco)
        if n == 0:
            out.append({"faixa": nome, "n": 0, "wr": 0.0, "ret": 0.0, "res": 0.0})
            continue
        wr = (bloco['Resultado_R$'] > 0).mean() * 100
        ret = bloco['Retorno_pct'].mean() if 'Retorno_pct' in bloco.columns else 0.0
        res = bloco['Resultado_R$'].sum()
        out.append({"faixa": nome, "n": n, "wr": float(wr), "ret": float(ret), "res": float(res)})
    return out

# ===== Série da cota (Base 100) =====
data_inicial = df_trades['Data'].min() - pd.Timedelta(days=1)
df_chart = pd.DataFrame({'Data': [pd.to_datetime(data_inicial)], 'Cota': [100.0]})
if not vendas_hist.empty:
    vendas_diarias = vendas_hist.groupby(vendas_hist['Data'].dt.date)['Resultado_R$'].sum().reset_index()
    vendas_diarias['Cota_Acum'] = (CAPITAL_INICIAL + vendas_diarias['Resultado_R$'].cumsum()) / COTAS_INICIAIS
    vendas_diarias['Data'] = pd.to_datetime(vendas_diarias['Data'])
    df_chart = pd.concat([df_chart, vendas_diarias[['Data', 'Cota_Acum']].rename(columns={'Cota_Acum': 'Cota'})])

hoje = pd.to_datetime(datetime.now().date())
if hoje.dayofweek == 5:
    ultimo_dia_util = hoje - pd.Timedelta(days=1)
elif hoje.dayofweek == 6:
    ultimo_dia_util = hoje - pd.Timedelta(days=2)
else:
    ultimo_dia_util = hoje
if not df_chart.empty and df_chart['Data'].iloc[-1].date() == ultimo_dia_util.date():
    df_chart.loc[df_chart.index[-1], 'Cota'] = valor_cota
else:
    df_chart = pd.concat([df_chart, pd.DataFrame({'Data': [ultimo_dia_util], 'Cota': [valor_cota]})], ignore_index=True)

# Drawdown máximo (sobre a curva da cota)
_cs = df_chart.dropna(subset=['Cota']).sort_values('Data')['Cota']
max_dd = ((_cs / _cs.cummax()) - 1).min() * 100 if len(_cs) else 0.0

# ============================================================
# RENDER: HEADER + KPIs
# ============================================================
_dt_ini = df_trades['Data'].min().strftime('%d/%m/%Y')
_chg_cls = "pos" if var_cota_pct >= 0 else "neg"
_arrow = "▲" if var_cota_pct >= 0 else "▼"

st.markdown(f"""
<div class="tv-head">
  <div class="tv-sym">
    <div class="tv-sym-name">SNIPER QUANT <span class="tv-badge">FASE 1</span></div>
    <div class="tv-sym-sub">Cota Base 100 · {n_trades} trades fechados · desde {_dt_ini}</div>
  </div>
  <div class="tv-price">
    <div class="tv-price-val">{fmt_num(valor_cota)}</div>
    <div class="tv-price-chg {_chg_cls}">{_arrow} {fmt_num(abs(var_cota_pct))}%</div>
  </div>
</div>
""", unsafe_allow_html=True)


def _tile(label, value, cls="", sub=""):
    sub_html = f"<div class='s'>{sub}</div>" if sub else ""
    return f"<div class='kpi'><div class='l'>{label}</div><div class='v {cls}'>{value}</div>{sub_html}</div>"

kpis = "".join([
    _tile("Patrimônio", fmt_brl(patrimonio_total)),
    _tile("L/P Latente", fmt_brl(lucro_latente), "pos" if lucro_latente >= 0 else "neg"),
    _tile("L/P Realizado", fmt_brl(lucro_realizado), "pos" if lucro_realizado >= 0 else "neg"),
    _tile("Win Rate", f"{fmt_num(win_rate,1)}%", "", f"{wins}/{n_trades} trades"),
    _tile("Posições Abertas", str(len(posicoes_list)), "", f"{fmt_brl(lucro_latente)} latente"),
])
st.markdown(f"<div class='kpi-row'>{kpis}</div>", unsafe_allow_html=True)

# ===== Segunda linha: Métricas Quant (recolhível) =====
with st.expander("⚙️ Métricas Quant", expanded=True):
    quant = "".join([
        _tile("Profit Factor", fmt_ratio(profit_factor),
              "pos" if profit_factor >= 1 else "neg", "ganho bruto ÷ perda bruta"),
        _tile("Expectancy", fmt_brl(expectancy),
              "pos" if expectancy >= 0 else "neg", "resultado médio/trade"),
        _tile("Payoff", fmt_ratio(payoff), "", f"ganho {fmt_brl(avg_win)} · perda {fmt_brl(avg_loss)}"),
        _tile("R-Múltiplo Médio", fmt_num(r_multiplo, 2),
              "pos" if r_multiplo >= 0 else "neg", f"risco médio {fmt_brl(risco_medio)}"),
        _tile("Melhor / Pior", f"{fmt_brl(melhor_trade)}", "pos", f"pior {fmt_brl(pior_trade)}"),
        _tile("Sequências", f"{streak_w}W / {streak_l}L", "", f"média {fmt_num(dias_medios,1)} dias/trade"),
        _tile("Drawdown Máx.", f"{fmt_num(max_dd,2)}%", "neg" if max_dd < 0 else "", "maior queda da cota"),
    ])
    st.markdown(f"<div class='kpi-row' style='margin-bottom:0'>{quant}</div>", unsafe_allow_html=True)

# ============================================================
# GRÁFICO PRINCIPAL (benchmarks + cota)
# ============================================================
_bench_end = datetime.now()


def _baixar_benchmark(ticker, nome_col):
    try:
        raw = yf.download(ticker, start=df_chart['Data'].min(), end=_bench_end,
                          interval="1d", progress=False)
        if raw.empty:
            return pd.DataFrame()
        serie = raw['Close']
        if hasattr(serie, 'columns'):
            serie = serie.iloc[:, 0]
        serie_norm = (serie / serie.iloc[0]) * 100
        df_bench = serie_norm.reset_index()
        df_bench.columns = ['Data', nome_col]
        return df_bench
    except Exception:
        return pd.DataFrame()


with st.spinner("Carregando benchmarks (IBOV · S&P 500 · CDI)…"):
    ibov_df = _baixar_benchmark("^BVSP", "IBOV")
    sp500_df = _baixar_benchmark("^GSPC", "SP500")
    cdi_df_raw = baixar_cdi_bcb(df_chart['Data'].min(), _bench_end)
    if not cdi_df_raw.empty:
        base = cdi_df_raw['CDI_Acum'].iloc[0]
        cdi_df_raw['CDI'] = (cdi_df_raw['CDI_Acum'] / base) * 100
        cdi_df = cdi_df_raw[['Data', 'CDI']].copy()
    else:
        cdi_df = pd.DataFrame()

render_tradingview_chart(
    cota=serie_para_json(df_chart, 'Cota'),
    ibov=serie_para_json(ibov_df, 'IBOV'),
    sp500=serie_para_json(sp500_df, 'SP500'),
    cdi=serie_para_json(cdi_df, 'CDI'),
    altura=480,
)

# ============================================================
# EDGE POR FAIXA DE IFR (o coração do setup)
# ============================================================
st.markdown("<div class='sec-label'>🎯 Edge por Faixa de IFR (entrada)</div>", unsafe_allow_html=True)
edge = calcular_edge_ifr(vendas_hist)
if edge and any(e["n"] > 0 for e in edge):
    _wr_max = max((e["wr"] for e in edge if e["n"] > 0), default=100) or 100
    linhas = [
        "<div class='edge-row'>"
        "<div class='edge-faixa edge-head'>FAIXA</div>"
        "<div class='edge-track' style='background:transparent'><span class='edge-head'>WIN RATE</span></div>"
        "<div class='edge-ret edge-head'>RET. MÉD.</div>"
        "<div class='edge-n edge-head'>TRADES</div></div>"
    ]
    for e in edge:
        if e["n"] == 0:
            linhas.append(
                f"<div class='edge-row'><div class='edge-faixa'>{e['faixa']}</div>"
                f"<div class='edge-track'></div>"
                f"<div class='edge-ret' style='color:#555b66'>—</div>"
                f"<div class='edge-n'>0</div></div>")
            continue
        larg = max(6.0, e["wr"] / _wr_max * 100)
        cor = C_UP if e["ret"] >= 0 else C_DOWN
        cor_ret = "pos" if e["ret"] >= 0 else "neg"
        linhas.append(
            f"<div class='edge-row'>"
            f"<div class='edge-faixa'>{e['faixa']}</div>"
            f"<div class='edge-track'><div class='edge-fill' style='width:{larg:.1f}%;"
            f"background:linear-gradient(90deg,{cor}bb,{cor})'>{e['wr']:.0f}%</div></div>"
            f"<div class='edge-ret {cor_ret}'>{e['ret']:+.2f}%</div>"
            f"<div class='edge-n'>{e['n']}</div></div>")
    st.markdown(f"<div class='edge-wrap'>{''.join(linhas)}</div>", unsafe_allow_html=True)
    _melhor_faixa = max((e for e in edge if e["n"] > 0), key=lambda x: x["wr"])
    st.caption(f"Barra = Win Rate · cor = sinal do retorno médio · melhor faixa por WR: "
               f"**{_melhor_faixa['faixa']}** ({_melhor_faixa['wr']:.0f}% em {_melhor_faixa['n']} trades). "
               f"IFR lido na entrada (coluna IFR2 da planilha).")
else:
    st.info("Sem IFR de entrada registrado nos trades fechados para montar o edge.")

# ============================================================
# POSIÇÕES EM ABERTO
# ============================================================
st.subheader("Posições em Aberto")
if posicoes_list:
    df_pos = pd.DataFrame(posicoes_list)
    st.dataframe(
        df_pos.style.format({"P.Médio": "R$ {:.2f}", "Atual": "R$ {:.2f}",
                             "L/P R$": "R$ {:.2f}", "L/P %": "{:.2f}%"})
        .map(colorir_lucro_prejuizo, subset=['L/P R$', 'L/P %'])
        .map(colorir_status, subset=['Status']),
        use_container_width=True, hide_index=True
    )
else:
    st.info("Nenhuma posição aberta.")

# ============================================================
# MATRIZ DE PERFORMANCE MENSAL
# ============================================================
st.subheader("📊 Matriz de Performance")
modo_visao = st.radio("Nível de Detalhe:", ["Resumido (Apenas %)", "Detalhado (Trades | WR)"],
                      horizontal=True, label_visibility="collapsed")
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

    if modo_visao == "Resumido (Apenas %)":
        res_mensal['Display'] = res_mensal['Retorno_%'].apply(lambda x: f"{x:.2f}%")
    else:
        res_mensal['Display'] = res_mensal.apply(
            lambda x: f"{x['Retorno_%']:.2f}%\n({int(x['Total_Trades'])}t | {x['WinRate']:.0f}%)", axis=1)

    pivot_retorno = res_mensal.pivot(index='Ano', columns='Mês_Num', values='Display')
    meses_nomes = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                   7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    pivot_retorno = pivot_retorno.rename(columns=meses_nomes)

    def colorir_matrix_string(val):
        if pd.isna(val) or val == "-":
            return 'color:#555b66; text-align:center;'
        if str(val).strip().startswith('-'):
            return 'background-color:rgba(234,57,67,.15); color:#ea3943; text-align:center; font-weight:700;'
        return 'background-color:rgba(22,200,138,.15); color:#16c88a; text-align:center; font-weight:700;'

    st.dataframe(pivot_retorno.style.map(colorir_matrix_string), use_container_width=True)
    st.caption(f"Visualização: {modo_visao} · retorno sobre capital inicial de {fmt_brl(CAPITAL_INICIAL)}")
else:
    st.info("Aguardando dados para gerar a matriz.")

# ============================================================
# LIVRO-RAZÃO
# ============================================================
with st.expander("🛠️ Ver Histórico Completo (Livro-Razão)"):
    df_hist_view = df_trades.copy()
    df_hist_view['ID'] = pd.to_numeric(df_hist_view['ID'], errors='coerce')
    df_hist_view = df_hist_view.sort_values(by=['Data', 'Operacao'], ascending=[False, False])
    df_hist_view['Resultado %'] = df_hist_view.apply(
        lambda x: (x['Resultado_R$'] / ((x['Preco'] * x['Qtd']) - x['Resultado_R$'])) * 100
        if x['Operacao'] == "Venda" and (x['Preco'] * x['Qtd'] - x['Resultado_R$']) != 0 else 0, axis=1)
    st.dataframe(
        df_hist_view.style.format({"Preco": "R$ {:.2f}", "Resultado_R$": "R$ {:.2f}", "Resultado %": "{:.2f}%"})
        .map(colorir_lucro_prejuizo, subset=['Resultado_R$', 'Resultado %']),
        use_container_width=True, hide_index=True
    )
