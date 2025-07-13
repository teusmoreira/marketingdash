import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -------------------- CONFIGURAÇÃO DA PÁGINA --------------------
st.set_page_config(
    page_title="Dashboard de Análise de NPS",
    page_icon="icons8-marketing-100.png",
    layout="wide"
)

# --- NOME DO ARQUIVO DEFINIDO DIRETAMENTE NO CÓDIGO ---
NOME_ARQUIVO_NPS = "NPS Dados 2025.1.xlsx"

# -------------------- FUNÇÕES DE CÁLCULO --------------------
def classificar_nps(nota):
    if nota <= 6:
        return 'Detrator'
    elif nota <= 8:
        return 'Passivo'
    else:
        return 'Promotor'

def calcular_score_nps(df):
    total_respostas = len(df)
    if total_respostas == 0:
        return 0
    promotores = df[df['classificacao'] == 'Promotor'].shape[0]
    detratores = df[df['classificacao'] == 'Detrator'].shape[0]
    percent_promotores = (promotores / total_respostas) * 100
    percent_detratores = (detratores / total_respostas) * 100
    return round(percent_promotores - percent_detratores)

# -------------------- CARREGAMENTO DOS DADOS --------------------
@st.cache_data
def carregar_dados(nome_arquivo):
    if nome_arquivo.endswith('.csv'):
        return pd.read_csv(nome_arquivo, encoding='latin-1', sep=';')
    else:
        return pd.read_excel(nome_arquivo)

# -------------------- INTERFACE PRINCIPAL --------------------
st.sidebar.image("icons8-marketing-100.png", width=100)

try:
    df_original = carregar_dados(NOME_ARQUIVO_NPS)
    df_original.rename(columns={'NPS Quantitativo': 'nota_nps', 'Data': 'data'}, inplace=True)
    df_original['data'] = pd.to_datetime(df_original['data'])
    df_original['classificacao'] = df_original['nota_nps'].apply(classificar_nps)
except FileNotFoundError:
    st.error(f"Erro: Arquivo '{NOME_ARQUIVO_NPS}' não encontrado.")
    st.info("Por favor, certifique-se de que o arquivo de dados e o script Python estão na mesma pasta.")
    st.stop()
except Exception as e:
    st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
    st.info("Verifique se o arquivo não está corrompido e se as colunas foram renomeadas corretamente no código.")
    st.stop()

# ---- FILTROS LATERAIS (com a nova caixa de pesquisa) ----
data_inicio = st.sidebar.date_input('De:', df_original['data'].min().date())
data_fim = st.sidebar.date_input('Até:', df_original['data'].max().date())
data_inicio_dt = pd.to_datetime(data_inicio)
data_fim_dt = pd.to_datetime(data_fim)
df_filtrado = df_original[(df_original['data'] >= data_inicio_dt) & (df_original['data'] <= data_fim_dt)]

# --- NOVO: Caixa de Pesquisa por Empresa ---
if 'Empresa' in df_filtrado.columns:
    termo_pesquisa = st.sidebar.text_input("Pesquisar Empresa por Nome:")
    if termo_pesquisa:
        # Filtra o dataframe com base no texto digitado, ignorando maiúsculas/minúsculas
        df_filtrado = df_filtrado[df_filtrado['Empresa'].str.contains(termo_pesquisa, case=False, na=False)]

# --- Filtros Categóricos em lista ---
filtros_disponiveis = ['Plano do Cliente', 'Setor', 'Canal'] # Removido 'Empresa' daqui pois já tem a busca
for filtro in filtros_disponiveis:
    if filtro in df_filtrado.columns:
        # As opções agora são baseadas no dataframe já pré-filtrado pela busca
        opcoes = df_filtrado[filtro].unique()
        opcoes_selecionadas = st.sidebar.multiselect(
            f'Filtrar por {filtro}',
            options=opcoes,
            default=opcoes
        )
        df_filtrado = df_filtrado[df_filtrado[filtro].isin(opcoes_selecionadas)]

# -------------------- PAINEL PRINCIPAL (DASHBOARD) --------------------
st.title("Análise de NPS e Critérios")
st.markdown("---")

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados. Por favor, ajuste os filtros ou o termo de pesquisa.")
    st.stop()

# ----- KPIs -----
# (O código dos KPIs e do resto do dashboard continua o mesmo)
score_nps_final = calcular_score_nps(df_filtrado)
total_respostas = len(df_filtrado)
total_promotores = df_filtrado[df_filtrado['classificacao'] == 'Promotor'].shape[0]
total_passivos = df_filtrado[df_filtrado['classificacao'] == 'Passivo'].shape[0]
total_detratores = df_filtrado[df_filtrado['classificacao'] == 'Detrator'].shape[0]

st.header("Visão Geral do NPS", divider='blue')
col1, col2, col3 = st.columns(3)
col1.metric("Score NPS Final", f"{score_nps_final}")
col2.metric("Total de Respostas", f"{total_respostas}")
col3.metric("Promotores", f"{total_promotores/total_respostas:.1%}")
st.write("")
col_det, col_pas, col_pro = st.columns(3)
with col_det:
    st.error(f"**Detratores:** {total_detratores} ({total_detratores/total_respostas:.1%})")
with col_pas:
    st.warning(f"**Passivos:** {total_passivos} ({total_passivos/total_respostas:.1%})")
with col_pro:
    st.success(f"**Promotores:** {total_promotores} ({total_promotores/total_respostas:.1%})")

st.markdown("---")

# -------------------- GERADOR DE GRÁFICOS PERSONALIZADOS --------------------
st.header("Gerador de Gráficos Personalizados", divider='rainbow')
colunas_categoricas = [col for col in ['Setor', 'Plano do Cliente', 'Empresa', 'Canal', 'classificacao'] if col in df_filtrado.columns]
metricas_disponiveis = ['Contagem de Respostas', 'Score NPS']
col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
with col_sel1:
    tipo_grafico = st.selectbox("Tipo de Gráfico", options=['Barras', 'Pizza (Rosca)'])
with col_sel2:
    eixo_x = st.selectbox("Eixo X", options=colunas_categoricas, help="Selecione a categoria principal para agrupar os dados.")
with col_sel3:
    eixo_y = st.selectbox("Eixo Y", options=metricas_disponiveis, help="Selecione a métrica que você quer analisar.")
with col_sel4:
    cor = st.selectbox("Agrupar por Cor", options=[None] + colunas_categoricas, help="Opcional. Separe os dados por uma segunda categoria usando cores.")

if eixo_x and eixo_y:
    if tipo_grafico == 'Barras':
        if eixo_y == 'Score NPS':
            df_grafico = df_filtrado.groupby([eixo_x] + ([cor] if cor else [])).apply(calcular_score_nps).reset_index(name='valor')
        else:
            df_grafico = df_filtrado.groupby([eixo_x] + ([cor] if cor else [])).size().reset_index(name='valor')
        figura = px.bar(df_grafico, x=eixo_x, y='valor', color=cor, text='valor', title=f'{eixo_y} por {eixo_x}' + (f' agrupado por {cor}' if cor else ''))
        figura.update_traces(texttemplate='%{text:.2s}')
    elif tipo_grafico == 'Pizza (Rosca)':
        if eixo_y != 'Contagem de Respostas':
            st.warning(f"Gráficos de Pizza mostram melhor a 'Contagem de Respostas'. A métrica foi alterada automaticamente.")
        df_grafico = df_filtrado.groupby(eixo_x).size().reset_index(name='valor')
        figura = px.pie(df_grafico, names=eixo_x, values='valor', hole=0.4, title=f'Contagem de Respostas por {eixo_x}')
    st.plotly_chart(figura, use_container_width=True)


# -------------------- GRÁFICO DE RADAR (TEIA) --------------------
st.markdown("---")
st.header("Análise Comparativa de Critérios (Gráfico de Radar)", divider='green')

colunas_de_notas = [col for col in df_filtrado.columns if df_filtrado[col].dtype in ['int64', 'float64'] and col not in ['nota_nps']]
colunas_de_agrupamento = [col for col in ['Empresa', 'Setor', 'Plano do Cliente', 'Canal'] if col in df_filtrado.columns]

if not colunas_de_notas or not colunas_de_agrupamento:
    st.warning("Para gerar o Gráfico de Radar, são necessárias colunas de notas numéricas (ex: 'Atendimento', 'Preço') e colunas de categoria (ex: 'Empresa', 'Setor') no arquivo.")
else:
    col_radar1, col_radar2 = st.columns(2)
    with col_radar1:
        categoria_radar = st.selectbox("Selecione a categoria para comparar:", options=colunas_de_agrupamento)
    with col_radar2:
        # As opções de itens agora são baseadas no dataframe já filtrado (inclusive pela busca)
        itens_selecionados_radar = st.multiselect(
            f"Selecione os itens de '{categoria_radar}' para plotar:",
            options=df_filtrado[categoria_radar].unique()
        )
    if not itens_selecionados_radar:
        st.info(f"Selecione um ou mais itens em '{categoria_radar}' para gerar o gráfico.")
    else:
        fig_radar = go.Figure()
        df_radar_filtrado = df_filtrado[df_filtrado[categoria_radar].isin(itens_selecionados_radar)]
        df_media_radar = df_radar_filtrado.groupby(categoria_radar)[colunas_de_notas].mean().reset_index()

        for item in itens_selecionados_radar:
            dados_item = df_media_radar[df_media_radar[categoria_radar] == item]
            if not dados_item.empty:
                valores = dados_item[colunas_de_notas].values.flatten().tolist()
                textos_rotulos = [f'{v:.1f}' for v in valores]
                valores.append(valores[0])
                textos_rotulos.append(textos_rotulos[0])
                categorias_theta = colunas_de_notas + [colunas_de_notas[0]]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=valores, theta=categorias_theta, fill='toself', name=str(item),
                    mode='lines+markers+text', text=textos_rotulos, textposition='top center',
                    textfont=dict(size=12),
                    hovertemplate=f"<b>{item}</b><br>Critério: %{{theta}}<br>Nota Média: %{{r:.2f}}<extra></extra>"
                ))
                
        fig_radar.update_layout(
            template='plotly_dark', polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=True, title=f"Comparativo de Notas Médias por '{categoria_radar}'"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# -------------------- GRÁFICO DE TENDÊNCIA --------------------
st.markdown("---")
# (O restante do código de tendência e feedbacks continua igual)
st.header("Análise de Tendências", divider='blue')
df_filtrado['mes_ano'] = df_filtrado['data'].dt.to_period('M').astype(str)
metrica_linha = st.selectbox("Escolha a métrica para ver a tendência:", options=metricas_disponiveis)
if metrica_linha == 'Score NPS':
    df_grafico_linha = df_filtrado.groupby('mes_ano').apply(calcular_score_nps).reset_index(name='valor')
else:
    df_grafico_linha = df_filtrado.groupby('mes_ano').size().reset_index(name='valor')
fig_linha_dinamico = px.line(df_grafico_linha, x='mes_ano', y='valor', markers=True, text='valor', title=f'Tendência Mensal de {metrica_linha}')
fig_linha_dinamico.update_traces(textposition="top center")
st.plotly_chart(fig_linha_dinamico, use_container_width=True)

st.markdown("---")
if 'Justificativa' in df_filtrado.columns:
    st.header("Análise de Feedbacks", divider='blue')
    df_detratores = df_filtrado[df_filtrado['classificacao'] == 'Detrator'][['nota_nps', 'Justificativa']].dropna()
    st.subheader("Feedbacks Recentes de Detratores")
    st.dataframe(df_detratores.tail(10), use_container_width=True)