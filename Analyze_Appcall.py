import pandas as pd
import streamlit as st
import plotly_express as px
import plotly.graph_objects as go
import base64
from io import BytesIO


# Config Uploader
st.set_option('deprecation.showfileUploaderEncoding', False)


# Title of the app
st.set_page_config(page_title="Analyze Appcall", page_icon=":bar_chart:", layout="wide")
st.title('AppCall Performance')
st.markdown('Esse é o arquivo que estou analisando:')

# Sidebar
st.sidebar.subheader("Settings")
# Setup file upload
uploaded_file = st.sidebar.file_uploader(label="Upload CSV or Excel file here", type=['csv','xlsx'])

global df
if uploaded_file is not None:

	print(uploaded_file)

	try:
		df = pd.read_csv(uploaded_file)



	except Exception as e:
		print(e)
		df = pd.read_excel(uploaded_file,engine='openpyxl')


try:
	st.dataframe(data=df,width=2000,height=150)
except Exception as e:
	print(e)

input_prechurn = st.number_input('Digite o parâmetro a ser utilizado como pre-CHURN',min_value=100,max_value=5000,value=100,step=100)
input_Estorno = st.number_input('Digite o percentual de estorno aceitável',min_value=0.0,max_value=100.0,value=5.0,step=0.25)
input_Chargeback = st.number_input('Digite o percentual de chargeback aceitável',min_value=0.0,max_value=100.0,value=2.0,step=0.25)

# Churn
df ['Dimensionamento_AppCall'] = (df['Total Call Center']/df['Total Aprovado'])*100
df.loc[(df['Total Aprovado'] == 0), 'Status_Processamento'] = "CHURN"
df.loc[(df['Total Aprovado'] > 0)&(df['Total Aprovado'] <= input_prechurn), 'Status_Processamento'] = "Pre-CHURN"
df.loc[(df['Total Aprovado'] > input_prechurn), 'Status_Processamento'] = "Processando"

# Estorno
df ['Percentual_Estornos'] = (df['Pedidos Estornados']/df['Total Aprovado'])*100
df.loc[(df['Percentual_Estornos'] > input_Estorno), 'Status_Estorno'] = "Alerta"
df.loc[(df['Percentual_Estornos'] <= input_Estorno), 'Status_Estorno'] = "aceitável"
df.loc[(df['Percentual_Estornos'] > 50.0), 'Status_Estorno'] = "PREOCUPANTE"

# Charageback
df ['Percentual_Chargeback'] = (df['Pedidos Chargeback']/df['Total Aprovado'])*100
df.loc[(df['Percentual_Chargeback'] > input_Chargeback), 'Status_Chargeback'] = "Alerta"
df.loc[(df['Percentual_Chargeback'] <= input_Chargeback), 'Status_Chargeback'] = "aceitável"
df.loc[(df['Percentual_Chargeback'] > 20.0), 'Status_Chargeback'] = "PREOCUPANTE"


df = df.rename(columns = {'Total Aprovado': 'Total_Aprovado'}, inplace = False)

ranking_appcall= df
# Segmentação por Contribuição do CallCenter no Faturamento do site
ranking_appcall ['Dimensionamento_AppCall'].fillna(0, inplace=True)

ranking_appcall ['Status_Appcall'] = ranking_appcall  ['Dimensionamento_AppCall']
ranking_appcall.loc[(ranking_appcall['Dimensionamento_AppCall'] > 0) & (ranking_appcall['Dimensionamento_AppCall'] <= 5), 'Status_Appcall'] = "Até 5%"
ranking_appcall.loc[ranking_appcall['Dimensionamento_AppCall'] == 0, 'Status_Appcall'] = "Inativo"
ranking_appcall.loc[(ranking_appcall['Dimensionamento_AppCall'] > 5) & (ranking_appcall['Dimensionamento_AppCall'] < 10), 'Status_Appcall'] = "5% a 10%"
ranking_appcall.loc[ranking_appcall['Dimensionamento_AppCall'] >= 10, 'Status_Appcall'] = "Maior que 10%"

ranking_appcall_QntParceiro = ranking_appcall
ranking_appcall_QntParceiro['Quantidade Sites'] = 1
Estatisticas_Status_Appcall = ranking_appcall_QntParceiro.groupby('Status_Appcall').sum()
Estatisticas_Status_Appcall = Estatisticas_Status_Appcall.drop(columns=['Dimensionamento_AppCall'])
Estatisticas_Status_Appcall ['Média Leads'] = Estatisticas_Status_Appcall['Leads']/Estatisticas_Status_Appcall['Quantidade Sites']

# Filter in SideBar
status_processamento =  st.sidebar.multiselect('Selecione o Status da Operação',options=ranking_appcall['Status_Processamento'].unique(),default=ranking_appcall['Status_Processamento'].unique())
squad = st.sidebar.multiselect ("Selecione o Squad", options=ranking_appcall['Squad'].unique(),default=ranking_appcall['Squad'].unique())
Ativo_Inativo = st.sidebar.multiselect ("Segmentação Appcall", options=ranking_appcall['Status_Appcall'].unique(),default=ranking_appcall['Status_Appcall'].unique())
# Situation_Reversals = st.sidebar.multiselect ("ESTORNO", options=ranking_appcall['Status_Estorno'].unique(),default=ranking_appcall['Status_Estorno'].unique())
# Situation_Chargeback = st.sidebar.multiselect ("CHARGEBACK", options=ranking_appcall['Status_Chargeback'].unique(),default=ranking_appcall['Status_Chargeback'].unique())


# Resultado da Query
# st.header('Resultado do Filtro')
df_selection_AppCall = ranking_appcall.query("Status_Processamento == @status_processamento & Status_Appcall == @Ativo_Inativo & Squad == @squad" )
st.header('Ranking AppCall')
df_selection_AppCall = df_selection_AppCall.sort_values('Total Call Center',ascending=False)
st.dataframe(df_selection_AppCall)
st.write('Exporte documentos conforme o filtro escolhido:')
def to_excel(dataframe):
	    output = BytesIO()
	    writer = pd.ExcelWriter(output, engine='xlsxwriter')
	    dataframe.to_excel(writer, sheet_name='Sheet1')
	    writer.save()
	    processed_data = output.getvalue()
	    return processed_data

def get_table_download_link(dataframe):
	    """Generates a link allowing the data in a given panda dataframe to be downloaded
	    in:  dataframe
	    out: href string
	    """
	    val = to_excel(dataframe)
	    b64 = base64.b64encode(val)  # val looks like b'...'
	    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download Lista de Sites!</a>' # decode b'abc' => abc

dataframe = df_selection_AppCall # your dataframe
st.markdown(get_table_download_link(dataframe), unsafe_allow_html=True)
st.markdown('#')

# Definindo variáveis relevantes

Sites_Analisados = len(df_selection_AppCall)
st.write(f'**Sites Analisados:** {Sites_Analisados}')

# Repetir os gráficos de cima só que referenciando o df da query!!!!
	#### --> Grafico Comparando Faturamento Total e Faturamento Appcall por STATUS_APPCALL

st.header('Faturamento conforme Status AppCall')

agrupa_status_df_selection = df_selection_AppCall.groupby('Status_Appcall').sum()
agrupa_status_df_selection = agrupa_status_df_selection.drop(columns=['Dimensionamento_AppCall'])
agrupa_status_df_selection ['Média Leads'] = agrupa_status_df_selection['Leads']/agrupa_status_df_selection['Quantidade Sites']
agrupa_status_df_selection

GraficoTotal_Estatisticas_Status_Appcall = px.bar(agrupa_status_df_selection,y=agrupa_status_df_selection.index,x='Total_Aprovado',orientation="v",title="<b>Total da Operação</b>")
GraficoCall_Estatisticas_Status_Appcall = px.bar(agrupa_status_df_selection,y=agrupa_status_df_selection.index,x='Total Call Center',orientation="v",title="<b>Atuação do Appcall</b>")

plot = go.Figure(data=[go.Bar(name= 'Total da Operação',x=agrupa_status_df_selection.index,y=agrupa_status_df_selection['Total_Aprovado']),go.Bar(name="Atuação AppCall",x=agrupa_status_df_selection.index,y=agrupa_status_df_selection['Total Call Center'])])
plot.update_layout(height=600, width=600)
st.plotly_chart(plot,use_container_width=True)


	#### --> Grafico Comparando Faturamento Total e Faturamento Appcall por SQUAD
st.header('Faturamento conforme Squad')
agrupa_df_selection_squad = df_selection_AppCall.groupby('Squad').sum()

agrupa_df_selection_squad = agrupa_df_selection_squad.drop(columns=['Dimensionamento_AppCall'])
agrupa_df_selection_squad ['Média Leads'] = agrupa_df_selection_squad['Leads']/agrupa_df_selection_squad['Quantidade Sites']
agrupa_df_selection_squad



Grafico_agrupa_df_selection_squad = px.bar(agrupa_df_selection_squad,x=agrupa_df_selection_squad.index,y='Total_Aprovado',orientation="h",title="<b>Total da Operação</b>")
Grafico_agrupa_df_selection_squad = px.bar(agrupa_df_selection_squad,x=agrupa_df_selection_squad.index,y='Total Call Center',orientation="h",title="<b>Atuação do Appcall</b>")

plot = go.Figure(data=[go.Bar(name= 'Total da Operação',x=agrupa_df_selection_squad.index,y=agrupa_df_selection_squad['Total_Aprovado']),go.Bar(name="Atuação AppCall",x=agrupa_df_selection_squad.index,y=agrupa_df_selection_squad['Total Call Center'])])
plot.update_layout(height=600, width=600)
st.plotly_chart(plot,use_container_width=True)

		# Explorando Squad

c3 , c4 = st.columns(2)
with c3:
	Grafico_df_selection_Sites = px.pie(agrupa_df_selection_squad,values='Quantidade Sites', names=agrupa_df_selection_squad.index, title='Sites por Squad')
	st.plotly_chart(Grafico_df_selection_Sites,use_container_width=True)


with c4:
	Grafico_df_selection_Leads = px.pie(agrupa_df_selection_squad,values='Leads', names=agrupa_df_selection_squad.index, title='Leads por Squad')
	st.plotly_chart(Grafico_df_selection_Leads,use_container_width=True)


situation_Reversals = st.sidebar.multiselect ("ESTORNO", options=ranking_appcall['Status_Estorno'].unique(),default=ranking_appcall['Status_Estorno'].unique())
situation_Chargeback = st.sidebar.multiselect ("CHARGEBACK", options=ranking_appcall['Status_Chargeback'].unique(),default=ranking_appcall['Status_Chargeback'].unique())



df_selection_revolution = df.query("Squad == @squad & Status_Estorno == @situation_Reversals & Status_Chargeback == @situation_Chargeback" )

df_selection_revolution 







