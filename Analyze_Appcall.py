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
st.sidebar.subheader("Consolidado")
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


df = df.rename(columns = {'Total Aprovado': 'Total_Aprovado'}, inplace = False)

ranking_appcall= df
# Segmentação por Contribuição do CallCenter no Faturamento do site

ranking_appcall ['Dimensionamento_AppCall'] = (ranking_appcall ['Total Call Center']/ranking_appcall ['Total_Aprovado'])*100
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

# Churn

ranking_appcall.loc[(ranking_appcall['Total_Aprovado'] == 0), 'Status_Processamento'] = "CHURN"
ranking_appcall.loc[(ranking_appcall['Total_Aprovado'] > 0)&(ranking_appcall['Total_Aprovado'] <= input_prechurn), 'Status_Processamento'] = "Pre-CHURN"
ranking_appcall.loc[(ranking_appcall['Total_Aprovado'] > input_prechurn), 'Status_Processamento'] = "Processando"



# Filter in SideBar
status_processamento =  st.sidebar.multiselect('Selecione o Status da Operação',options=ranking_appcall['Status_Processamento'].unique(),default=ranking_appcall['Status_Processamento'].unique())
squad = st.sidebar.multiselect ("Selecione o Squad", options=ranking_appcall['Squad'].unique(),default=ranking_appcall['Squad'].unique())
Ativo_Inativo = st.sidebar.multiselect ("Segmentação Appcall", options=ranking_appcall['Status_Appcall'].unique(),default=ranking_appcall['Status_Appcall'].unique())


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


st.markdown('#')

# Detalhamento operação do parceiro
st.title('Análise de Pedidos do Parceiro')
st.markdown('Esse é o arquivo que estou analisando:')

# Sidebar
st.sidebar.subheader("Parceiro")

# Setup file upload
uploaded_file2 = st.sidebar.file_uploader(label="Upload", type=['csv','xlsx'])

global df2
if uploaded_file2 is not None:

	print(uploaded_file2)

	try:
		df2 = pd.read_csv(uploaded_file2)



	except Exception as e:
		print(e)
		df2 = pd.read_excel(uploaded_file2,engine='openpyxl')


try:
	st.dataframe(data=df2,width=2000,height=150)
except Exception as e:
	print(e)

# Filter in SideBar
Filtro_origem =  st.sidebar.multiselect('Selecione a origem dos pedidos',options=df2['origem'].unique(),default=df2['origem'].unique())


# Resultado da Query
# st.header('Resultado do Filtro')
df_selection_Origem = df2.query("origem == @Filtro_origem" )





df_selection_Origem['Quantidade Pedidos'] = 1

faturamento_total_df2 = df2['total_pedido'].sum()

fatramento_total_selection = df_selection_Origem['total_pedido'].sum()

total_pedidos = df_selection_Origem['Quantidade Pedidos'].sum()

maior_pedido = df_selection_Origem['total_pedido'].max()

menor_pedido = df_selection_Origem['total_pedido'].min()


st.markdown('#')

# Mapeando origem dos pedidos:

st.subheader('Mapeando a origem dos Pedidos')
origem_pedidos = df2.groupby('origem').sum()


origem_pedidos ['Dimensionamento'] = (origem_pedidos ['total_pedido']/faturamento_total_df2)*100

origem_pedidos

# grafico ORIGEM
st.markdown('#')
grafico_origem_pedidos = px.pie(origem_pedidos,values='Dimensionamento', names=origem_pedidos.index, title='Composição dos Pedidos')
st.plotly_chart(grafico_origem_pedidos,use_container_width=True)

st.subheader('Estatísticas Gerais')

st.markdown('#')

C5, C6 = st.columns(2)
with C5:
	st.write(f'**Quantidade de pedidos analisados:** {total_pedidos}')
	st.write(f'**Faturamento Total =** R$ {fatramento_total_selection}')
with C6:
	st.write(f'**Maior Venda =** R$ {maior_pedido}')
	st.write(f'**Menor Venda =** R$ {menor_pedido}')

st.markdown('#')


# Mapeando produtos do parceiro
st.subheader('Ranking Produtos mais vendidos')
ranking_pedidos_produtos = df_selection_Origem.groupby('bundle').sum()

ranking_pedidos_produtos = ranking_pedidos_produtos.sort_values('total_pedido',ascending=False)
ranking_pedidos_produtos.drop(columns=['id_pedido'])
ranking_pedidos_produtos

st.write('Exporte documentos conforme o filtro escolhido:')
def to_excel(dataframe1):
	    output = BytesIO()
	    writer = pd.ExcelWriter(output, engine='xlsxwriter')
	    dataframe1.to_excel(writer, sheet_name='Sheet1')
	    writer.save()
	    processed_data = output.getvalue()
	    return processed_data

def get_table_download_link(dataframe1):
	    """Generates a link allowing the data in a given panda dataframe to be downloaded
	    in:  dataframe
	    out: href string
	    """
	    val = to_excel(dataframe1)
	    b64 = base64.b64encode(val)  # val looks like b'...'
	    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download Lista de Produtos!</a>' # decode b'abc' => abc

dataframe1 = ranking_pedidos_produtos # your dataframe
st.markdown(get_table_download_link(dataframe1), unsafe_allow_html=True)
st.markdown('#')


# Detalhamento LEADS do parceiro

st.title('LEADS do Parceiro')
st.markdown('Esse é o arquivo que estou analisando:')

# Sidebar
st.sidebar.subheader("LEADS")

# Setup file upload
uploaded_file3 = st.sidebar.file_uploader(label="Leads", type=['csv','xlsx'])

global df3
if uploaded_file3 is not None:

	print(uploaded_file3)

	try:
		df3 = pd.read_csv(uploaded_file2)



	except Exception as e:
		print(e)
		df3 = pd.read_excel(uploaded_file3,engine='openpyxl')


try:
	st.dataframe(data=df3,width=2000,height=150)
except Exception as e:
	print(e)

	st.markdown('#')
	st.markdown('#')
	st.markdown('#')


Cx , Cy = st.columns(2)
with Cx:
	st.subheader('Ranking de Leads')


	df3 ['Quantidade'] = 1

	ranking_leads_abandonados = df3.groupby('Pacote de interesse').sum()
	ranking_leads_abandonados = ranking_leads_abandonados.sort_values('Quantidade',ascending=False)
	ranking_leads_abandonados = ranking_leads_abandonados.drop(columns=['Telefone','Número de documento'])
	ranking_leads_abandonados

	st.write('Exporte documentos conforme o filtro escolhido:')
	def to_excel(dataframe2):
			output = BytesIO()
			writer = pd.ExcelWriter(output, engine='xlsxwriter')
			dataframe2.to_excel(writer, sheet_name='Sheet1')
			writer.save()
			processed_data = output.getvalue()
			return processed_data

	def get_table_download_link(dataframe2):
			"""Generates a link allowing the data in a given panda dataframe to be downloaded
			in:  dataframe
			out: href string
			"""
			val = to_excel(dataframe2)
			b64 = base64.b64encode(val)  # val looks like b'...'
			return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Carrinhos Abandonados!</a>' # decode b'abc' => abc

	dataframe2 = ranking_leads_abandonados # your dataframe
	st.markdown(get_table_download_link(dataframe2), unsafe_allow_html=True)
	st.markdown('#')


with Cy:

	st.subheader('Ranking Cliente Final')
	# Ranking Cliente Final
	ranking_leads_clientes = df3.groupby(['Email','Telefone']).sum()
	ranking_leads_clientes = ranking_leads_clientes.sort_values('Quantidade',ascending=False)

	ranking_leads_clientes


