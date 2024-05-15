import streamlit as st
import CoolProp.CoolProp as prop
from CoolProp.CoolProp import PropsSI,PhaseSI
from pathlib import Path
from PIL import Image
import pandas as pd
import numpy as np
import plotly.express as px
import requests

#Inicial
programas = ["Propriedades Termodinâmicas","Perda de Carga","Final"]
legendas1 = ["Fornece gráfico de propriedades termodinamicas selecionadas","Cálculo de perda de carga","Informações sobre o programa"]

st.sidebar.header("Selecione o programa desejado")
applicativo = st.sidebar.radio("Seleção",programas,captions = legendas1)


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
            un_pressão = st.selectbox("Un",["MCA","Bar","Pa"],index=1)
        with col4:
            st.header("Temp.",anchor=False)
            temperatura = st.number_input("Digite a temperatura", min_value=0.1,step=0.1,format="%.1f")
        with col5:
            st.header("Un.", anchor=False)
            un_temperatura = st.selectbox("Un.", ["°C", "K"])

        #obter propriedades atravéz do coolprop
        pressão_consulta = (9806.38 * pressao) if (un_pressão == "MCA") else (100000*pressao) if (un_pressão == "Bar") else pressao
        temperatura_consulta = (273.155 + temperatura) if un_temperatura == "°C" else temperatura
        try:
            viscosidade_Pas = prop.PropsSI('VISCOSITY', 'T', temperatura_consulta, 'P', pressão_consulta, fluido_selecionado)
            densidade = prop.PropsSI('D', 'T', temperatura_consulta, 'P', pressão_consulta, fluido_selecionado)
            qualidade = PhaseSI('P', pressão_consulta, 'T', temperatura_consulta, fluido_selecionado)
            viscosidade_cp = viscosidade_Pas*1000
            temperatura_ebulição = PropsSI('T','P', pressão_consulta,'Q',0,fluido_selecionado)
            temperatura_ebulição = temperatura_ebulição - 273.15
            p_vapor = PropsSI('P', 'T', temperatura_consulta, 'Q', 1, fluido_selecionado)
            p_vapor =   p_vapor/100000
            texto_viscosidade = "{:.3f} Cp".format(viscosidade_cp)
            st.subheader(texto_viscosidade,anchor=False,divider="blue")
            texto_densidade = "{:.3f} kg/m³".format(densidade)
            st.subheader(texto_densidade,anchor=False,divider="blue")
            texto_titulo = qualidade
            st.subheader(texto_titulo,anchor=False,divider="blue")
            texto_ebulição = "Ebulição {:.1f} °C".format(temperatura_ebulição)
            st.subheader(texto_ebulição, anchor=False,divider="blue")
            texto_pvapor = "P vapor {:.3f} Bar".format(p_vapor)
            st.subheader(texto_pvapor, anchor=False, divider="blue")

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

if applicativo == "Perda de Carga":
    rugosidade_data = {'Aço Carbono':0.15,'Cobre':0.0015,'PVC':0.0018,'Aço Inoxidável':0.015,'Ferro Fundido':0.26,'Aço comercial ou ferro Forjado':0.046}
    materiais_lista = rugosidade_data.keys()
    materiais_lista = list(materiais_lista)
    metodo_carga = st.selectbox("Selecione o metodo de calculo", ["Simplificado", "Sucção/recalque/NPSHd"])
    carga1, carga2, carga3, carga4 = st.columns(4)
    with carga1:
        st.header("Pressão", anchor=False)
        carga_un = st.selectbox("Unidade", ["Mcf", "Bar", "Pa"], index=1)
    with carga2:
        st.header("Vazão", anchor=False)
        carga_vazao = st.number_input("m³/h", min_value=0.1, step=0.1, format="%.1f")
    with carga3:
        st.header("Tubo", anchor=False)
        carga_tubo = st.selectbox("Unid", materiais_lista, index=1)
    with carga4:
        st.header("   Ø", anchor=False)
        carga_tubo = st.selectbox("Uni", ['1/4”','1/2”','3/8”','3/4”','1”,3”','4”','5”','6”','8”','10”','12”','1.1/4”','1.1/2”','2”','2.1/2”'], index=1)

    st.header("P Entrada (0 em ambiente)", anchor=False)
    carga5, carga6 = st.columns(2)
    with carga5:
        carga_entrada = st.number_input("Manométrica", min_value=0.0, step=0.1, format="%.1f")
    with carga6:
        altura_entrada = st.number_input("Altura [m]", min_value=0.0, step=0.1, format="%.1f")

    st.header("P Saída (0 em ambiente)", anchor=False)
    carga7, carga8 = st.columns(2)
    with carga7:
        carga_saída = st.number_input("P saida", min_value=0.0, step=0.1, format="%.1f")
    with carga8:

        altura_saida = st.number_input("Altura [m] ", min_value=0.0, step=0.1, format="%.1f")

if applicativo == "Final":
    arqivo_css = 'https://github.com/JoaoJuniorGrb/app/blob/4ef7f6d97028d111ca7ddc34ff1a2e6c6e9b0a3f/propriedades/styles/main.css'
    arqivo_pdf = 'https://github.com/JoaoJuniorGrb/app/blob/4ef7f6d97028d111ca7ddc34ff1a2e6c6e9b0a3f/propriedades/assets/Curriculo.pdf'
    arqivo_img = 'https://github.com/JoaoJuniorGrb/appestreamlit/blob/624cf41fb2c6bc7152359344c6d0b29f264228e1/Foto_.jpg?raw=true'
    titulo = "Curriculum | João Ferreira Junior"
    nome = "João Ferreira Junior"
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








#remove estilo stream lit
remove_st_estilo = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""

st.markdown(remove_st_estilo,unsafe_allow_html=True)
