import pandas as pd
from sqlalchemy import create_engine
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

# Conexión a MySQL
DB_USER = "root"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_NAME = "mi_base_de_datos"

def cargar_datos():
    try:
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
        df = pd.read_sql_query("SELECT * FROM mi_tabla", engine)
        df.columns = df.columns.str.lower().str.strip()
        return df
    except Exception as err:
        print(f"Error de MySQL: {err}")
        return None

df = cargar_datos()
if df is None:
    raise ValueError("No se pudieron cargar los datos desde MySQL.")

columnas_necesarias = {'analisis', 'total_po', 'ciudad', 'aliado', 'región'}
if not columnas_necesarias.issubset(set(df.columns)):
    raise ValueError(f"Faltan columnas necesarias en la base de datos. Columnas disponibles: {df.columns}")

df['porcentaje'] = (df['analisis'].sum() / df['total_po'].sum()) * 100

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src="/assets/claro_logo.png", height="80px"), width=12, className="text-center")
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Porcentaje de Análisis", className="text-center text-white"),
                    html.H2(id='resultado-porcentaje', className="text-center text-danger fw-bold")
                ])
            ], className="shadow-lg p-3 mb-4 bg-dark rounded")
        ], width=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🎯 Público Objetivo", className="text-center text-white"),
                    html.H2(id='publico-objetivo', className="text-center text-primary fw-bold")
                ])
            ], className="shadow-lg p-3 mb-4 bg-dark rounded")
        ], width=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📥 Cargas en Presenze", className="text-center text-white"),
                    html.H2(id='cargas-presenze', className="text-center text-success fw-bold")
                ])
            ], className="shadow-lg p-3 mb-4 bg-dark rounded")
        ], width=4),
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🔍 Filtros", className="text-center text-white"),
                    dcc.Dropdown(id='filtro-ciudad', multi=True, placeholder="Seleccione una ciudad"),
                    dcc.Dropdown(id='filtro-aliado', multi=True, placeholder="Seleccione un aliado"),
                    dcc.Dropdown(id='filtro-region', multi=True, placeholder="Seleccione una región")
                ])
            ], className="shadow-lg p-3 mb-4 bg-dark rounded")
        ], width=6)
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico-barras'), width=6),
        dbc.Col(dcc.Graph(id='grafico-lineas'), width=6)
    ])
], fluid=True, style={'backgroundColor': '#C3131F'})

@app.callback(
    [Output('resultado-porcentaje', 'children'),
     Output('publico-objetivo', 'children'),
     Output('cargas-presenze', 'children'),
     Output('grafico-barras', 'figure'),
     Output('grafico-lineas', 'figure'),
     Output('filtro-ciudad', 'options'),
     Output('filtro-aliado', 'options'),
     Output('filtro-region', 'options')],
    [Input('filtro-ciudad', 'value'),
     Input('filtro-aliado', 'value'),
     Input('filtro-region', 'value')]
)
def actualizar_dashboard(ciudad, aliado, region):
    df_filtrado = df.copy()
    if region:
        df_filtrado = df_filtrado[df_filtrado['región'].isin(region)]
    if ciudad:
        df_filtrado = df_filtrado[df_filtrado['ciudad'].isin(ciudad)]
    if aliado:
        df_filtrado = df_filtrado[df_filtrado['aliado'].isin(aliado)]
    
    porcentaje = (df_filtrado['analisis'].sum() / df_filtrado['total_po'].sum()) * 100 if not df_filtrado.empty else 0
    publico_objetivo = df_filtrado['total_po'].sum()
    cargas_presenze = df_filtrado['analisis'].sum()
    
    df_barras = df_filtrado.groupby('ciudad', as_index=False)['analisis'].sum()
    fig_barras = go.Figure(go.Bar(x=df_barras['analisis'], y=df_barras['ciudad'], orientation='h', text=df_barras['analisis'], textposition='outside', marker_color='#C3131F'))
    fig_barras.update_layout(title="📊 Análisis por Ciudad", xaxis_title="Análisis", yaxis_title="Ciudad", plot_bgcolor='black', paper_bgcolor='black', font=dict(color='white'))
    
    df_lineas = df_filtrado.groupby('aliado', as_index=False)['analisis'].sum()
    fig_lineas = go.Figure(go.Scatter(x=df_lineas['aliado'], y=df_lineas['analisis'], mode='lines+markers', line=dict(color='#C3131F')))
    fig_lineas.update_layout(title="📈 Análisis por Aliado", xaxis_title="Aliado", yaxis_title="Suma de Análisis", plot_bgcolor='black', paper_bgcolor='black', font=dict(color='white'))
    
    ciudades_options = [{'label': c, 'value': c} for c in df_filtrado['ciudad'].unique()]
    aliados_options = [{'label': a, 'value': a} for a in df_filtrado['aliado'].unique()]
    regiones_options = [{'label': r, 'value': r} for r in df['región'].unique()]
    
    return f"{porcentaje:.2f}%", publico_objetivo, cargas_presenze, fig_barras, fig_lineas, ciudades_options, aliados_options, regiones_options

if __name__ == '__main__':
    app.run(debug=True)