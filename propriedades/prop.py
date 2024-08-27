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


#Inicial
programas = ["Perda de Carga","Propriedades Termodinamicas","Placa de orificio","Tubulacao de vapor","Final", "Base Instalada"]
legendas1 = ["Cálculo de perda de carga","Fornece gráfico de propriedades termodinamicas selecionadas",'Em desenvolvimento','Em desenvolvimento',"Informações sobre o programa","ZTND"]

st.sidebar.header("Selecione o programa desejado")
applicativo = st.sidebar.radio("Seleção",programas)

# Mostra a legenda correspondente à opção selecionada
indice_selecionado = programas.index(applicativo)
st.sidebar.write(legendas1[indice_selecionado])

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
        st.plotly_chart(fig)
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
        st.plotly_chart(fig)

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

            if dados_fluido == "Outro":
                p_vapor = st.number_input("P. de Vapor [Bar]", min_value=0.000001,step=0.1, format="%.4f")
                carga_densidade = st.number_input("ρ [kg/m³]", min_value=0.000001, step=0.01, format="%.1f",value=999.0)
                carga_visosidade_ = st.number_input("μ [Cp]", min_value=0.00001, step=0.001, format="%.3f", value=1.01)
                carga_visosidade = carga_visosidade_ / 1000
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
                carga_densidade = prop.PropsSI('D', 'T', (temperatura_npsh + 273.15), 'P', abs_press, fluido_npsh)
                carga_visosidade = prop.PropsSI('VISCOSITY', 'T', (temperatura_npsh + 273.15), 'P', abs_press,fluido_npsh)
            # st.title("Min {}".format(min_altitude), anchor=False)
            # st.title("Max {}".format(max_altitude), anchor=False)
            # st.title("Med {}".format(med_altitude), anchor=False)
            abs_bar = abs_press / (100000)
            abs_mcf = (abs_bar * 100000)/(9.81 * carga_densidade)
            bar_vapor = p_vapor * margem_pv
            st.subheader("Pressão Abs \n {:.3f} Bar Absoluto \n( {:.2f} mcf )".format(abs_bar, abs_mcf), anchor=False)
            st.subheader("Pressão vapor \n {:.3f} Bar absoluto".format(bar_vapor), anchor=False)

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
            carga_densidade = prop.PropsSI('D', 'T', (temperatura_npsh + 273.15), 'P', abs_press, fluido_npsh)
            carga_visosidade = prop.PropsSI('VISCOSITY', 'T', (temperatura_npsh + 273.15), 'P', abs_press, fluido_npsh)
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

        perda_bar = (df_acessorios_usados["perda [m²/s²]"].sum()) * carga_densidade / 100000
        # st.table(df_acessorios_usados)
        dinamica_bar = (carga_densidade * (velocidade * velocidade) )/ (2 * 100000)
        npsh_disponivel_bar = abs_bar - bar_vapor - perda_bar + dinamica_bar + (
        altura_entrada_npsh * 9.81 * carga_densidade / 100000)
        npsh_disponivel_mcf = (npsh_disponivel_bar * 100000)/(9.81 * carga_densidade)
        st.subheader("NPSH = Pabs + Pdin + Palt - Perda carga - Pvapor",anchor=False)
        st.subheader("NPSH=({:.3f})+({:.3f})+({:.3f})-({:.3f})-({:.3f})".format(abs_bar,dinamica_bar,(altura_entrada_npsh * 9.81 * carga_densidade / 100000) ,perda_bar,bar_vapor),
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
            lambda x: f_reynolds(carga_densidade, carga_visosidade, x, diametro_int_str))
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
        df_grafico_perda['Perda carga bar'] = (df_grafico_perda['Perda total m²/s²'] * carga_densidade) / 100000
        df_grafico_perda['ABS bar'] = abs_bar
        df_grafico_perda['Pv bar'] = bar_vapor
        df_grafico_perda['P Altura bar'] = altura_entrada_npsh * 9.81 * carga_densidade / 100000
        df_grafico_perda['P dinamica bar'] = carga_densidade * (df_grafico_perda['Velocidade m/s'] ** 2) / (2 * 100000)
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
        st.plotly_chart(fig)

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
    
    # Criando o autenticador
    authenticator = stauth.Authenticate(
        config['credentials'],
        'some_cookie_name',
        'some_signature_key',
        cookie_expiry_days=9000
    )
    
    # Exibindo a tela de login
    name, authentication_status, username = authenticator.login()

    if authentication_status:
        st.write(f'Bem-vindo {name}!')
    elif authentication_status is False:
        st.error('Nome de usuário ou senha incorretos')
    elif authentication_status is None:
        st.warning('Por favor, insira seu nome de usuário e senha')

    # Opcional: Adicionar uma opção de logout
    if authentication_status:
        if st.sidebar.button('Logout'):
            authenticator.logout('Logout', 'sidebar')
            st.experimental_rerun()
