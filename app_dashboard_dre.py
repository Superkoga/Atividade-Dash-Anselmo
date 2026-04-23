import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc

# ========================
# LOGIN
# ========================
USER = "admin"
PASSWORD = "123"

# ========================
# CARREGAR DADOS
# ========================
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

df = carregar_dados()

# ========================
# APP
# ========================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# ========================
# LOGIN LAYOUT
# ========================
login_layout = dbc.Container([
    html.H2("Login", className="mt-4"),
    dbc.Input(id="user", placeholder="Usuário", className="mb-2"),
    dbc.Input(id="password", type="password", placeholder="Senha", className="mb-2"),
    dbc.Button("Entrar", id="login-btn", color="primary"),
    html.Div(id="login-output", className="mt-2")
])

# ========================
# DASHBOARD LAYOUT
# ========================
dashboard_layout = dbc.Container([

    html.H1("Dashboard DRE", className="mt-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Selecione o mês"),
            dcc.Dropdown(
                id="mes",
                options=[{"label": m, "value": m} for m in sorted(df["Mes"].unique())],
                multi=True
            )
        ], width=4)
    ]),

    dcc.Graph(id="grafico"),

    html.H3("Detecção de perdas"),
    html.Div(id="perdas", className="mb-4"),

    dbc.Button("Exportar PDF", id="pdf-btn", color="success"),
    html.Div(id="pdf-output", className="mt-2")

], fluid=True)

# ========================
# LAYOUT PRINCIPAL
# ========================
app.layout = html.Div([
    dcc.Store(id="login-status", data=False),
    html.Div(id="page-content", children=login_layout)  # 👈 mostra login inicial
])

# ========================
# LOGIN CALLBACK
# ========================
@app.callback(
    Output("login-status", "data"),
    Output("login-output", "children"),
    Input("login-btn", "n_clicks"),
    State("user", "value"),
    State("password", "value")
)
def login(n, user, password):
    if n:
        if user == USER and password == PASSWORD:
            return True, "Login realizado com sucesso!"
        else:
            return False, "Usuário ou senha inválidos."
    return False, ""

# ========================
# TROCA DE TELA
# ========================
@app.callback(
    Output("page-content", "children"),
    Input("login-status", "data")
)
def render_page(logged):
    if logged:
        return dashboard_layout
    return login_layout

# ========================
# GRÁFICO + PERDAS
# ========================
@app.callback(
    Output("grafico", "figure"),
    Output("perdas", "children"),
    Input("mes", "value")
)
def atualizar(meses):
    df_f = df.copy()

    if meses:
        df_f = df_f[df_f["Mes"].isin(meses)]

    resumo = df_f.groupby(["Mes", "Tipo"])["Valor"].sum().reset_index()

    fig = px.bar(
        resumo,
        x="Mes",
        y="Valor",
        color="Tipo",
        barmode="group",
        title="Realizado vs Orçado"
    )

    pivot = resumo.pivot(index="Mes", columns="Tipo", values="Valor").fillna(0)
    pivot["Diferença"] = pivot.get("Realizado", 0) - pivot.get("Orçado", 0)

    perdas = pivot[pivot["Diferença"] < 0]

    if perdas.empty:
        texto = "Nenhuma perda identificada ✅"
    else:
        texto = [
            html.P(f"Mês {i}: perda de R$ {abs(row['Diferença']):,.0f}")
            for i, row in perdas.iterrows()
        ]

    return fig, texto

# ========================
# EXPORTAR PDF (CORRIGIDO)
# ========================
@app.callback(
    Output("pdf-output", "children"),
    Input("pdf-btn", "n_clicks"),
    State("mes", "value")
)
def exportar_pdf(n, meses):
    if n:
        df_f = df.copy()

        if meses:
            df_f = df_f[df_f["Mes"].isin(meses)]

        resumo = df_f.groupby(["Mes", "Tipo"])["Valor"].sum().reset_index()

        fig = px.bar(
            resumo,
            x="Mes",
            y="Valor",
            color="Tipo",
            barmode="group",
            title="Realizado vs Orçado"
        )

        fig.write_image("dashboard.pdf")

        return "PDF gerado com sucesso!"

    return ""

# ========================
# RUN
# ========================
if __name__ == "__main__":
    app.run(debug=True)