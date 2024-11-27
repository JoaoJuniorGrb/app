import streamlit as st
import CoolProp.CoolProp as prop
from CoolProp.CoolProp import PropsSI,PhaseSI
from pathlib import Path
from PIL import Image
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.optimize import fsolve
import requests
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import requests
from io import BytesIO
import firebase_admin
from firebase_admin import credentials, storage, initialize_app
import json
from streamlit_autorefresh import st_autorefresh
import time
from datetime import datetime
import pytz
from firebase_admin import db
import firebase_admin
from firebase_admin import credentials, storage
import json
import control as ctrl
import plotly.graph_objects as go

url_imagem = "https://i0.wp.com/cdn.newspulpaper.com/wp-content/uploads/2024/06/05163805/Submarca-Fiedler-01.png?resize=1068%2C373&ssl=1"
# Esconde o cabeçalho e o rodapé padrão do Streamlit
st.set_page_config(page_title="Fiedler Automação", page_icon="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAqFBMVEUuMo0rMI0oLY8lK48kKpARHJIwNIZiX3ZybXQFFZN2cWvUxS/55wj/7gD/8AD/8wDh0SAdJI9ZVnro1x//9gD/7wB+eGcWIJKPh1/u3ROakVZFRoExNYAmLIPz4RSFfmRNTH0qL44+QITLvTN4c2a4q0jBtD7JvD+VjV47PYfayyqqoE9gXnCIgGNbWXivpEtmY25SUnwAEJRKS34AAJamnFSflVfOwC7jtOtQAAAA/0lEQVR4AWIYcACgih60GIahAIDWippas1f7/79sXrLd4+BRlGTu/0pRNd3gNIGTTAtAhL+ITfkddVzPRxwJFHYXRshHxI/dL5vfqQlBxI7SbMGILKbl4WWwApBHXW8+d5stJLt9TDgPUJbw4B0TTODpHHysHOn78QKvK0LyIgfXjx3LqJS48pbF0fOw/0ZqFpWC+gQr27tGevVx+f4UM7/BFcABpfKLJEm8jzModxZqTboRn4Rfqttc26vRBa7/hInBF7Lp4/Sq2cMYj+enlbMRGDqep2Cy9N0Yzw/AogIn29JMwZAneRc+/S1Zq8RKaDfrlt6HLW0oQqAiw6AAACorHoO4OiwrAAAAAElFTkSuQmCC", layout="wide")

st.sidebar.markdown(
    f"<img src='{url_imagem}' style='width:200px;'/>",
    unsafe_allow_html=True
)
#remove estilo stream lit
remove_st_estilo = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""

st.markdown(remove_st_estilo,unsafe_allow_html=True)
#----------------------------------------------------------------
firebase_creds = dict(st.secrets["firebase"])


# Verifique se o Firebase já está inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'fiedlerapp2024.appspot.com',
        'databaseURL': 'https://fiedlerapp2024-default-rtdb.firebaseio.com'
    })

# Função para carregar o JSON diretamente do Storage
def load_(nome_arquivo):
    bucket = storage.bucket()
    blob = bucket.blob(nome_arquivo)  # Caminho relativo dentro do bucket
    file_data = blob.download_as_bytes()  # Baixa o conteúdo do arquivo como bytes
    return file_data

config = load_("config.yaml")
config = config.decode('utf-8')    
config = yaml.safe_load(config)
#st.write(config)


# Configurando a autenticação
authenticator = stauth.Authenticate(
        
        names=[user['name'] for user in config['credentials']['usernames'].values()],
        usernames=list(config['credentials']['usernames'].keys()),
        passwords=[user['password'] for user in config['credentials']['usernames'].values()],
        cookie_name=config['cookie']['name'],  # Verifique se isso está apontando para 'random_cookie_name'
        key=config['cookie']['key'],  # Verifique se a chave 'random_signature_key' está correta
        cookie_expiry_days=config['cookie']['expiry_days']

    )
# Criando a interface de login
name, authentication_status, username = authenticator.login('Login', 'sidebar')

#Inicial
if authentication_status:
    programas = ["Perda de Carga",'Equações de afinidade',"Propriedades Termodinâmicas","Placa de orificio","QHS","Sistemas de controle","Final", "Base Instalada",'Gestão de projetos']
    legendas1 = ["Cálculo de perda de carga",'Em desenvolvimento',"Fornece gráfico de propriedades termodinamicas selecionadas",'Em desenvolvimento','Em desenvolvimento','Em desenvolvimento',"Informações sobre o programa","Levantamentos","Informações sobre Projetos"]
if not authentication_status:
    programas = ["Perda de Carga",'Equações de afinidade', "Propriedades Termodinâmicas",  "QHS","Sistemas de controle", "Final"]
    legendas1 = ["Cálculo de perda de carga",'Em desenvolvimento', "Fornece gráfico de propriedades termodinamicas selecionadas",
                  'Em desenvolvimento','Em desenvolvimento', "Informações sobre o programa"]
if name == "Fellipe Gebien":
    programas = ["Localização de Pedidos"]
    legendas1 = ["Localização de pedidos a partir da O.V. com acesso a historico de alterções"]

if name == "Joao Hering Ferreira":
    programas = ["Perda de Carga",'Equações de afinidade',"Propriedades Termodinâmicas","Placa de orificio","QHS","Sistemas de controle","Final", "Base Instalada","Localização de Pedidos",'Gestão de projetos']
    legendas1 = ["Cálculo de perda de carga",'Em desenvolvimento',"Fornece gráfico de propriedades termodinamicas selecionadas",'Em desenvolvimento','Em desenvolvimento','Em desenvolvimento',"Informações sobre o programa","Levantamentos","Localização de pedidos a partir da O.V. com acesso a historico de alterções","Informações sobre Projetos"]


st.sidebar.header("Selecione o programa desejado")
applicativo = st.sidebar.radio("Seleção",programas)

if authentication_status == True:
    authenticator.logout('Logout', 'sidebar')

# Mostra a legenda correspondente à opção selecionada
indice_selecionado = programas.index(applicativo)

st.sidebar.write(legendas1[indice_selecionado])
if authentication_status == False:
        st.error('Nome de usuário ou senha incorretos')
if authentication_status == None:
        st.warning('Por favor, insira suas credenciais')
#------------------------------------------------------------------------------------------------------------------------------

if applicativo == "Propriedades Termodinâmicas":
    biblioteca_prop = st.selectbox("Selecione o metodo de Pesquisa",["CoolProp","Cantera","ThermoPy"])
    if biblioteca_prop == "CoolProp":
        dicionario_propriedades = [
            {'Viscosidade': 'VISCOSITY'},
            {'Densidade': 'D'},
            {'Entalpia': 'H'},
            {'Entropia': 'S'},
            {'Qualidade (fração mássica)': 'Q'},
            {'Energia interna': 'U'},
            {'Calor específico a pressão constante': 'C'},
            {'Velocidade do som': 'V'},
            {'Condutividade térmica': 'CONDUCTIVITY'}
        ]
        lista_fluidos = prop.get_global_param_string("fluids_list").split(",")
        st.title('Insira as condições do fluido', anchor=False)

        col1, col2, col3,col4,col5 = st.columns(5)
        with col1:
            st.header("Fluido",anchor=False)
            fluido_selecionado = st.selectbox("Fluido", lista_fluidos, index=93)
        with col2:
            st.header("Pressão",anchor=False)
            pressao = st.number_input("Digite a pressão", min_value=0.1,step=0.1,format="%.1f")
        with col3:
            st.header("Un.",anchor=False)
            un_pressão = st.selectbox("Un",["Bar","Pa"],index=1)
        with col4:
            st.header("Temp.",anchor=False)
            temperatura = st.number_input("Digite a temperatura", min_value=0.1,step=0.1,format="%.1f")
        with col5:
            st.header("Un.", anchor=False)
            un_temperatura = st.selectbox("Un.", ["°C", "K"])

        #obter propriedades atravéz do coolprop
        pressão_consulta = (100000*pressao) if (un_pressão == "Bar") else pressao
        temperatura_consulta = (273.155 + temperatura) if un_temperatura == "°C" else temperatura
        try:
            p_vapor = PropsSI('P', 'T', temperatura_consulta, 'Q', 1, fluido_selecionado)
            p_vapor =   p_vapor/100000
            texto_pvapor = "P vapor {:.3f} Bar".format(p_vapor)
            st.subheader(texto_pvapor, anchor=False, divider="blue")
            viscosidade_Pas = prop.PropsSI('VISCOSITY', 'T', temperatura_consulta, 'P', pressão_consulta, fluido_selecionado)
            densidade = prop.PropsSI('D', 'T', temperatura_consulta, 'P', pressão_consulta, fluido_selecionado)
            qualidade = PhaseSI('P', pressão_consulta, 'T', temperatura_consulta, fluido_selecionado)
            viscosidade_cp = viscosidade_Pas*1000
            temperatura_ebulição = PropsSI('T','P', pressão_consulta,'Q',0,fluido_selecionado)
            temperatura_ebulição = temperatura_ebulição - 273.15
            texto_viscosidade = "{:.3f} Cp".format(viscosidade_cp)
            st.subheader(texto_viscosidade,anchor=False,divider="blue")
            texto_densidade = "{:.3f} kg/m³".format(densidade)
            st.subheader(texto_densidade,anchor=False,divider="blue")
            texto_titulo = qualidade
            st.subheader(texto_titulo,anchor=False,divider="blue")
            texto_ebulição = "Ebulição {:.1f} °C".format(temperatura_ebulição)
            st.subheader(texto_ebulição, anchor=False,divider="blue")
            

        except Exception as e:
            st.subheader("Não disponível para este fluido")
            st.write(str(e))
        st.title('Grafico', anchor=False)
        col6, col7 = st.columns(2)
        with col6:
            condicao_x = st.selectbox("Condição",["Temperatura","Pressão"], index=1)
            if condicao_x == "Pressão":
                grafico_df = pd.DataFrame(columns=["Pressão_Pa","Pressão_sel", "Densidade", "Viscosidade", "Estado"])
                pressao_indice = np.linspace((pressão_consulta-100000),(pressão_consulta+100000),num=101)
                pressao_indice = np.where(pressao_indice < 1000,1000,pressao_indice)
                grafico_df["Pressão_Pa"] = pressao_indice
                grafico_df["Pressão_sel"] = (grafico_df["Pressão_Pa"]/9806.08) if (un_pressão == "MCA") else (grafico_df["Pressão_Pa"]/100000) if (un_pressão == "Bar") else grafico_df["Pressão_Pa"]
                for i in range(len(grafico_df)):
                    grafico_df.loc[(i), "Estado"] = PhaseSI('P', grafico_df.loc[i, "Pressão_Pa"], 'T',temperatura_consulta, fluido_selecionado)
                    if grafico_df.loc[(i), "Estado"] == "liquid":
                        grafico_df.loc[(i),"Densidade"] = prop.PropsSI('D', 'T', temperatura_consulta, 'P', grafico_df.loc[i,"Pressão_Pa"], fluido_selecionado)
                        grafico_df.loc[(i),"Viscosidade"] = 1000*prop.PropsSI('VISCOSITY', 'T', temperatura_consulta, 'P',grafico_df.loc[i, "Pressão_Pa"], fluido_selecionado)
                    else:
                        grafico_df.loc[(i), "Densidade"] = "null"
                        grafico_df.loc[(i), "Viscosidade"] ="null"



            elif condicao_x == "Temperatura":
                grafico_df = pd.DataFrame(columns=["Temperatura_K","Temperatura_sel","Densidade", "Viscosidade", "Estado"])
                temperatura_indice = np.linspace((temperatura_consulta - 100), (temperatura_consulta + 100), num=101)


                temperatura_indice = np.where(temperatura_indice < 1, 274, temperatura_indice)
                grafico_df["Temperatura_K"] = temperatura_indice
                grafico_df["Temperatura_sel"] = (temperatura_indice - 273.15) if un_temperatura == "°C" else temperatura_indice
                for i in range(len(grafico_df)):
                    try:

                        if "liquid" == PhaseSI('P', pressão_consulta, 'T',grafico_df.loc[i, "Temperatura_K"],fluido_selecionado):
                            grafico_df.loc[(i), "Estado"] = PhaseSI('P', pressão_consulta, 'T',grafico_df.loc[i, "Temperatura_K"],fluido_selecionado)
                            grafico_df.loc[(i), "Densidade"] = prop.PropsSI('D', 'T', grafico_df.loc[i, "Temperatura_K"], 'P',pressão_consulta, fluido_selecionado)
                            grafico_df.loc[(i), "Viscosidade"] = 1000*prop.PropsSI('VISCOSITY', 'T', grafico_df.loc[i, "Temperatura_K"], 'P',pressão_consulta, fluido_selecionado)
                        else:
                            grafico_df.loc[(i), "Estado"] = "null"
                            grafico_df.loc[(i), "Densidade"] = "null"
                            grafico_df.loc[(i), "Viscosidade"] = "null"
                            grafico_df.loc[(i), "Estado"] = "null"
                    except Exception as e:
                        if "liquid" == PhaseSI('P', pressão_consulta, 'T', grafico_df.loc[i, "Temperatura_K"],fluido_selecionado):
                            grafico_df.loc[(i), "Estado"] = "null"
                            grafico_df.loc[(i), "Densidade"] = "null"
                            grafico_df.loc[(i), "Viscosidade"] = "null"
                            grafico_df.loc[(i), "Estado"] = "null"

        with col7:
            propriedade_y = st.selectbox("Propriedade", ['Densidade','Viscosidade'], index=1)
        if propriedade_y == 'Densidade' and condicao_x == "Temperatura":
            fig = px.line(grafico_df, x="Temperatura_sel", y="Densidade")
            fig.update_yaxes(title_text='Densidade kg/m³')
        if propriedade_y == 'Viscosidade' and condicao_x == "Temperatura":
            fig = px.line(grafico_df, x="Temperatura_sel", y="Viscosidade")
            fig.update_yaxes(title_text='Viscosidade Cp')
        if propriedade_y == 'Viscosidade' and condicao_x == "Pressão":
            fig = px.line(grafico_df, x="Pressão_sel", y="Viscosidade")
            fig.update_yaxes(title_text='Viscosidade Cp')
        if propriedade_y == 'Densidade' and condicao_x == "Pressão":
            fig = px.line(grafico_df, x="Pressão_sel", y="Densidade")
            fig.update_yaxes(title_text='Densidade kg/m³')
        st.plotly_chart(fig, use_container_width=True)
        #st.table(grafico_df)

#------------------------------------------------------------------------------------------------------------------------------

if applicativo == "QHS":

    def f_velocidade (diametro_int_str,carga_vazao_str):
            area_tubo = 3.1415 * ((diametro_int_str / 1000) ** 2) / 4
            velocidade = (carga_vazao_str / 3600) / area_tubo
            return velocidade

    # Dados da tabela transcritos manualmente
    dados_tubos = {
        'Material': ['Aço carbono'] * 26 + ['Inox'] * 26 + ['PVC'] * 9 + ["Outro"],
        'Bitola nominal': [
            '1/4"', '3/8"', '1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '2 1/2"', '3"', '3.1/2"', '4"', '5"', '6"',
            '8"', '10"', '12"', '14"', '16"', '18"', '20"', '22"', '24"', '26"', '28"', '30"',
            '1/4"', '3/8"', '1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '2 1/2"', '3"', '3.1/2"', '4"', '5"', '6"',
            '8"', '10"', '12"', '14"', '16"', '18"', '20"', '22"', '24"', '26"', '28"', '30"',
            "15", "20", "25", "32", '40', '50', '65', '75', '100', "N/A"],
        'D interno': [
            9.24, 12.53, 15.80, 20.93, 26.64, 35.04, 40.90, 52.50, 62.71, 77.92, 90.12, 102.26, 128.30, 154.08, 202.71,
            254.51, 303.22, 334.34, 381.00, 428.66, 477.82, 527.04, 574.64, 777.84, 825.50, 876.30,
            9.24, 12.53, 15.80, 20.93, 26.64, 35.04, 40.90, 52.50, 62.71, 77.92, 90.12, 102.26, 128.30, 154.08, 202.71,
            254.51, 303.22, 334.34, 381.00, 428.66, 477.82, 527.04, 574.64, 777.84, 825.50, 876.30,
            17, 21.6, 27.8, 35.2, 44, 53.4, 66.6, 75.6, 97.8, "N/A"],
        'SCHEDULE': [40] * 52 + ['NBR5684', 'NBR5685', 'NBR5686', 'NBR5687', 'NBR5688', 'NBR5689', 'NBR5690', 'NBR5691',
                                 'NBR5692', "N/A"]
    }

    # Criação do DataFrame
    df_tubos = pd.DataFrame(dados_tubos)
    rugosidade_data = {'Outro': "n/a", 'Aço carbono': 0.046, 'PVC': 0.0015, 'Inox': 0.015, 'Ferro Fundido': 0.26,
                       'Aço comercial ou ferro Forjado': 0.046}
    materiais_lista = df_tubos['Material'].unique().tolist()
    def get_altitude(municipio):
        df_municipio = get_municipios()
        id_municipio = df_municipio.loc[df_municipio["Município - Estado"] == municipio, "ID"].values[0]
        url = "https://servicodados.ibge.gov.br/api/v1/bdg/municipio/" + str(id_municipio) + "/estacoes"
        response = requests.get(url)
        if response.status_code == 200:
            altitudes_base = response.json()
            data_processed = []
            for item in altitudes_base:
                altitude_normal = item.get('altitudeNormal')
                altitude_geometrica = item.get('altitudeGeometrica')
                data_processed.append({
                    'Código Estação': item['codigoEstacao'],
                    'Município': item['municipio']['nomeMunicipio'],
                    'Estado': item['municipio']['uf']['sigla'],
                    'Latitude': item['latitude'],
                    'Longitude': item['longitude'],
                    'Altitude Normal': str((altitude_normal)) if altitude_normal else None,
                    'Altitude Geométrica': str((altitude_geometrica)) if altitude_geometrica else None,

                })
            df_altitudes = pd.DataFrame(data_processed)

            # Função para converter strings de números para float
            def convert_column_to_float(column):
                return column.str.replace('.', '').str.replace(',', '.').astype(float)

            # Aplicar a conversão para as colunas 'Altitude Normal' e 'Altitude Geométrica'
            df_altitudes['Altitude Normal'] = convert_column_to_float(df_altitudes['Altitude Normal'])
            df_altitudes['Altitude Geométrica'] = convert_column_to_float(
                df_altitudes['Altitude Geométrica'].fillna('0'))  # Preencher NaNs temporariamente
        return df_altitudes


    def get_abspress(altitude, p_o):
        exp = (9.806655 * 0.0289644 / (8.3144594 * 0.0065))
        pressao_abs = p_o * (1 - (altitude * 0.0065 / (288.15))) ** exp
        return pressao_abs


    def get_municipios():
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
        response = requests.get(
            url)  # Faz uma requisição GET para a URL da API do IBGE que retorna os dados dos municípios.
        if response.status_code == 200:  # Verifica se a resposta da requisição foi bem-sucedida (código 200).
            municipios_base = response.json()  # Converte a resposta JSON em um dicionário Python.
            data = []
            for municipio in municipios_base:
                id_municipio = municipio['id']
                nome_municipio = municipio['nome']
                sigla_estado = municipio['microrregiao']['mesorregiao']['UF']['sigla']
                data.append([id_municipio, nome_municipio, sigla_estado])

            df_municipio = pd.DataFrame(data, columns=['ID', 'Nome do Município', 'Sigla do Estado'])
            df_municipio['Município - Estado'] = df_municipio['Nome do Município'] + "-" + df_municipio[
                "Sigla do Estado"]
            return df_municipio  # Retorna os dados dos municípios.
        else:
            municipios_base = [{'Nome do Município': "erro base de dados"}]
            return df_municipio


    try:
        municipios_base = get_municipios()
        municipio = st.selectbox("Selecione o municipio", municipios_base['Município - Estado'])
    except Exception as e:
        municipios_base = "0"
        st.success("API IBGE Indisponível")

    # st.dataframe(municipios_base)
    try:
        df_altitude = get_altitude(municipio)
        min_altitude = int(df_altitude["Altitude Normal"].min())
        max_altitude = int(df_altitude["Altitude Normal"].max())
        med_altitude = int(df_altitude["Altitude Normal"].mean())
        # st.dataframe(df_altitude)
        # st.info("Min{}m | Med {}m | Max {}m".format(min_altitude,med_altitude,max_altitude))
    except Exception as e:
        min_altitude = -1
        max_altitude = "Vazio"
        med_altitude = 0
    if min_altitude == -1:
        altitude_npsh = st.number_input("Altitude (Sem dados IBGE)", min_value=0, value=0, step=1)
    else:
        altitude_npsh = st.number_input(
            "Altitude Min {}m | Med {}m | Max {}m".format(min_altitude, med_altitude, max_altitude),
            min_value=0, value=med_altitude, step=1, )
    abs_press = get_abspress(altitude_npsh, 101325)
    abs_bar = abs_press / (100000)
    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])
    with col1:
        st.header("Vap. 1", anchor=False)
        fluido_selecionado_1 = st.selectbox("Vapor", ("Saturado","Superaquecido"), key="fluido_1")
        massa_vapor_1_kgh = st.number_input("Vazão [kg/h]", min_value=0.0000000001,step=0.1, format="%.1f")

        if fluido_selecionado_1 == "Saturado":
            pressao_vap_1_bar = st.number_input("P Manometrica [bar]", min_value=0.0000000001,step=0.1, format="%.3f")
            pressao_vap_1_pa = float((pressao_vap_1_bar + abs_bar) * 100000)
            densidade_vapor_1 = prop.PropsSI('D', 'P',pressao_vap_1_pa,'Q',1, "Water")

        if fluido_selecionado_1 == "Superaquecido":
            pressao_vap_1_bar = st.number_input("P Manometrica [bar]", min_value=0.0000000001, step=0.1, format="%.3f")
            pressao_vap_1_pa = (pressao_vap_1_bar + abs_bar)* 100000
            temperatura_vap_1_c = st.number_input("Temperatura °C", min_value=-273.10, value = 100.00 ,step=0.1, format="%.1f")
            temperatura_vap_1_k = temperatura_vap_1_c + 273.15
            densidade_vapor_1 = prop.PropsSI('D', 'P', pressao_vap_1_pa, 'T',temperatura_vap_1_k,"Water")
        vazao_vapor_1_mcubh = massa_vapor_1_kgh / densidade_vapor_1
        tipo_tubo = st.selectbox("Tubo", materiais_lista, index=0)
        tipo_tubo_str = str(tipo_tubo)
        df_tubo_sel = df_tubos[df_tubos['Material'] == tipo_tubo_str]
        lista_bitola = df_tubo_sel['Bitola nominal'].unique().tolist()
        rugosidade = rugosidade_data[tipo_tubo_str]
        diametro_tubo = st.selectbox("Diâmetro comercial", lista_bitola, index=0)
        diametro_tubo_str = str(diametro_tubo)
        if tipo_tubo_str == "Outro":
            diametro_int = st.number_input("   Ø int [mm]", min_value=0.01, step=0.1, format="%.1f")
            diametro_int_str = float(diametro_int)
        if tipo_tubo_str != "Outro":
            diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (
                    df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
            diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
            st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
        velocidade = f_velocidade(diametro_int_str, vazao_vapor_1_mcubh)

        velocidades = []
        for index, row in df_tubo_sel.iterrows():
            diametro = row['D interno']
            bitola = row['Bitola nominal']
            vel = f_velocidade(diametro, vazao_vapor_1_mcubh)
            if vel < 35:
                velocidades.append(
                    {'Bitola nominal': bitola, 'Diâmetro interno (mm)': diametro, 'Velocidade (m/s)': vel})
        df_velocidades = pd.DataFrame(velocidades)
        #st.dataframe(df_velocidades)
        bitola_rec_1 = df_velocidades.iloc[0][0]
        st.subheader("Velocidade \n {:.2f} m/s".format(velocidade), anchor=False)
        if velocidade > 35:
            st.info("Recom. {}".format(bitola_rec_1))
        st.info("Velocidade\n 35m/s")


    with col2:
        st.header("Vap. 2", anchor=False)
        fluido_selecionado_2 = st.selectbox("Vapor", ("Saturado", "Superaquecido"), key="fluido_2")
        massa_vapor_2_kgh = st.number_input("Vazão [kg/h]", min_value=0.0000000001, step=0.1, format="%.1f",key = "massa_2")

        if fluido_selecionado_2 == "Saturado":
            pressao_vap_2_bar = st.number_input("P Manometrica [bar]", min_value=0.0000000001, step=0.1, format="%.3f",key = "pressao_2")
            pressao_vap_2_pa = float((pressao_vap_2_bar + abs_bar) * 100000)
            densidade_vapor_2 = prop.PropsSI('D', 'P', pressao_vap_2_pa, 'Q', 1, "Water")

        if fluido_selecionado_2 == "Superaquecido":
            pressao_vap_2_bar = st.number_input("P Manometrica [bar]", min_value=0.0000000001, step=0.1, format="%.3f", key = 'superaquecido_2')
            pressao_vap_2_pa = (pressao_vap_2_bar + abs_bar) * 100000
            temperatura_vap_2_c = st.number_input("Temperatura °C", min_value=-273.10, value=100.00, step=0.1,format="%.1f", key = "superaquecido_3")
            temperatura_vap_2_k = temperatura_vap_2_c + 273.15
            densidade_vapor_2 = prop.PropsSI('D', 'P', pressao_vap_2_pa, 'T', temperatura_vap_2_k, "Water")
        vazao_vapor_2_mcubh = massa_vapor_2_kgh / densidade_vapor_2
        tipo_tubo = st.selectbox("Tubo", materiais_lista, index=0,key = "tubo_2")
        tipo_tubo_str = str(tipo_tubo)
        df_tubo_sel = df_tubos[df_tubos['Material'] == tipo_tubo_str]
        lista_bitola = df_tubo_sel['Bitola nominal'].unique().tolist()
        rugosidade = rugosidade_data[tipo_tubo_str]
        diametro_tubo = st.selectbox("Diâmetro comercial", lista_bitola, index=0,key = "diametro_tubo_2")
        diametro_tubo_str = str(diametro_tubo)
        if tipo_tubo_str == "Outro":
            diametro_int = st.number_input("   Ø int [mm]", min_value=0.01, step=0.1, format="%.1f")
            diametro_int_str = float(diametro_int)
        if tipo_tubo_str != "Outro":
            diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (
                    df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
            diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
            st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
        velocidade = f_velocidade(diametro_int_str, vazao_vapor_2_mcubh)
        velocidades = []
        for index, row in df_tubo_sel.iterrows():
            diametro = row['D interno']
            bitola = row['Bitola nominal']
            vel = f_velocidade(diametro, vazao_vapor_2_mcubh)
            if vel < 35:
                velocidades.append(
                    {'Bitola nominal': bitola, 'Diâmetro interno (mm)': diametro, 'Velocidade (m/s)': vel})
        df_velocidades = pd.DataFrame(velocidades)
        # st.dataframe(df_velocidades)
        bitola_rec_2 = df_velocidades.iloc[0][0]
        st.subheader("Velocidade \n {:.2f} m/s".format(velocidade), anchor=False)
        if velocidade > 35:
            st.info("Recom. {}".format(bitola_rec_2))
        st.info("Velocidade\n 35m/s")

    with col3:
        st.header("Cond.", anchor=False)

        temperatura_vap_3_c = st.number_input("Temperatura °C", min_value=-273.10, value=99.00, step=0.1,format="%.1f")
        temperatura_vap_3_k = temperatura_vap_3_c + 273.15
        massa_vapor_3_kgh = st.number_input("Vazão [kg/h]", min_value=0.0000000001, step=0.1, format="%.1f",key="cond_4")

        pressao_vap_3_bar = st.number_input("P Manometrica [bar]", min_value=0.0000000001,value=1.00 ,step=0.1, format="%.3f",
                                                key="cond_2")
        pressao_vap_3_pa = float((pressao_vap_3_bar + abs_bar) * 100000)
        densidade_vapor_3 = prop.PropsSI('D', 'P', pressao_vap_3_pa, 'T', temperatura_vap_3_k, "Water")


        vazao_vapor_3_mcubh = massa_vapor_3_kgh / densidade_vapor_3
        tipo_tubo = st.selectbox("Tubo", materiais_lista, index=0, key='cond_5')
        tipo_tubo_str = str(tipo_tubo)
        df_tubo_sel = df_tubos[df_tubos['Material'] == tipo_tubo_str]
        lista_bitola = df_tubo_sel['Bitola nominal'].unique().tolist()
        rugosidade = rugosidade_data[tipo_tubo_str]
        diametro_tubo = st.selectbox("Diâmetro comercial", lista_bitola, index=0, key='cond_6')
        diametro_tubo_str = str(diametro_tubo)
        if tipo_tubo_str == "Outro":
            diametro_int = st.number_input("   Ø int [mm]", min_value=0.01, step=0.1, format="%.1f")
            diametro_int_str = float(diametro_int)
        if tipo_tubo_str != "Outro":
            diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (
                    df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
            diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
            st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
        velocidade = f_velocidade(diametro_int_str, vazao_vapor_3_mcubh)

        velocidades = []
        for index, row in df_tubo_sel.iterrows():
            diametro = row['D interno']
            bitola = row['Bitola nominal']
            vel = f_velocidade(diametro, vazao_vapor_3_mcubh)
            if vel < 0.51:
                velocidades.append(
                    {'Bitola nominal': bitola, 'Diâmetro interno (mm)': diametro, 'Velocidade (m/s)': vel})
        df_velocidades = pd.DataFrame(velocidades)
        #st.dataframe(df_velocidades)
        bitola_rec_3 = df_velocidades.iloc[0][0]
        st.subheader("Velocidade \n {:.3f} m/s".format(velocidade), anchor=False)
        if velocidade > 0.51:
            st.info("Recom. {}".format(bitola_rec_3))

        st.info("Velocidade\n 0,5m/s")

    with col4:
            st.header("Hidro 1", anchor=False)
            vazao_succao_mcbh = st.number_input("Vazão [m³/h]", min_value=0.0000000001, step=0.1, format="%.1f",key="sucao1")

            tipo_tubo = st.selectbox("Tubo", materiais_lista, index=0, key='hidro1')
            tipo_tubo_str = str(tipo_tubo)
            df_tubo_sel = df_tubos[df_tubos['Material'] == tipo_tubo_str]
            lista_bitola = df_tubo_sel['Bitola nominal'].unique().tolist()
            rugosidade = rugosidade_data[tipo_tubo_str]
            diametro_tubo = st.selectbox("Diâmetro comercial", lista_bitola, index=0, key='hidro2')
            diametro_tubo_str = str(diametro_tubo)
            if tipo_tubo_str == "Outro":
                diametro_int = st.number_input("   Ø int [mm]", min_value=0.01, step=0.1, format="%.1f")
                diametro_int_str = float(diametro_int)
            if tipo_tubo_str != "Outro":
                diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (
                        df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
                diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
                st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
            velocidade = f_velocidade(diametro_int_str, vazao_succao_mcbh)

            velocidades = []
            for index, row in df_tubo_sel.iterrows():
                diametro = row['D interno']
                bitola = row['Bitola nominal']
                vel = f_velocidade(diametro, vazao_succao_mcbh)
                if vel < 1.5:
                    velocidades.append(
                        {'Bitola nominal': bitola, 'Diâmetro interno (mm)': diametro, 'Velocidade (m/s)': vel})
            df_velocidades = pd.DataFrame(velocidades)
            # st.dataframe(df_velocidades)
            bitola_rec_3 = df_velocidades.iloc[0][0]
            st.subheader("Velocidade \n {:.3f} m/s".format(velocidade), anchor=False)
            st.info("Recom. {}".format(bitola_rec_3))

    with col5:
            st.header("Hidro 2", anchor=False)

            tipo_tubo = st.selectbox("Tubo", materiais_lista, index=0, key='hidro3')
            tipo_tubo_str = str(tipo_tubo)
            df_tubo_sel = df_tubos[df_tubos['Material'] == tipo_tubo_str]
            lista_bitola = df_tubo_sel['Bitola nominal'].unique().tolist()
            rugosidade = rugosidade_data[tipo_tubo_str]
            diametro_tubo = st.selectbox("Diâmetro comercial", lista_bitola, index=0, key='hidro4')
            diametro_tubo_str = str(diametro_tubo)
            if tipo_tubo_str == "Outro":
                diametro_int = st.number_input("   Ø int [mm]", min_value=0.01, step=0.1, format="%.1f")
                diametro_int_str = float(diametro_int)
            if tipo_tubo_str != "Outro":
                diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (
                        df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
                diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
                st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
            velocidade = f_velocidade(diametro_int_str, vazao_succao_mcbh)

            velocidades = []
            for index, row in df_tubo_sel.iterrows():
                diametro = row['D interno']
                bitola = row['Bitola nominal']
                vel = f_velocidade(diametro, vazao_succao_mcbh)
                if vel < 3:
                    velocidades.append(
                        {'Bitola nominal': bitola, 'Diâmetro interno (mm)': diametro, 'Velocidade (m/s)': vel})
            df_velocidades = pd.DataFrame(velocidades)
            # st.dataframe(df_velocidades)
            bitola_rec_3 = df_velocidades.iloc[0][0]
            st.subheader("Velocidade \n {:.3f} m/s".format(velocidade), anchor=False)
            st.info("Recom. {}".format(bitola_rec_3))

#------------------------------------------------------------------------------------------------------------------------------

if applicativo == "Perda de Carga":
    st.header("Perda de Carga", anchor=False)

    # Dados da tabela transcritos manualmente
    dados_tubos = {
    'Material': ['Aço carbono'] * 26 + ['Inox'] * 26 + ['PVC'] * 9 + ["Outro"],
        'Bitola nominal': [
        '1/4"', '3/8"', '1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '2 1/2"', '3"', '3.1/2"', '4"', '5"', '6"', '8"', '10"', '12"', '14"', '16"', '18"', '20"', '22"', '24"', '26"', '28"', '30"',
        '1/4"', '3/8"', '1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '2 1/2"', '3"', '3.1/2"', '4"', '5"', '6"', '8"', '10"', '12"', '14"', '16"', '18"', '20"', '22"', '24"', '26"', '28"', '30"',
        "15", "20", "25", "32", '40', '50', '65', '75', '100' , "N/A"],
    'D interno': [
        9.24, 12.53, 15.80, 20.93, 26.64, 35.04, 40.90, 52.50, 62.71, 77.92, 90.12, 102.26, 128.30, 154.08, 202.71, 254.51, 303.22, 334.34, 381.00, 428.66, 477.82, 527.04, 574.64, 777.84, 825.50, 876.30,
        9.24, 12.53, 15.80, 20.93, 26.64, 35.04, 40.90, 52.50, 62.71, 77.92, 90.12, 102.26, 128.30, 154.08, 202.71, 254.51, 303.22, 334.34, 381.00, 428.66, 477.82, 527.04, 574.64, 777.84, 825.50, 876.30,
        17, 21.6, 27.8, 35.2, 44, 53.4, 66.6, 75.6, 97.8, "N/A"],
    'SCHEDULE': [40] * 52 + ['NBR5684', 'NBR5685', 'NBR5686', 'NBR5687', 'NBR5688', 'NBR5689', 'NBR5690', 'NBR5691', 'NBR5692',"N/A"]
    }


    def get_altitude(municipio):
        df_municipio = get_municipios()
        id_municipio = df_municipio.loc[df_municipio["Município - Estado"] == municipio,"ID"].values[0]
        url = "https://servicodados.ibge.gov.br/api/v1/bdg/municipio/" + str(id_municipio) + "/estacoes"
        response = requests.get(url)
        if response.status_code == 200:
            altitudes_base = response.json()
            data_processed = []
            for item in altitudes_base:
                altitude_normal = item.get('altitudeNormal')
                altitude_geometrica = item.get('altitudeGeometrica')
                data_processed.append({
                    'Código Estação': item['codigoEstacao'],
                    'Município': item['municipio']['nomeMunicipio'],
                    'Estado': item['municipio']['uf']['sigla'],
                    'Latitude': item['latitude'],
                    'Longitude': item['longitude'],
                    'Altitude Normal': str((altitude_normal)) if altitude_normal else None,
                    'Altitude Geométrica': str((altitude_geometrica)) if altitude_geometrica else None,

                })
            df_altitudes = pd.DataFrame(data_processed)

            # Função para converter strings de números para float
            def convert_column_to_float(column):
                return column.str.replace('.', '').str.replace(',', '.').astype(float)

            # Aplicar a conversão para as colunas 'Altitude Normal' e 'Altitude Geométrica'
            df_altitudes['Altitude Normal'] = convert_column_to_float(df_altitudes['Altitude Normal'])
            df_altitudes['Altitude Geométrica'] = convert_column_to_float(
                df_altitudes['Altitude Geométrica'].fillna('0'))  # Preencher NaNs temporariamente
        return df_altitudes
    def get_abspress(altitude,p_o):
        exp = (9.806655*0.0289644/(8.3144594*0.0065))
        pressao_abs = p_o * (1-(altitude*0.0065/(288.15))) ** exp
        return pressao_abs

    def get_municipios():
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
        response = requests.get(url)  # Faz uma requisição GET para a URL da API do IBGE que retorna os dados dos municípios.
        if response.status_code == 200:  # Verifica se a resposta da requisição foi bem-sucedida (código 200).
            municipios_base = response.json()  # Converte a resposta JSON em um dicionário Python.
            data = []
            for municipio in municipios_base:
                id_municipio = municipio['id']
                nome_municipio = municipio['nome']
                sigla_estado = municipio['microrregiao']['mesorregiao']['UF']['sigla']
                data.append([id_municipio, nome_municipio, sigla_estado])

            df_municipio = pd.DataFrame(data, columns=['ID', 'Nome do Município', 'Sigla do Estado'])
            df_municipio['Município - Estado'] = df_municipio['Nome do Município'] + "-" + df_municipio["Sigla do Estado"]
            return df_municipio  # Retorna os dados dos municípios.
        else:
            municipios_base = [{'Nome do Município':"erro base de dados"}]
            return df_municipio

    def calcular_perda_de_carga(f_atrito,comprimento,velocidade,diametro_int_str):
        rey = f_reynolds(carga_densidade, carga_visosidade, velocidade, diametro_int_str)
        if rey > 3000:
            perda_h = float(f_atrito * comprimento * (velocidade ** 2) / (2 * (diametro_int_str/1000)))
            return perda_h
        else:
            perda_h = float(((64/rey) * comprimento * (velocidade ** 2) / (2 * (diametro_int_str/1000))))
            return perda_h

    def perda_acessórios(k,velocidade):
        perda_acess = k*(velocidade**2)/2
        return perda_acess

    def f_colebrook(reynolds,diametro_int_str,rugosidade):
        def equation(f):
            equation = 1 / np.sqrt(f) + 2.0 * np.log10((rugosidade / (diametro_int_str)) / 3.7 + 2.51 / (reynolds * np.sqrt(f)))
            return equation

        iteracao_inicial = 0.02
        fator_atrito, = fsolve(equation,iteracao_inicial)
        return fator_atrito

    def f_reynolds(carga_densidade,carga_visosidade,velocidade,diametro_int_str):
        reynolds = carga_densidade * (diametro_int_str/1000) * velocidade/ carga_visosidade
        reynolds = float(reynolds)
        return reynolds

    def f_velocidade (diametro_int_str,carga_vazao_str):
        area_tubo = 3.1415 * ((diametro_int_str / 1000) ** 2) / 4
        velocidade = (carga_vazao_str / 3600) / area_tubo
        return velocidade
        # lista de acessórios
        # Dicionário com os dados fornecidos
    perda_friccao_dict = {
            'Entrada reentrante': 0.78,
            'Entrada borda viva': 0.5,
            'Cotovelo 45°, padrão': 0.35,
            'Cotovelo 45°, raio longo': 0.2,
            'Cotovelo 90°, padrão': 0.75,
            'Cotovelo 90°, raio longo': 0.45,
            'Cotovelo quadrado ou chanfro': 1.3,
            'Curva 180°, retorno próximo': 1.5,
            'Tê, padrão, ao longo da corrida, ramal bloqueado': 0.4,
            'União': 0.04,
            'Válvula de gaveta, aberta': 0.17,
            'Válvula de gaveta, meia aberta': 0.9,
            'Válvula de gaveta, três quartos aberta': 4.5,
            'Válvula de gaveta, totalmente aberta': 24,
            'Válvula de diafragma, aberta': 2.3,
            'Válvula de diafragma, meia aberta': 2.6,
            'Válvula de diafragma, três quartos aberta': 4.3,
            'Válvula de diafragma, totalmente aberta': 21,
            'Válvula de esfera, totalmente aberta': 0.5,
            'Válvula de esfera, 1/3 fechado': 5.5,
            'Válvula de esfera, 2/3 fechado': 200,
            'Válvula globo, assento biselado, aberta': 6,
            'Válvula globo, assento biselado, meia aberta': 9.5,
            'Válvula globo, assento de composição, aberta': 6,
            'Válvula globo, assento de composição, meia aberta': 8.5,
            'Válvula globo, disco de plugue, aberta': 9,
            'Válvula globo, disco de plugue, meia aberta': 13,
            'Válvula globo, disco de plugue, três quartos aberta': 36,
            'Válvula globo, disco de plugue, totalmente aberta': 112,
            'Válvula Y ou de purga, aberta': 3,
            'Válvula borboleta, θ = 5°': 0.24,
            'Válvula borboleta, θ = 10°': 0.52,
            'Válvula borboleta, θ = 20°': 1.54,
            'Válvula borboleta, θ = 40°': 10.8,
            'Válvula borboleta, θ = 60°': 118,
            'Válvula de retenção, oscilante': 2,
            'Válvula de retenção, disco': 10,
            'Válvula de retenção, esfera': 70,
            'Válvula de pé': 15,
            'Medidor de água, disco': 7,
            'Medidor de água, pistão': 15,
            'Medidor de água, rotativo (disco em forma de estrela)': 10,
            'Medidor de água, roda de turbina': 6
        }

    # Criação do DataFrame
    df_tubos = pd.DataFrame(dados_tubos)
    rugosidade_data = {'Outro':"n/a",'Aço carbono':0.046,'PVC':0.0015,'Inox':0.015,'Ferro Fundido':0.26,'Aço comercial ou ferro Forjado':0.046}
    materiais_lista = df_tubos['Material'].unique().tolist()

    metodo_carga = st.selectbox("Selecione o metodo de calculo", ["Simplificado", "Sucção/NPSH disponível"])
    if metodo_carga == "Simplificado":
        carga1, carga2, carga3, carga4 = st.columns(4)
        with carga1:
            st.header("Distâncias", anchor=False)
            altura_entrada = st.number_input("Altura inicial [m]", min_value=-1000.0, value=0.0, step=0.1,
                                             format="%.1f")
            altura_saida = st.number_input("Altura final [m]", min_value=-1000.0, value=0.0, step=0.1, format="%.1f")
            comprimento_tubulação = st.number_input("Tubulação [m]", min_value=0.0, step=0.1, format="%.1f")
        with carga2:
            st.header("Fluido", anchor=False)
            carga_vazao = st.number_input("Q [m³/h]", min_value=0.000001, step=0.01, format="%.2f")
            carga_vazao_str = (carga_vazao)
            carga_densidade = st.number_input("ρ [kg/m³]", min_value=0.000001, step=0.01, format="%.2f", value=999.0)
            carga_visosidade_ = st.number_input("μ [Cp]", min_value=0.00001, step=0.001, format="%.3f", value=1.01)
            carga_visosidade = carga_visosidade_ / 1000
            st.caption('1000[N.s/m²] = 1[CP]')
        with carga3:
            st.header("Tubo", anchor=False)
            tipo_tubo = st.selectbox("Tipo", materiais_lista, index=0)
            tipo_tubo_str = str(tipo_tubo)
            df_tubo_sel = df_tubos[df_tubos['Material'] == tipo_tubo_str]
            lista_bitola = df_tubo_sel['Bitola nominal'].unique().tolist()
            rugosidade = rugosidade_data[tipo_tubo_str]
            if tipo_tubo_str != "Outro":
                st.subheader("Rugosidade \n {} mm".format(rugosidade), anchor=False)

            if tipo_tubo_str == "Outro":
                rugosidade = st.number_input("e [mm]", min_value=0.000001, step=0.01, format="%.4f")
            st.info("Sucção < 1,5m/s \n"
                    "Recalque < 3.0m/s")

        with carga4:
            st.header("   Ø", anchor=False)
            diametro_tubo = st.selectbox("Diâmetro comercial", lista_bitola, index=0)
            diametro_tubo_str = str(diametro_tubo)
            if tipo_tubo_str == "Outro":
                diametro_int = st.number_input("Ø int [mm]", min_value=0.01, step=0.1, format="%.1f")
                diametro_int_str = float(diametro_int)
            if tipo_tubo_str != "Outro":
                diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (
                            df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
                diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
                st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
            velocidade = f_velocidade(diametro_int_str, carga_vazao_str)
            st.subheader("Velocidade \n {:.2f} m/s".format(velocidade), anchor=False)

        st.header("Acessórios", anchor=False)

        # inserção de acessórios

        # Inicializar o estado, se necessário
        if 'inputs' not in st.session_state:
            st.session_state['inputs'] = []


        # Função para adicionar um campo de entrada
        def add_input():
            st.session_state['inputs'].append({'Acessório': 'Cotovelo 90°, padrão', 'Quantidade': 1})


        # Função para remover um campo de entrada
        def remove_input(index):
            st.session_state['inputs'].pop(index)


        acessorios = list(perda_friccao_dict.keys())

        # Botão que, ao ser pressionado, aciona a função add_input
        st.button('Adicionar acessório', on_click=add_input)

        # Exibir os campos de entrada baseados no número armazenado no estado da sessão
        for i, value in enumerate(st.session_state['inputs']):
            # Forçar o valor a ser um dicionário, caso não seja
            if not isinstance(value, dict):
                st.session_state['inputs'][i] = {'Acessório': 'Cotovelo 45°, padrão', 'Quantidade': 1}

            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                current_acessorio = st.session_state['inputs'][i].get('Acessório', 'Cotovelo 45°, padrão')
                acessorio = st.selectbox("Acessório", acessorios, index=acessorios.index(current_acessorio),
                                         key=f'acessorio_{i}')
                st.session_state['inputs'][i]['Acessório'] = acessorio
            with col2:
                current_quantidade = st.session_state['inputs'][i].get('Quantidade', 1)
                quantidade = st.number_input("Quantidade", min_value=1, step=1, key=f'quantidade_{i}',
                                             value=current_quantidade)
                st.session_state['inputs'][i]['Quantidade'] = quantidade
            with col3:
                st.subheader("\n", anchor=False)
                st.button('Excluir', key=f'remove_{i}', on_click=remove_input, args=(i,))

        # Exibir o estado atual dos inputs para depuração

        df_acessorios_usados = pd.DataFrame(st.session_state['inputs'])
        tubo_dict = {'Acessório': 'Tubo', 'Quantidade': comprimento_tubulação, 'perda': 'PVC'}

        reynolds = f_reynolds(carga_densidade, carga_visosidade, velocidade, diametro_int_str)
        fator_atrito = f_colebrook(reynolds, diametro_int_str, rugosidade)

        # Verifique se o DataFrame não está vazio antes de tentar exibir
        if not df_acessorios_usados.empty:
            df_acessorios_usados["k"] = df_acessorios_usados["Acessório"].map(perda_friccao_dict)
            df_acessorios_usados["perda [m²/s²]"] = df_acessorios_usados["Quantidade"] * df_acessorios_usados["k"] * (
                        velocidade ** 2) / 2

            nova_linha = pd.DataFrame({'Acessório': "Tubo"}, index=[0])
            df_acessorios_usados = pd.concat([df_acessorios_usados, nova_linha], ignore_index=True)

        else:
            df_acessorios_usados["k"] = 0
            df_acessorios_usados["Quantidade"] = 0
            nova_linha = pd.DataFrame({'Acessório': "Tubo"}, index=[0])
            df_acessorios_usados = pd.concat([df_acessorios_usados, nova_linha], ignore_index=True)
        if not df_acessorios_usados.empty:
            somatorio_k = (df_acessorios_usados['k'] * df_acessorios_usados['Quantidade']).sum()
        else:
            somatorio_k = 0
        perda_total_tubo = float(
            calcular_perda_de_carga(fator_atrito, comprimento_tubulação, velocidade, diametro_int_str))
        indice_tubo = (df_acessorios_usados.index[df_acessorios_usados['Acessório'] == "Tubo"][0])
        df_acessorios_usados.loc[indice_tubo, "perda [m²/s²]"] = perda_total_tubo
        df_acessorios_usados.loc[indice_tubo, "Quantidade"] = comprimento_tubulação
        df_acessorios_usados.loc[indice_tubo, "k"] = 0
        perda_mcf = (df_acessorios_usados["perda [m²/s²]"].sum()) / 9.81
        perda_mcf = perda_mcf - altura_entrada + altura_saida
        # st.table(df_acessorios_usados)

        # st.subheader(indice_tubo, anchor=False)
        st.subheader("Reynolds {:.0f} ".format(reynolds), anchor=False)
        st.subheader("Perda de Carga {:.2f} [mcf]".format(perda_mcf), anchor=False)
        if perda_mcf < 0:
            st.subheader("Pressão positiva na saida!!!", anchor=False)
        st.subheader("Fator de atrito {:.4f} ".format(fator_atrito), anchor=False)
        # st.subheader("e/d {:.6f} ".format(rugosidade / diametro_int_str), anchor=False)

        resolucao = st.slider("Selecione a resolução do grafico", (int(2 * carga_vazao_str)), 1000, 100, 1)
        alcance = st.slider("Selecione o alcance no Grafico (x Vazão inicial)", 1, 100, 2, 1)

        vazao_indice = np.linspace((0.0001), (alcance * carga_vazao_str), num=resolucao)
        df_grafico_perda = pd.DataFrame({'Vazão': vazao_indice, })
        df_grafico_perda['Velocidade m/s'] = df_grafico_perda['Vazão'].apply(
            lambda x: f_velocidade(diametro_int_str, x))
        df_grafico_perda['k'] = None
        df_grafico_perda['Reynolds'] = None
        df_grafico_perda['Reynolds'] = df_grafico_perda["Velocidade m/s"].apply(
            lambda x: f_reynolds(carga_densidade, carga_visosidade, x, diametro_int_str))
        df_grafico_perda['f tubo'] = None
        df_grafico_perda['f tubo'] = df_grafico_perda["Reynolds"].apply(
            lambda x: f_colebrook(x, diametro_int_str, rugosidade))
        df_grafico_perda['k'] = df_grafico_perda['k'].map(lambda x: somatorio_k)
        df_grafico_perda['Perda tubo m²/s²'] = None
        df_grafico_perda['Perda tubo m²/s²'] = df_grafico_perda.apply(
            lambda row: calcular_perda_de_carga(row['f tubo'], comprimento_tubulação, row['Velocidade m/s'],
                                                diametro_int_str), axis=1)
        df_grafico_perda['Perda acess m²/s²'] = df_grafico_perda.apply(
            lambda row: perda_acessórios(row['k'], row['Velocidade m/s']), axis=1)
        calcular_perda_de_carga(fator_atrito, comprimento_tubulação, velocidade, diametro_int_str)
        df_grafico_perda['Perda total m²/s²'] = df_grafico_perda['Perda acess m²/s²'] + df_grafico_perda[
            'Perda tubo m²/s²']
        df_grafico_perda['Perda total mcf'] = (df_grafico_perda[
                                                   'Perda total m²/s²'] / 9.81) - altura_entrada + altura_saida

        opcao_grafico_x = st.selectbox("Eixo X", ["Vazão", "Reynolds", "Velocidade m/s"])
        opcao_grafico_y = st.multiselect("Eixo Y", ["Reynolds", "Perda total mcf", "Velocidade m/s"])
        # st.line_chart(df_grafico_perda, x=opcao_grafico_x,y=opcao_grafico_y)

        fig = px.line(df_grafico_perda, x=opcao_grafico_x, y=opcao_grafico_y,
                      labels={'Vazão': 'Vazão (m³/h)'
                          , "Velocidade": "m/s"})
        # Escondendo o título do eixo Y
        fig.update_yaxes(title_text='')
        st.plotly_chart(fig, use_container_width=True)

        # st.table(df_grafico_perda)
    if metodo_carga == "Sucção/NPSH disponível":

        dicionario_propriedades = [
            {'Viscosidade': 'VISCOSITY'},
            {'Densidade': 'D'},
            {'Entalpia': 'H'},
            {'Entropia': 'S'},
            {'Qualidade (fração mássica)': 'Q'},
            {'Energia interna': 'U'},
            {'Calor específico a pressão constante': 'C'},
            {'Velocidade do som': 'V'},
            {'Condutividade térmica': 'CONDUCTIVITY'}]
        lista_fluidos = prop.get_global_param_string("fluids_list").split(",")

        npsh1, npsh2, npsh3, npsh4 = st.columns([1, 1, 1, 2])
        with npsh1:
            dados_fluido = st.selectbox("Base de dados Fluido", ('Coolprop',"Outro"))
            if dados_fluido == 'Coolprop':
                fluido_npsh = st.selectbox("Fluido", lista_fluidos, index=93)
                temperatura_npsh = st.number_input("Temperatura [°C]", min_value=0.1, value=30.0, step=0.1, format="%.1f")
                press_rt = st.number_input("Pressão man[bar]", min_value=0.000, value=0.000, step=0.1, format="%.3f")
                press_rt = press_rt * 100000
            if dados_fluido == "Outro":
                p_vapor = st.number_input("P. de Vapor [Bar]", min_value=0.000001,step=0.1, format="%.4f")
                carga_densidade = st.number_input("ρ [kg/m³]", min_value=0.000001, step=0.01, format="%.1f",value=999.0)
                carga_visosidade_ = st.number_input("μ [Cp]", min_value=0.00001, step=0.001, format="%.3f", value=1.01)
                carga_visosidade_1 = carga_visosidade_ / 1000
                carga_densidade_1 = carga_densidade
                press_rt = st.number_input("Pressão man[bar]", min_value=0.000, value=0.000, step=0.1, format="%.3f")
                press_rt = press_rt * 100000
            vazao_npsh = st.number_input("Vazão [m³/h]", min_value=0.00000001, step=0.1, format="%.1f")

        with npsh2:
            tipo_tubo = st.selectbox("Tubo", materiais_lista, index=0)
            tipo_tubo_str = str(tipo_tubo)
            df_tubo_sel = df_tubos[df_tubos['Material'] == tipo_tubo_str]
            lista_bitola = df_tubo_sel['Bitola nominal'].unique().tolist()
            rugosidade = rugosidade_data[tipo_tubo_str]
            if tipo_tubo_str == "Outro":
                rugosidade = st.number_input("e [mm]", min_value=0.000001, step=0.01, format="%.4f")
            comprimento_tubulação = st.number_input("Tubulação [m]", min_value=0.0, step=0.1, format="%.1f")
            altura_entrada_npsh = st.number_input("Altura Sucção [m]", min_value=-1000.0, value=0.0, step=0.1,format="%.1f")
            margem_pv = st.number_input("Margem [Pv+%]", min_value=0.0,value=10.0,step=1.0, format="%.0f")
            margem_pv = (margem_pv/100) + 1
            if tipo_tubo_str != "Outro":
                st.subheader(" Rugosidade \n {} mm".format(rugosidade), anchor=False)

        with npsh3:
            diametro_tubo = st.selectbox("Diâmetro comercial", lista_bitola, index=0)
            diametro_tubo_str = str(diametro_tubo)
            if tipo_tubo_str == "Outro":
                diametro_int = st.number_input("   Ø int [mm]", min_value=0.01, step=0.1, format="%.1f")
                diametro_int_str = float(diametro_int)
            if tipo_tubo_str != "Outro":
                diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (
                        df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
                diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
                st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
            velocidade = f_velocidade(diametro_int_str, vazao_npsh)
            st.subheader("Velocidade \n {:.2f} m/s".format(velocidade), anchor=False)
            st.info("Sucção < 1,5m/s \n"
                    "Recalque < 3.0m/s")

        with npsh4:
            try:
                municipios_base = get_municipios()
                municipio = st.selectbox("Selecione o municipio", municipios_base['Município - Estado'])
            except Exception as e:
                municipios_base = "0"
                st.success("API IBGE Indisponível")
            # st.dataframe(municipios_base)
            try:
                df_altitude = get_altitude(municipio)
                min_altitude = int(df_altitude["Altitude Normal"].min())
                max_altitude = int(df_altitude["Altitude Normal"].max())
                med_altitude = int(df_altitude["Altitude Normal"].mean())
                # st.dataframe(df_altitude)
                # st.info("Min{}m | Med {}m | Max {}m".format(min_altitude,med_altitude,max_altitude))
            except Exception as e:
                min_altitude = -1
                max_altitude = "Vazio"
                med_altitude = 0
            if min_altitude == -1:
                altitude_npsh = st.number_input("Altitude (Sem dados IBGE)", min_value=0, value=0, step=1)
            else:
                altitude_npsh = st.number_input(
                    "Altitude Min {}m | Med {}m | Max {}m".format(min_altitude, med_altitude, max_altitude),
                    min_value=0, value=med_altitude, step=1, )
            abs_press = get_abspress(altitude_npsh, 101325)
            if dados_fluido == 'Coolprop':
                p_vapor = PropsSI('P', 'T', (temperatura_npsh + 273.15), 'Q', 1, fluido_npsh)
                p_vapor = p_vapor / (100000)
                p_final = abs_press + press_rt
                carga_densidade = prop.PropsSI('D', 'T', (temperatura_npsh + 273.15), 'P', p_final , fluido_npsh)
                carga_densidade_1 = carga_densidade
                carga_visosidade_1 = prop.PropsSI('VISCOSITY', 'T', (temperatura_npsh + 273.15), 'P', p_final,fluido_npsh)
            # st.title("Min {}".format(min_altitude), anchor=False)
            # st.title("Max {}".format(max_altitude), anchor=False)
            # st.title("Med {}".format(med_altitude), anchor=False)
            abs_bar = abs_press / (100000)
            abs_mcf = (abs_bar * 100000)/(9.81 * carga_densidade_1)
            bar_vapor = p_vapor * margem_pv
            st.subheader("Pressão Abs \n {:.3f} Bar Absoluto \n( {:.2f} mcf )".format(abs_bar, abs_mcf), anchor=False)
            st.subheader("Pressão vapor \n {:.3f} Bar absoluto".format(bar_vapor), anchor=False)
            st.subheader("Densidade \n {:.1f} kg/m³".format(carga_densidade_1), anchor=False)
            


        st.header("Acessórios", anchor=False)

        # inserção de acessórios

        # Inicializar o estado, se necessário
        if 'inputs' not in st.session_state:
            st.session_state['inputs'] = []


        # Função para adicionar um campo de entrada
        def add_input():
            st.session_state['inputs'].append({'Acessório': 'Cotovelo 90°, padrão', 'Quantidade': 1})


        # Função para remover um campo de entrada
        def remove_input(index):
            st.session_state['inputs'].pop(index)


        acessorios = list(perda_friccao_dict.keys())

        # Botão que, ao ser pressionado, aciona a função add_input
        st.button('Adicionar acessório', on_click=add_input)

        # Exibir os campos de entrada baseados no número armazenado no estado da sessão
        for i, value in enumerate(st.session_state['inputs']):
            # Forçar o valor a ser um dicionário, caso não seja
            if not isinstance(value, dict):
                st.session_state['inputs'][i] = {'Acessório': 'Cotovelo 45°, padrão', 'Quantidade': 1}

            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                current_acessorio = st.session_state['inputs'][i].get('Acessório', 'Cotovelo 45°, padrão')
                acessorio = st.selectbox("Acessório", acessorios, index=acessorios.index(current_acessorio),
                                         key=f'acessorio_{i}')
                st.session_state['inputs'][i]['Acessório'] = acessorio
            with col2:
                current_quantidade = st.session_state['inputs'][i].get('Quantidade', 1)
                quantidade = st.number_input("Quantidade", min_value=1, step=1, key=f'quantidade_{i}',
                                             value=current_quantidade)
                st.session_state['inputs'][i]['Quantidade'] = quantidade
            with col3:
                st.subheader("\n", anchor=False)
                st.button('Excluir', key=f'remove_{i}', on_click=remove_input, args=(i,))

        if dados_fluido == 'Coolprop':
            pass
            #carga_densidade = prop.PropsSI('D', 'T', (temperatura_npsh + 273.15), 'P', abs_press, fluido_npsh)
            #carga_visosidade = prop.PropsSI('VISCOSITY', 'T', (temperatura_npsh + 273.15), 'P', abs_press, fluido_npsh)
        df_acessorios_usados = pd.DataFrame(st.session_state['inputs'])
        tubo_dict = {'Acessório': 'Tubo', 'Quantidade': comprimento_tubulação, 'perda': 'PVC'}

        reynolds = f_reynolds(carga_densidade_1, carga_visosidade_1, velocidade, diametro_int_str)
        fator_atrito = f_colebrook(reynolds, diametro_int_str, rugosidade)

        # Verifique se o DataFrame não está vazio antes de tentar exibir
        if not df_acessorios_usados.empty:
            df_acessorios_usados["k"] = df_acessorios_usados["Acessório"].map(perda_friccao_dict)
            df_acessorios_usados["perda [m²/s²]"] = df_acessorios_usados["Quantidade"] * df_acessorios_usados["k"] * (
                    velocidade ** 2) / 2

            nova_linha = pd.DataFrame({'Acessório': "Tubo"}, index=[0])
            df_acessorios_usados = pd.concat([df_acessorios_usados, nova_linha], ignore_index=True)

        else:
            df_acessorios_usados["k"] = 0
            df_acessorios_usados["Quantidade"] = 0
            nova_linha = pd.DataFrame({'Acessório': "Tubo"}, index=[0])
            df_acessorios_usados = pd.concat([df_acessorios_usados, nova_linha], ignore_index=True)
        if not df_acessorios_usados.empty:
            somatorio_k = (df_acessorios_usados['k'] * df_acessorios_usados['Quantidade']).sum()
        else:
            somatorio_k = 0
        perda_total_tubo = float(
            calcular_perda_de_carga(fator_atrito, comprimento_tubulação, velocidade, diametro_int_str))
        indice_tubo = (df_acessorios_usados.index[df_acessorios_usados['Acessório'] == "Tubo"][0])
        df_acessorios_usados.loc[indice_tubo, "perda [m²/s²]"] = perda_total_tubo
        df_acessorios_usados.loc[indice_tubo, "Quantidade"] = comprimento_tubulação
        df_acessorios_usados.loc[indice_tubo, "k"] = 0
        perda_mcf = (df_acessorios_usados["perda [m²/s²]"].sum()) / 9.81

        perda_bar = (df_acessorios_usados["perda [m²/s²]"].sum()) * carga_densidade_1 / 100000
        # st.table(df_acessorios_usados)
        dinamica_bar = (carga_densidade_1 * (velocidade * velocidade) )/ (2 * 100000)
        npsh_disponivel_bar = abs_bar - bar_vapor - perda_bar + dinamica_bar + ((press_rt/100000) +
        (altura_entrada_npsh * 9.81 * carga_densidade_1 / 100000))
        npsh_disponivel_mcf = (npsh_disponivel_bar * 100000)/(9.81 * carga_densidade_1)
        st.subheader("NPSH = Pabs + Pdin + Palt - Perda carga - Pvapor",anchor=False)
        st.subheader("NPSH=({:.3f})+({:.3f})+({:.3f})-({:.3f})-({:.3f})".format(abs_bar,dinamica_bar,(((press_rt/100000))+altura_entrada_npsh * 9.81 * carga_densidade_1/100000) ,perda_bar,bar_vapor),
                     anchor=False)
        st.subheader("NPSH disponivel {:.2f} Bar ({:.1f}) mcf".format(npsh_disponivel_bar, npsh_disponivel_mcf), anchor=False)

        resolucao = st.slider("Selecione a resolução do grafico", (int(2 * vazao_npsh)), 1000, 100, 1)
        alcance = st.slider("Selecione o alcance no Grafico (x Vazão inicial)", 1, 100, 2, 1)

        vazao_indice = np.linspace((0.0001), (alcance * vazao_npsh), num=resolucao)
        df_grafico_perda = pd.DataFrame({'Vazão': vazao_indice, })
        df_grafico_perda['Velocidade m/s'] = df_grafico_perda['Vazão'].apply(
            lambda x: f_velocidade(diametro_int_str, x))
        df_grafico_perda['k'] = None
        df_grafico_perda['Reynolds'] = None
        df_grafico_perda['Reynolds'] = df_grafico_perda["Velocidade m/s"].apply(
            lambda x: f_reynolds(carga_densidade_1, carga_visosidade_1, x, diametro_int_str))
        df_grafico_perda['f tubo'] = None
        df_grafico_perda['f tubo'] = df_grafico_perda["Reynolds"].apply(
            lambda x: f_colebrook(x, diametro_int_str, rugosidade))
        df_grafico_perda['k'] = df_grafico_perda['k'].map(lambda x: somatorio_k)
        df_grafico_perda['Perda tubo m²/s²'] = None
        df_grafico_perda['Perda tubo m²/s²'] = df_grafico_perda.apply(
            lambda row: calcular_perda_de_carga(row['f tubo'], comprimento_tubulação, row['Velocidade m/s'],diametro_int_str), axis=1)
        df_grafico_perda['Perda acess m²/s²'] = df_grafico_perda.apply(
            lambda row: perda_acessórios(row['k'], row['Velocidade m/s']), axis=1)
        calcular_perda_de_carga(fator_atrito, comprimento_tubulação, velocidade, diametro_int_str)
        df_grafico_perda['Perda total m²/s²'] = df_grafico_perda['Perda acess m²/s²'] + df_grafico_perda['Perda tubo m²/s²']
        df_grafico_perda['Perda carga bar'] = (df_grafico_perda['Perda total m²/s²'] * carga_densidade_1) / 100000
        df_grafico_perda['ABS bar'] = abs_bar
        df_grafico_perda['Pv bar'] = bar_vapor
        df_grafico_perda['P Altura bar'] = altura_entrada_npsh * 9.81 * carga_densidade / 100000
        df_grafico_perda['P dinamica bar'] = carga_densidade_1 * (df_grafico_perda['Velocidade m/s'] ** 2) / (2 * 100000)
        df_grafico_perda['NPSH Disp. bar'] = df_grafico_perda['ABS bar'] + df_grafico_perda['P Altura bar'] + df_grafico_perda['P dinamica bar'] - df_grafico_perda['Perda carga bar'] - df_grafico_perda['Pv bar']

        #st.table(df_grafico_perda)
        opcao_grafico_x = st.selectbox("Eixo X", ["Vazão", "Velocidade m/s"])
        opcao_grafico_y = st.multiselect("Eixo Y", ['NPSH Disp. bar',"Perda carga bar",'P dinamica bar', "Velocidade m/s"])
        # st.line_chart(df_grafico_perda, x=opcao_grafico_x,y=opcao_grafico_y)

        fig = px.line(df_grafico_perda, x=opcao_grafico_x, y=opcao_grafico_y,
                      labels={'Vazão': 'Vazão (m³/h)'
                          , "Velocidade": "m/s"})
        # Escondendo o título do eixo Y
        fig.update_yaxes(title_text='Bar')
        st.plotly_chart(fig, use_container_width=True)

#------------------------------------------------------------------------------------------------------------------------------

if applicativo == "Final":
    arqivo_css = 'https://github.com/JoaoJuniorGrb/app/blob/4ef7f6d97028d111ca7ddc34ff1a2e6c6e9b0a3f/propriedades/styles/main.css'
    arqivo_pdf = 'https://github.com/JoaoJuniorGrb/app/blob/4ef7f6d97028d111ca7ddc34ff1a2e6c6e9b0a3f/propriedades/assets/Curriculo.pdf'
    arqivo_img = 'https://github.com/JoaoJuniorGrb/appestreamlit/blob/624cf41fb2c6bc7152359344c6d0b29f264228e1/Foto_.jpg?raw=true'
    titulo = "Curriculum | João Ferreira Junior"
    nome = "João Hering Ferreira"
    descrição = "Engenheiro de Energia, Pós graduação em Automação e controle de processos Conhecimento em Python e microcontroladores"
    st.title('Desenvolvido por',nome)
    # Fazer o download da imagem
    response = requests.get(arqivo_img)
    if response.status_code == 200:
        # Abrir a imagem a partir do conteúdo binário
        img = Image.open(BytesIO(response.content))

    email = "joaojunior.grb@hotmail.com"
    midia_social = {"LinkedIn": "https://www.linkedin.com/in/jo%C3%A3o-ferreira-junior-b2698163/?lipi=urn%3Ali%3Apage%3Ad_flagship3_feed%3BAjwOn5KcRhmkdM6UuXiVjw%3D%3D"}

    projetos = {":toolbox: Ferramenta 1": "ferramenta 1",
                ":toolbox: Ferramenta 2": "ferramenta 2",
                ":toolbox: Ferramenta 3": "ferramenta 2"}

    col1, col2 = st.columns(2, gap="small")

    with col1:
        st.image(img,width=250)

    with col2:
        st.title(nome,anchor=False)
        st.write(descrição,anchor=False)
        st.write(":email:", email)

    # midias sosiais
    st.write("#")
    colunas = st.columns(len(midia_social))
    for indice, (plataforma, link) in enumerate(midia_social.items()):
        colunas[indice].write(f"[{plataforma}]({link})")
    # experiencias
    st.write("#")
    st.subheader("Experiências",anchor=False)
    st.write(""":white_check_mark: Fiedler Automação industrial""", anchor=False)
    st.write(""" 	:white_check_mark: Termosul engenharia e aquecimento """,
        anchor = False
    )


#------------------------------------------------------------------------------------------------------------------------------

if applicativo == "Base Instalada":
    # Especifica o caminho do arquivo no bucket, sem o prefixo "gs://"
    file_path_isolutions = "isolutions/levantamento grundfos hidros_1.4"
    file_path_cargil = "levantamento cargil/resultado_final_cargil.json"
    resultado_final = load_(file_path_cargil).decode('utf-8')
    isolutions = load_(file_path_isolutions).decode('utf-8')

    if authentication_status:
        
        nome= name
        st.markdown(
            f"""
            <h1 style="text-align: left;">
                Bem-vindo, {nome}
            </h1>
            """,
            unsafe_allow_html=True)
        # Divisor personalizado com degradê de amarelo para azul
        st.markdown("""
        <hr style="border: 0; height: 16px; background: linear-gradient(to left, blue,blue,blue,blue,blue,yellow,yellow,blue);">
        """, unsafe_allow_html=True)

        df_original = pd.read_json(resultado_final)
        df_isoltutions = pd.read_json(isolutions)
        #st.dataframe(df_original)

        levantamento = st.selectbox('Levantamento', ('Base instalada Cargil', 'Isolutions Grundfos'))
        
#-----------------------------------------------------------dashboard------------------------------------------------

        if levantamento == 'Base instalada Cargil':        
            dashboard = st.selectbox('Pesquisa',('Geral','Tag'))
            df_original['PN'] = df_original['PN'].astype(str)
            df_original["arquivo"] = df_original["arquivo"].astype(str)
            df_bombas = df_original[df_original["PN"].str[-3:] == df_original["arquivo"].str[-3:]]
            df_peças = df_original[df_original["PN"].str[-3:] != df_original["arquivo"].str[-3:]]
            df_peças['PN'] = df_peças['PN'].astype(str)
            df_peças = df_peças['PN'].value_counts().reset_index()
            df_peças.columns = ['PN', 'Quantidade']
            df_peças = df_peças.sort_values(by='Quantidade', ascending=False).reset_index(drop=True)
            df_peças = pd.merge(df_peças,df_original[['PN','Description','Descrição','arquivo','TAG']] )
            df_peças = df_peças[['Descrição','Description', 'PN', 'Quantidade']]
            df_peças['Descrição'] = df_peças['Descrição'].astype(str)
            df_peças['Description'] = df_peças['Description'].astype(str)
            df_peças['PN'] = "(" + df_peças['PN'].astype(str) + ")"
            df_peças['DescriçãoPN'] = df_peças['Description'] + " " + df_peças['PN'].astype(str)
            df_peças['Quantidade'] = df_peças['Quantidade'].astype(float)
            df_peças = df_peças.drop_duplicates(subset=['PN'])
            lista_peças = df_peças['Description'].unique()
            df_peças_filtrado = df_peças
            tags = df_original['TAG'].unique()
    
            #st.subheader('bombas')
            #st.dataframe(df_original)
            # Configura a página para o modo widescreen
         
            if dashboard == 'Geral':
                #st.set_page_config(layout="wide")
                pecas_pesquisa = st.multiselect("Itens da pesquisa:", lista_peças, ['MECHANICAL SEAL', 'BEARING CARRIER', 'HOLDER BEARING', 'SPRING BEARING', 'HOUSING BEARING', 'BEARING', 'BEARING HOUSE', 'SHAFT', 'SHAFT SLEEVE', 'IMPELLER', 'IMPROSEAL', 'GASKET'])
                df_peças_filtrado = df_peças_filtrado[df_peças_filtrado['Description'].isin(pecas_pesquisa)]
                st.subheader('peças',anchor=False)
                dsh1, dsh2 = st.columns([0.2,0.3], gap='small')
                with dsh1:
                        st.dataframe(df_peças_filtrado)
    
    
                # Criar gráfico básico com Plotly Express
                with dsh2:
                        bar_pecas = px.bar(df_peças_filtrado,y='Quantidade' , x='DescriçãoPN',)
                        #st.bar_chart(df_peças, x="Quantidade", y="PN", horizontal=False)
                        st.plotly_chart(bar_pecas)
    
            if dashboard == 'Tag':
                st.subheader('Tags',anchor=False)
                tags_pesquisa = st.multiselect("Tags da pesquisa:",tags)
                df_tags_filtrado = df_original[df_original['TAG'].isin(tags_pesquisa)]
                pecas_pesquisa_tag = st.multiselect("Peças para Tag selecionada", lista_peças,lista_peças)
                df_tags_filtrado = df_tags_filtrado[df_tags_filtrado['Description'].isin(pecas_pesquisa_tag)]
                st.dataframe(df_tags_filtrado,use_container_width=True)
        
        
        if levantamento == 'Isolutions Grundfos':
            df_isoltutions['POT KW UNIT VALOR'] = df_isoltutions['POT KW UNIT'].astype(float).round(2)
            df_isoltutions['POT KW UNIT'] = df_isoltutions['POT KW UNIT'].astype(float).round(1)
            df_isoltutions['POT TOTAL BOMBAS'] = df_isoltutions['POT TOTAL BOMBAS'].astype(float).round(1)
            isol1, isol2 = st.columns(2)
            inversores_marca_isolutions = sorted(df_isoltutions['MARCA'].unique())
            inversores_ano_isolutions = sorted(df_isoltutions['Ano'].unique())
            inversores_pot_isolutions = sorted(df_isoltutions['POT KW UNIT'].unique())
            with isol1:
                marca_isolutions = st.multiselect('Marcas', inversores_marca_isolutions, inversores_marca_isolutions)
                inicio_ano, final_ano = st.select_slider('Período',
                                                         options=['2017', '2018', '2019', '2020', '2021', '2022',
                                                                  '2023', '2024'], value=('2017', '2024'))

            with isol2:
                df_modelo = df_isoltutions[df_isoltutions['MARCA'].isin(marca_isolutions)]
                modelos = df_modelo["MODELO"].unique()
                pot = df_modelo["POT KW UNIT"].unique()
                pot_isolutions = st.multiselect('Potencia',pot,pot)
                modelo_isulutions = st.multiselect('Modelo',modelos,modelos)
            df_isoltutions_filtrado = df_isoltutions[df_isoltutions['MARCA'].isin(marca_isolutions) & df_isoltutions['POT KW UNIT'].isin(pot_isolutions) & df_isoltutions['MODELO'].isin(modelo_isulutions)]
            df_isoltutions_filtrado['Ano'] = df_isoltutions_filtrado['Ano'].astype(int)
            df_isoltutions_filtrado = df_isoltutions_filtrado[(df_isoltutions_filtrado['Ano'] >=int(inicio_ano)) & (df_isoltutions_filtrado['Ano'] <= int(final_ano))]
            # Criar uma nova coluna com o produto de 'QTD SKID' e 'QTD INV'
            df_isoltutions_filtrado['QTD TOTAL'] = df_isoltutions_filtrado['QTD SKID'] * df_isoltutions_filtrado['QTD INV']
            #grafico_inversores = px.bar(df_isoltutions_filtrado['QTD INV']*df_isoltutions_filtrado['MODELO'].counts, y='Quantidade', x=pot)

            # Criar uma nova coluna com a contagem de modelos multiplicada pela quantidade de inversores
            df_grafico_inv = df_isoltutions_filtrado.groupby(['MODELO', 'POT KW UNIT','POT KW UNIT VALOR']).agg({'QTD TOTAL': 'sum'}).reset_index()
            df_grafico_inv['POT KW UNIT'] = df_grafico_inv['POT KW UNIT'].astype(str) + "kW"
            
            df_grafico_inv = df_grafico_inv.sort_values(by='POT KW UNIT VALOR', ascending=True)
            #st.dataframe(df_grafico_inv)

            

            # Gerar o gráfico com Plotly Express
            color_map = {
                "-": "white",  # Categoria "-" com cor branca
                "MGE": "blue",  # MGE com azul escuro
                "MGE FAI": "blue",  # MGE com azul escuro
                "CUE": "blue",  # CUE com azul escuro
                "V20": "gray",  # V20 com cinza
                "G120X": "gray",  # G120X com cinza
                "POWERFLEX": "orange",  # Powerflex com laranja
                "CFW":"yellow",
                "FC-51":"red"
            }
            # Gerar o gráfico com Plotly Express, configurando explicitamente as cores e o eixo X categorizado
            grafico_inversores = px.bar(df_grafico_inv,
                                        x='POT KW UNIT',  # Eixo X com a potência categorizada
                                        y='QTD TOTAL',  # Eixo Y com a quantidade de inversores
                                        color='MODELO',  # Usar a coluna 'MODELO' para aplicar o mapeamento de cores
                                        title='Quantidade de Inversores ',
                                        color_discrete_map=color_map,  # Aplicar o mapeamento de cores
                                        
            )
            
            
         
            color_ = {
                "-": "white",  # Categoria "-" com cor branca
                "Grundfos": "blue",  # MGE com azul escuro
                "Siemens": "gray",  # V20 com cinza
                "ROCKWELL": "orange",  # Powerflex com laranja
                "WEG":"yellow",
                "DANFOSS":"red"
            }
            df_inversores_ano = df_isoltutions_filtrado.groupby(['MARCA','Ano']).agg({'QTD TOTAL':'sum'}).reset_index()
            #st.dataframe(df_inversores_ano)
            inversores_ano = px.bar(df_inversores_ano, x="Ano", y="QTD TOTAL", color='MARCA', title='Unidades Vendidas por marca', color_discrete_map = color_)
            

            isol3, isol4 = st.columns(2)

            with isol3:
                st.plotly_chart(grafico_inversores, use_container_width=True)
            with isol4:
                st.plotly_chart(inversores_ano, use_container_width=True)
            st.dataframe(df_isoltutions_filtrado)

    elif authentication_status == False:
        st.error('Nome de usuário ou senha incorretos')
    elif authentication_status == None:
        st.warning('Por favor, insira suas credenciais')

#-----------------------------------------------------ordem de venda--------------------------------------------------------------
if applicativo == "Localização de Pedidos":
    

    # Define o fuso horário de Brasília
    fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")
    # Obtém a data e hora atuais no fuso horário de Brasília
    data_atual = datetime.now(fuso_horario_brasilia)


    # Função para enviar dados para o Firebase RTDB
    def enviar_rtdb(referencia_1,referencia_2,data,endereco,hora,nome):
        try:
            # Constrói o caminho dinâmico para o Firebase RTDB
            ref = db.reference(f"{referencia_1}/{referencia_2}")

            # Dados a serem enviados
            dados = {
                "data": str(data),
                "endereco": str(endereco),
                "hora": str(hora),
                "nome": str(nome),
            }

            # Envia os dados para o Firebase
            ref.set(dados)

            return True  # Retorna True se a operação foi bem-sucedida

        except Exception as e:
            return False

    def consulta_rtdb (referencia):
        try:
            # Constrói o caminho dinâmico para o Firebase RTDB
            ref = db.reference(referencia)
            dados_estoque = ref.get()
            return (True,dados_estoque)

        except Exception as e:
            return (False, "vazio")

    nome = name
    # URL da imagem


    # Exibir a imagem

    st.markdown(
        f"""
               <h1 style="text-align: left;">
                   Bem-vindo, {nome}
               </h1>
               """,
        unsafe_allow_html=True
    )

    # Divisor personalizado com degradê de amarelo para azul
    st.markdown("""
           <hr style="border: 0; height: 16px; background: linear-gradient(to left, blue,blue,blue,blue,blue,yellow,yellow,blue);">
           """, unsafe_allow_html=True)

    estoque_col_1,estoque_col_2 = st.columns([0.2,0.8])

    with estoque_col_1:
        status = False
        # Inicialize o estado dos campos de texto se ainda não estiverem definidos
        if "ov_estoque" not in st.session_state:
            st.session_state.ov_estoque = ""
        if "endereco_estoque" not in st.session_state:
            st.session_state.endereco_estoque = ""
        # Função para limpar o conteúdo dos campos ao focar
        def clear_text(field_name):
            st.session_state[field_name] = ""

        ov_estoque =  st.text_input("OV",placeholder="Insira a ordem de venda")
        endereco_estoque =  st.text_input("Localização",placeholder="Insira o endereço")
        registrar = st.button("Registrar",type="secondary",use_container_width=True)
        if registrar:
            data = str(data_atual.strftime("%d/%m/%Y")) # Formato: dd/mm/aaaa)
            hora = str(data_atual.strftime("%H:%M"))
            status = enviar_rtdb("estoque",ov_estoque, data, endereco_estoque, hora, nome)
            if status:
                st.success(f"OV:{ov_estoque} ({hora}-{data})",icon="✅")

            if not status:
                st.success(f"{ov_estoque} falha!")
    with estoque_col_2:
        df_stoque_status,dc_estoque  = consulta_rtdb ("estoque")
        df_estoque = pd.DataFrame.from_dict(dc_estoque,orient="index").reset_index()
        df_estoque.rename(columns={"index": "OV"},inplace=True)
        df_estoque = df_estoque[["OV", "endereco", "hora", "data", "nome"]]

        # Verifica se há atualizações a cada intervalo (por exemplo, 5 segundos)
        st_autorefresh(interval=5000, limit=None, key="firebase_update")
        st.dataframe(df_estoque,use_container_width=True)
if applicativo == "Sistemas de controle":
    metodo_controle = st.selectbox("Metodo",["Classico","Espaço de estados"])
    if metodo_controle == "Classico":
        # Adiciona CSS para centralizar a imagem
        st.markdown(
            """
            <style>
            .centered-image {
                display: block;
                margin-left: auto;
                margin-right: auto;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Exibe a imagem com a classe CSS para centralizar
        st.image(
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_QT6rPDPR6BIvrmQE1p6QgZOCxRN1tA6qrw&s",
            caption="Diagrama de blocos referência",
            use_column_width=True,
            output_format="auto"
        )
        clas_contr_1,clas_contr_2,clas_contr_3,clas_contr_4 = st.columns([0.5,0.6,0.5,0.6])

        with clas_contr_1:
            numerador_G = st.text_input("Numerador do sistema G(s)", "1", key="numerador_G")
            denominador_G = st.text_input("Denominador do sistema G(s)", "1,1,1", key="denominador_G")
            # Conversão dos inputs de texto para listas numéricas
            numerador_g = list(map(float, numerador_G.split(",")))
            denominador_g = list(map(float, denominador_G.split(",")))
            realimentacao = st.checkbox("Realimentado")
        with clas_contr_2:
            if realimentacao:
                    numerador_L = st.text_input("Numerador da realimentação L(s)", "1", key="numerador_L")
                    denominador_L = st.text_input("Denominador da realimentação L(s)", "1", key="denominador_L")
                    # Conversão dos inputs de texto para listas numéricas
                    numerador_l = list(map(float, numerador_L.split(",")))
                    denominador_l = list(map(float, denominador_L.split(",")))
            if not realimentacao:
                    numerador_C = st.text_input("Numerador controlador C(s) ", "1", key="numerador_C")
                    denominador_C = st.text_input("Denominador controlador C(s) ", "1", key="denominador_C")
                    # Conversão dos inputs de texto para listas numéricas
                    numerador_c = list(map(float, numerador_C.split(",")))
                    denominador_c = list(map(float, denominador_C.split(",")))
            sinal_entrada = st.selectbox("Sinal de Entrada", ["Degrau","Rampa","Senoide"])

        with clas_contr_3:
            if realimentacao:
                numerador_C = st.text_input("Numerador controlador C(s) ", "1")
                denominador_C = st.text_input("Denominador controlador C(s) ", "1")
                # Conversão dos inputs de texto para listas numéricas
                numerador_c = list(map(float, numerador_C.split(",")))
                denominador_c = list(map(float, denominador_C.split(",")))
                limite = st.number_input("Limite simulação",min_value=1,value=600)
                
            if not realimentacao:
                limite = st.number_input("Limite simulação",min_value=1,value=600)

        with clas_contr_4:
            tempo_simulacao =(st.slider("Tempo de simulação (segundos)",min_value=1,step=1, max_value=limite))
            resolucao_simulacao =(st.slider("Resolução (pontos)",min_value=10,step=1, max_value=100000))

        # Definição das funções de transferência
        g_func = ctrl.tf(numerador_g, denominador_g)

        if realimentacao:
            l_func = ctrl.tf(numerador_l, denominador_l)
            c_func = ctrl.tf(numerador_c, denominador_c)
            malha_aberta = c_func * g_func
            sistema_final = ctrl.feedback(malha_aberta, l_func)
        else:
            c_func = ctrl.tf(numerador_c, denominador_c)
            malha_aberta = c_func * g_func
            sistema_final = malha_aberta

        # Definição do tempo de simulação como um array de numpy
        tempo = np.linspace(0, tempo_simulacao, resolucao_simulacao)

        # Geração do sinal de entrada
        if sinal_entrada == "Degrau":
            u = np.ones_like(tempo)  # Degrau unitário
        elif sinal_entrada == "Rampa":
            u = tempo  # Sinal de rampa
        elif sinal_entrada == "Senoide":
            u = np.sin(2 * np.pi * 0.5 * tempo)  # Sinal senoidal de frequência 0.5 Hz

        # Simulação da resposta do sistema ao sinal de entrada
        tempo, resposta = ctrl.forced_response(sistema_final, T=tempo, U=u)

        # Criação do gráfico com Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tempo, y=resposta, mode='lines', name='Resposta do Sistema'))
        fig.add_trace(go.Scatter(x=tempo, y=u, mode='lines', name='Sinal de Entrada', line=dict(dash='dash')))
        fig.update_layout(
            title=f'Resposta do Sistema ao Sinal de Entrada ({sinal_entrada})',
            xaxis_title='Tempo (s)',
            yaxis_title='Amplitude'
        )

        # Exibição do gráfico no Streamlit
        st.plotly_chart(fig)

if applicativo == 'Equações de afinidade':
    from scipy.interpolate import interp1d
    # Exibe a imagem com a classe CSS para centralizar
    st.warning('Este recuro utiliza as relações de afinidade para EXTRAPOLAÇÃO de grandezas, esta relaçoes teoricas não refletem com precisao o comportamento real de operaçao de motobombas', icon="⚠️")
    afin_1, afin_2, afin_3 = st.columns(3)

    with afin_1:
        st.header("Vazão")
        st.image("https://omel.com.br/wp-content/uploads/2024/02/leis-de-afinidade-01-jpg.webp",caption="D diametro rotor / N RPM",
                use_column_width=True,
                output_format="auto")
        relacao_b1 = st.number_input("Rotação N1 | Rotor D1", min_value=1, max_value=5000)
        relacao_b2 = st.slider("Rotação N2 | Rotor D2", min_value=1, max_value=5000)
        vazao_nova = st.number_input('Nova vazão',min_value = 0.1)
        pressao_nova = st.number_input('Nova Pressão',min_value = 0.1)
        linha_bomba = st.number_input("Pontos", min_value=3)
        relacao_n = (relacao_b2/relacao_b1) 

    with afin_2:
        st.header("Altura man.")
        st.image("https://omel.com.br/wp-content/uploads/2024/02/leis-de-afinidade-02-jpg.webp",
                caption="D diametro rotor / N RPM",
                use_column_width=True,
                output_format="auto")
        
        data = {'Altura B1': [0.0]*linha_bomba, 'Vazão B1': [0.0]*linha_bomba,'Potencia B1': [0.0]*linha_bomba}
        df_pontos_de_trabalho = pd.DataFrame(data)
        edited_df = st.data_editor(df_pontos_de_trabalho,hide_index=True, use_container_width=True)
    with afin_3:
        st.header("Potencia")
        st.image(
                "https://omel.com.br/wp-content/uploads/2024/02/leis-de-afinidade-03-jpg.webp",
                caption="D diametro rotor / N RPM",
                use_column_width=True,
                output_format="auto")
        df_bomba_nova  = edited_df
        df_bomba_nova["Altura B2"] = df_bomba_nova["Altura B1"]*relacao_n**2
        df_bomba_nova["Vazão B2"] = df_bomba_nova["Vazão B1"]*relacao_n
        df_bomba_nova["Potencia B2"] = df_bomba_nova["Potencia B1"]*relacao_n**3
        st.dataframe(df_bomba_nova[["Vazão B2","Altura B2","Potencia B2"]], hide_index=True, use_container_width=True)
        
    if not df_bomba_nova.eq(0).all().all():
        # Interpolação para Altura B2
        altura_b2_interp = interp1d(df_bomba_nova["Vazão B2"], df_bomba_nova["Altura B2"], kind="quadratic", fill_value="extrapolate")
        # Interpolação para Potência B2
        potencia_b2_interp = interp1d(df_bomba_nova["Vazão B2"], df_bomba_nova["Potencia B2"], kind="quadratic", fill_value="extrapolate")

        # Criar novos pontos de Vazão (mais densos)
        vazao_b2_dense = np.linspace(df_bomba_nova["Vazão B2"].min(), df_bomba_nova["Vazão B2"].max(), 100)

        # Gerar os valores interpolados
        altura_b2_dense = altura_b2_interp(vazao_b2_dense)
        potencia_b2_dense = potencia_b2_interp(vazao_b2_dense)

        # Criar DataFrame com os dados interpolados para exibição ou gráfico
        df_bomba_interp = pd.DataFrame({
            "Vazão B2": vazao_b2_dense,
            "Altura B2": altura_b2_dense,
            "Potencia B2": potencia_b2_dense,
        })

        
        curva_bomba = px.line(df_bomba_interp, x="Vazão B2", y="Altura B2")
        # Adicionar a segunda linha 
        curva_bomba.add_trace(go.Scatter(x=df_bomba_nova['Vazão B1'], y=df_bomba_nova['Altura B1'], mode='lines', name='B1'))
        curva_bomba.update_layout(xaxis_title='Vazão',yaxis_title='Altura manometrica')
        curva_bomba.add_trace(go.Scatter(x=[vazao_nova], y=[pressao_nova], mode='markers', marker=dict(size=10, color='red'), name='Operação'))
        curva_potencia = px.line(df_bomba_interp, x="Potencia B2", y="Altura B2")


        st.plotly_chart(curva_bomba, use_container_width=True,key="curva")
        st.plotly_chart(curva_potencia, use_container_width=True,curva="potencia")

if applicativo == 'Gestão de projetos':
        # Divisor personalizado com degradê de amarelo para azul
        nome= name
        st.markdown(
            f"""
            <h1 style="text-align: left;">
                Gestão de projetos, Bem vindo {nome}!
            </h1>
            """,
            unsafe_allow_html=True)
            # Divisor personalizado com degradê de amarelo para azul
        st.markdown("""
            <hr style="border: 0; height: 16px; background: linear-gradient(to left, blue,blue,blue,blue,blue,yellow,yellow,blue);">
            """, unsafe_allow_html=True)
        # Define o fuso horário de Brasília
        fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")
        # Obtém a data e hora atuais no fuso horário de Brasília
        data_atual = datetime.now(fuso_horario_brasilia)
         # Função para enviar dados para o Firebase RTDB
        
        def enviar_rtdb(referencia_1,referencia_2,data_i,data_m,data_agend,pendente,realizado,status,cliente,nome):
            try:
                # Constrói o caminho dinâmico para o Firebase RTDB
                ref = db.reference(f"{referencia_1}/{referencia_2}")

                # Dados a serem enviados
                dados = {
                    "data inicio": data_i,
                    "data mod": data_m,
                    "data agenda": data_agend,
                    "cliente":str(cliente),
                    "nome": str(nome),
                    "status": status,
                    "realizado":str(realizado),
                    "pendente":str(pendente)
                }

                # Envia os dados para o Firebase
                ref.set(dados)

                return True  # Retorna True se a operação foi bem-sucedida

            except Exception as e:
                return False


        def consulta_rtdb (referencia):
            try:
                # Constrói o caminho dinâmico para o Firebase RTDB
                ref = db.reference(referencia)
                dados_projetos = ref.get()
                return (True,dados_projetos)

            except Exception as e:
                return (False, "vazio")
        
        estoque_col_1,estoque_col_2 = st.columns([0.2,0.8])

        with estoque_col_1:
            status = False
            
            # Inicializa o estado dos campos de texto se ainda não estiverem definidos
            if "fai_numero" not in st.session_state:
                st.session_state.fai_numero = ""  # Inicializa a chave no session_state
            if "fai_cliente" not in st.session_state:
                st.session_state.fai_cliente = ""  # Inicializa a chave no session_state

            fai_numero =  st.text_input("Novo projeto",placeholder="FAI",key="fai_numero")
            fai_cliente =  st.text_input("Cliente",placeholder="Cliente-Un-UF ",key="fai_cliente")

            if not fai_numero or not fai_cliente:
                st.warning("Por favor, preencha todos os campos!")
                registrar = False
            else:
                registrar = st.button("Registrar",type="secondary",use_container_width=True)
                               
            
            if registrar:
                with st.spinner("Atualizando dados..."):
                    time.sleep(1)
                data_inicio = data_atual.timestamp()
                data_mod = data_atual.timestamp()
                data_agend = data_atual.timestamp()
                #(referencia_1,referencia_2,data_i,data_m,pendente,realizado,status,cliente,nome)
                status_fai = False
                status = enviar_rtdb("projetos",fai_numero,data_inicio,data_mod,data_agend," "," ",status_fai,fai_cliente,nome)
                if status:
                    st.success(f"Registrado:{fai_numero} ({data_atual.strftime('%d-%m-%Y %H:%M')})",icon="✅")
                    st_autorefresh(interval=1000,limit=1)             
                if not status:
                    st.success(f"{fai_numero} falha!")
                
                
        with estoque_col_2:
            pass
        concluidos_fai = st.checkbox("Concluidos",value=False)
        atualizar_base = st.button("Salvar alterações",type="secondary",use_container_width=True)
        df_projeto_status,dc_projetos  = consulta_rtdb ("projetos")
        #st.dataframe(dc_projetos,use_container_width=True)
        df_projetos = pd.DataFrame.from_dict(dc_projetos,orient="index").reset_index()
        df_projetos.rename(columns={"index": "FAI"},inplace=True)
        df_projetos = df_projetos[["FAI","data inicio",'data mod',"data agenda",'pendente','realizado',"cliente","nome","status"]]
        df_projetos["data inicio"] = pd.to_datetime(df_projetos["data inicio"],unit='s', errors='coerce')
        df_projetos["data mod"] = pd.to_datetime(df_projetos["data mod"], unit='s', errors='coerce')
        df_projetos["data agenda"] = pd.to_datetime(df_projetos["data agenda"], unit='s', errors='coerce')
        df_projetos["prazo"] = df_projetos["data agenda"].apply(lambda x: max((x.replace(tzinfo=None) - data_atual.replace(tzinfo=None)).days, 0) if pd.notnull(x) else 0)
        maior_prazo = int(df_projetos["prazo"].max())
        df_projetos = df_projetos[["FAI","prazo",'pendente',"data agenda",'realizado',"cliente","nome","status","data inicio",'data mod']]
        if not concluidos_fai:
            df_projetos = df_projetos[df_projetos['status'] == False]
        df_projetos_editado = st.data_editor(df_projetos,column_config={"data inicio": st.column_config.DateColumn("Data de Início",format="DD/MM/YYYY"),
                "data mod": st.column_config.DateColumn("Última Modificação",format="DD/MM/YYYY"),"data agenda": st.column_config.DateColumn("Agenda",format="DD/MM/YYYY"),"prazo": st.column_config.ProgressColumn(
            "Prazo Restante",
            format="%d dias",  # Formato exibido no progresso
            min_value=0,  # Valor mínimo
            max_value= maior_prazo  # Valor máximo (ajuste de acordo com sua escala)
        )},hide_index=True, use_container_width=True)
            
            
        df_projetos_merged = pd.merge(df_projetos,df_projetos_editado,on="FAI",suffixes=('_df_og','_df_nv'),indicator=True)
        #st.dataframe(df_projetos_merged,hide_index=True)
        df_projetos_envio = df_projetos_merged [(df_projetos_merged["data inicio_df_og"] != df_projetos_merged["data inicio_df_nv"]) |
                                                    (df_projetos_merged["data mod_df_og"] != df_projetos_merged["data mod_df_nv"]) |
                                                    (df_projetos_merged["data agenda_df_og"] != df_projetos_merged["data agenda_df_nv"]) |
                                                    (df_projetos_merged["pendente_df_og"] != df_projetos_merged["pendente_df_nv"]) |
                                                    (df_projetos_merged["cliente_df_og"] != df_projetos_merged["cliente_df_nv"]) |
                                                    (df_projetos_merged["nome_df_og"] != df_projetos_merged["nome_df_nv"]) |
                                                    (df_projetos_merged["status_df_og"] != df_projetos_merged["status_df_nv"]) |
                                                    (df_projetos_merged["realizado_df_og"] != df_projetos_merged["realizado_df_nv"])
            ]        
        df_projetos_envio = df_projetos_envio[["FAI","data inicio_df_nv","data mod_df_nv","data agenda_df_nv","pendente_df_nv","cliente_df_nv","nome_df_nv","status_df_nv","realizado_df_nv"]]
        colunas_envio = {"FAI":'FAI',
                             "data inicio_df_nv":"data inicio",
                             "data mod_df_nv":"data mod",
                             "data agenda_df_nv":"data agenda",
                             "pendente_df_nv":"pendente",
                             "realizado_df_nv":"realizado",
                             "cliente_df_nv":"cliente",
                             "nome_df_nv":"nome",
                             "status_df_nv":"status"
                             }
        df_projetos_envio.rename(columns=colunas_envio, inplace=True)
        #st.dataframe(df_projetos_envio,hide_index=True)
            
        if atualizar_base:
                
            for i,row in df_projetos_envio.iterrows():
                    data_mod = data_atual.timestamp() 
                    dicionario_envio = row.to_dict()
                    data_inic = pd.to_datetime(dicionario_envio["data inicio"]).timestamp()
                    data_agenda= pd.to_datetime(dicionario_envio["data agenda"]).timestamp()
                    status_base = enviar_rtdb("projetos",dicionario_envio["FAI"],data_inic,data_mod,data_agenda,dicionario_envio["pendente"],dicionario_envio["realizado"],dicionario_envio["status"],dicionario_envio["cliente"],nome)
                    
                    if status_base:
                        fai_base = dicionario_envio["FAI"]
                        st.success(f"Atualizado:{fai_base} {data_atual.strftime('%d/%m/%Y %H:%M')}",icon="✅")

                    if not status_base:
                        fai_base = dicionario_envio["FAI"]
                        st.error(f"{fai_base} falha! ")



            # Verifica se há atualizações a cada intervalo (por exemplo, 5 segundos)
            with st.spinner("Atualizando dados..."):
                st_autorefresh(interval=5000, limit=15, key="firebase_update")
            

