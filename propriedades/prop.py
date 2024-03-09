import streamlit as st
import CoolProp.CoolProp as prop
from CoolProp.CoolProp import PropsSI,PhaseSI
from pathlib import Path
from PIL import Image
import pandas as pd
import numpy as np

#Inicial
programas = ["Propriedades Termodinâmicas","Final"]
legendas1 = ["Fornece gráfico de propriedades termodinamicas selecionadas","Informações sobre o programa"]

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
            fluido_selecionado = st.selectbox("Fluido", lista_fluidos, index=90)
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
                    grafico_df.loc[(i),"Densidade"] = prop.PropsSI('D', 'T', temperatura_consulta, 'P', grafico_df.loc[i,"Pressão_Pa"], fluido_selecionado)
                    grafico_df.loc[(i),"Viscosidade"] = prop.PropsSI('VISCOSITY', 'T', temperatura_consulta, 'P',grafico_df.loc[i, "Pressão_Pa"], fluido_selecionado)
                    grafico_df.loc[(i),"Estado"] = PhaseSI('P',grafico_df.loc[i, "Pressão_Pa"],'T', temperatura_consulta, fluido_selecionado)


            elif condicao_x == "Temperatura":
                grafico_df = pd.DataFrame(columns=["Temperatura", "Densidade", "Viscosidade", "Estado"])
        with col7:
            propriedade_y = st.selectbox("Propriedade", ['Densidade','Viscosidade'], index=1)

        st.table(grafico_df)

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



    # experiencias
    st.write("#")
    st.subheader("Skills",anchor=False)
    st.write(
        """
            :white_check_mark: Paineis de automação
            :white_check_mark: Programação em Python 
            :white_check_mark: Especificação de componentes
        """
        ,anchor=False
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
