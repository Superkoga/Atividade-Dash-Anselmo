import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ========================
# LOGIN
# ========================
USER = "admin"
PASSWORD = "123"

if "logged" not in st.session_state:
    st.session_state.logged = False

# ========================
# CARREGAR DADOS
# ========================
@st.cache_data
def carregar_dados():
    plano = pd.read_excel("DRE 2019.xlsx", sheet_name="Plano de Contas")
    realizado = pd.read_excel("DRE 2019.xlsx", sheet_name="Realizado")
    orcado = pd.read_excel("DRE 2019.xlsx", sheet_name="Orçado")

    realizado["Conta"] = realizado["Conta"].astype(str)
    orcado["Conta"] = orcado["Conta"].astype(str)
    plano["Conta"] = plano["Conta"].astype(str)

    realizado["Mês/Ano"] = pd.to_datetime(realizado["Mês/Ano"])
    orcado["Mês/Ano"] = pd.to_datetime(orcado["Mês/Ano"])

    df_real = realizado.merge(plano, on="Conta", how="left")
    df_orc = orcado.merge(plano, on="Conta", how="left")

    df_real["Tipo"] = "Realizado"
    df_orc["Tipo"] = "Orçado"

    df_real = df_real.rename(columns={"Valor Realizado": "Valor"})
    df_orc = df_orc.rename(columns={"Valor Orçado": "Valor"})

    df = pd.concat([df_real, df_orc], ignore_index=True)

    df["Ano"] = df["Mês/Ano"].dt.year
    df["Mes"] = df["Mês/Ano"].dt.month

    return df

# ========================
# LOGIN UI
# ========================
def tela_login():
    st.title("🔐 Login")

    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == USER and password == PASSWORD:
            st.session_state.logged = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

# ========================
# DASHBOARD
# ========================
def dashboard():
    st.title("📊 Dashboard DRE")

    df = carregar_dados()

    # filtro
    meses = st.multiselect(
        "Selecione o mês",
        options=sorted(df["Mes"].unique())
    )

    df_f = df.copy()

    if meses:
        df_f = df_f[df_f["Mes"].isin(meses)]

    resumo = df_f.groupby(["Mes", "Tipo"])["Valor"].sum().reset_index()

    # gráfico
    fig = px.bar(
        resumo,
        x="Mes",
        y="Valor",
        color="Tipo",
        barmode="group",
        title="Realizado vs Orçado"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ========================
    # PERDAS
    # ========================
    st.subheader("🔍 Detecção de perdas")

    pivot = resumo.pivot(index="Mes", columns="Tipo", values="Valor").fillna(0)
    pivot["Diferença"] = pivot.get("Realizado", 0) - pivot.get("Orçado", 0)

    perdas = pivot[pivot["Diferença"] < 0]

    if perdas.empty:
        st.success("Nenhuma perda identificada ✅")
    else:
        for i, row in perdas.iterrows():
            st.error(f"Mês {i}: perda de R$ {abs(row['Diferença']):,.0f}")

    # ========================
    # EXPORTAÇÃO (FUNCIONAL)
    # ========================
    st.subheader("📥 Exportar")

    # CSV
    csv = df_f.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Baixar dados (CSV)",
        data=csv,
        file_name="dados_dre.csv",
        mime="text/csv"
    )

    # IMAGEM (substitui PDF)
    if st.button("Gerar imagem do gráfico"):
        buf = io.BytesIO()
        fig.write_image(buf, format="png")

        st.download_button(
            label="Baixar gráfico (PNG)",
            data=buf.getvalue(),
            file_name="dashboard.png",
            mime="image/png"
        )

# ========================
# APP PRINCIPAL
# ========================
if not st.session_state.logged:
    tela_login()
else:
    dashboard()
