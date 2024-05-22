import streamlit as st
import CoolProp.CoolProp as prop
from CoolProp.CoolProp import PropsSI,PhaseSI
from pathlib import Path
from PIL import Image
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from io import BytesIO
from scipy.optimize import fsolve

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

    # Criação do DataFrame
    df_tubos = pd.DataFrame(dados_tubos)
    rugosidade_data = {'Outro':"n/a",'Aço carbono':0.046,'PVC':0.0015,'Inox':0.015,'Ferro Fundido':0.26,'Aço comercial ou ferro Forjado':0.046}
    materiais_lista = df_tubos['Material'].unique().tolist()

    metodo_carga = st.selectbox("Selecione o metodo de calculo", ["Simplificado", "Sucção/recalque/NPSHd"])
    carga1, carga2, carga3, carga4 = st.columns(4)
    with carga1:
        st.header("Pressão", anchor=False)
        carga_un = st.selectbox("Unidade", ["Mcf", "Bar", "Pa"], index=0)
        altura_entrada = st.number_input("Altura inicial [m]", min_value=0.0, step=0.1, format="%.1f")
        altura_saida = st.number_input("Altura final [m]", min_value=0.0, step=0.1, format="%.1f")
    with carga2:
        st.header("Fluido", anchor=False)
        carga_vazao = st.number_input("Q [m³/h]", min_value=0.000001, step=0.01, format="%.2f")
        carga_vazao_str = (carga_vazao)
        carga_densidade =  st.number_input("ρ [kg/m³]", min_value=0.000001, step=0.01, format="%.2f", value=999.0)
        carga_visosidade_ = st.number_input("μ [Cp]", min_value=0.00001, step=0.001, format="%.3f", value=1.01)
        carga_visosidade = carga_visosidade_/1000
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
            diametro_int = df_tubos.loc[(df_tubos['Material'] == tipo_tubo_str) & (df_tubos['Bitola nominal'] == diametro_tubo_str), 'D interno'].values
            diametro_int_str = diametro_int[0] if len(diametro_int) > 0 else -1
            st.subheader("Ø int \n {} mm".format(diametro_int_str), anchor=False)
        velocidade = f_velocidade(diametro_int_str,carga_vazao_str)
        st.subheader("Velocidade \n {:.2f} m/s".format(velocidade),anchor=False)

    st.header("Acessórios", anchor=False)



    #inserção de acessórios

    # Inicializar o estado, se necessário
    if 'inputs' not in st.session_state:
        st.session_state['inputs'] = []


    # Função para adicionar um campo de entrada
    def add_input():
        st.session_state['inputs'].append({'Acessório': 'Cotovelo 90°, padrão', 'Quantidade': 1})

    # Função para remover um campo de entrada
    def remove_input(index):
        st.session_state['inputs'].pop(index)

    #lista de acessórios
    # Dicionário com os dados fornecidos
    perda_friccao_dict = {
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
    acessorios = list(perda_friccao_dict.keys())

    # Botão que, ao ser pressionado, aciona a função add_input
    st.button('Adicionar acessório', on_click=add_input)

    # Exibir os campos de entrada baseados no número armazenado no estado da sessão
    # Exibir os campos de entrada baseados no número armazenado no estado da sessão
    # Exibir os campos de entrada baseados no número armazenado no estado da sessão
    for i, value in enumerate(st.session_state['inputs']):
        # Forçar o valor a ser um dicionário, caso não seja
        if not isinstance(value, dict):
            st.session_state['inputs'][i] = {'Acessório': 'Cotovelo 45°, padrão', 'Quantidade': 1}

        col1, col2, col3 = st.columns([4, 2, 2])
        with col1:
            current_acessorio = st.session_state['inputs'][i].get('Acessório','Cotovelo 45°, padrão')
            acessorio = st.selectbox("Acessório", acessorios, index=acessorios.index(current_acessorio),key=f'acessorio_{i}')
            st.session_state['inputs'][i]['Acessório'] = acessorio
        with col2:
            current_quantidade = st.session_state['inputs'][i].get('Quantidade', 1)
            quantidade = st.number_input("Quantidade", min_value=1, step=1, key=f'quantidade_{i}',value=current_quantidade)
            st.session_state['inputs'][i]['Quantidade'] = quantidade
        with col3:
            st.subheader("\n", anchor=False)
            st.button('Excluir', key=f'remove_{i}', on_click=remove_input, args=(i,))

    # Exibir o estado atual dos inputs para depuração
    st.write(st.session_state['inputs'])

    reynolds = f_reynolds(carga_densidade, carga_visosidade, velocidade, diametro_int_str)
    fator_atrito = f_colebrook(reynolds, diametro_int_str, rugosidade)
    st.subheader("Reynolds \n {:.2f} ".format(reynolds), anchor=False)
    st.subheader("f \n {:.4f} ".format(fator_atrito), anchor=False)
    st.subheader("e/d \n {:.6f} ".format(rugosidade / diametro_int_str), anchor=False)

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
