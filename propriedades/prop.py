import streamlit as st
import CoolProp.CoolProp as prop
from CoolProp.CoolProp import PropsSI,PhaseSI
from pathlib import Path
from PIL import Image

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
            qualidade = prop.PropsSI('Q', 'T', temperatura_consulta, 'P', pressão_consulta, fluido_selecionado)
            viscosidade_cp = viscosidade_Pas*1000
            #fase = PhaseSI('P', pressão_consulta,)

            texto_viscosidade = "{:.3f} Cp".format(viscosidade_cp)
            st.title(texto_viscosidade,anchor=False)
            texto_densidade = "{:.3f} kg/m³".format(densidade)
            st.title(texto_densidade,anchor=False)
            texto_titulo = "{:.3f} ".format(qualidade)
            st.title(texto_titulo,anchor=False)
        except Exception as e:
            st.title("Não disponível para este fluido")
            st.write(str(e))



if applicativo == "Final":
    arqivo_css = 'https://github.com/JoaoJuniorGrb/app/blob/4ef7f6d97028d111ca7ddc34ff1a2e6c6e9b0a3f/propriedades/styles/main.css'
    arqivo_pdf = 'https://github.com/JoaoJuniorGrb/app/blob/4ef7f6d97028d111ca7ddc34ff1a2e6c6e9b0a3f/propriedades/assets/Curriculo.pdf'
    arqivo_img = 'https://github.com/JoaoJuniorGrb/app/blob/4ef7f6d97028d111ca7ddc34ff1a2e6c6e9b0a3f/propriedades/assets/Foto_.jpg'
    titulo = "Curriculum | João Ferreira Junior"
    nome = "João Ferreira Junior"
    descrição = "Engenheiro de Energia, Pós graduação em Automação e controle de processos Conhecimento em Python e microcontroladores"
    st.title('Desenvolvido por',nome)

    email = "joaojunior.grb@hotmail.com"
    midia_social = {"LinkedIn": "https://www.linkedin.com/in/jo%C3%A3o-ferreira-junior-b2698163/?lipi=urn%3Ali%3Apage%3Ad_flagship3_feed%3BAjwOn5KcRhmkdM6UuXiVjw%3D%3D"}

    projetos = {":toolbox: Ferramenta 1": "ferramenta 1",
                ":toolbox: Ferramenta 2": "ferramenta 2",
                ":toolbox: Ferramenta 3": "ferramenta 2"}

    # carregando assets
    #with open(arqivo_css) as c:
    #   st.markdown("<style>{}</style>".format(c.read()), unsafe_allow_html=True)
   
    
    imagem = Image.open(arqivo_img)

    col1, col2 = st.columns(2, gap="small")

    with col1:
        st.image(imagem, width=250)

    with col2:
        st.title(nome,anchor=False)
        st.write(descrição,anchor=False)
        st.download_button(label="Download Curriculum",
                           data=pdfleitura,
                           file_name=arquivo_pdf.name,
                           mime="aplication/octet-stream"
                           )
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
