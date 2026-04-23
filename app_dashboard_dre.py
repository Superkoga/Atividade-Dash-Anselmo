import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Dashboard DRE 🚀")

df = pd.read_excel("DRE 2019.xlsx", sheet_name="Realizado")

df["Mês/Ano"] = pd.to_datetime(df["Mês/Ano"])
df["Mes"] = df["Mês/Ano"].dt.month

meses = st.multiselect(
    "Selecione o mês",
    options=sorted(df["Mes"].unique())
)

if meses:
    df = df[df["Mes"].isin(meses)]

fig = px.bar(df, x="Mes", y="Valor Realizado", title="Valores por mês")

st.plotly_chart(fig)

st.success("App funcionando!")
