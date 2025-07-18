import pandas as pd
import numpy as np
import streamlit as st
import json
import io
from datetime import datetime
from scipy.stats import norm
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import requests
import traceback

# Dicionário de tradução dos interesses
interests_translation = {
	"Activewear": "Roupas Esportivas",
	"Friends, Family & Relationships": "Amigos, Família e Relacionamentos",
	"Clothes, Shoes, Handbags & Accessories": "Moda",
	"Beauty & Cosmetics": "Beleza e Cosméticos",
	"Camera & Photography": "Fotografia",
	"Toys, Children & Baby": "Brinquedos, Crianças e Bebês",
	"Television & Film": "Televisão e Filmes",
	"Restaurants, Food & Grocery": "Restaurantes e Gastronomia",
	"Music": "Música",
	"Fitness & Yoga": "Fitness e Yoga",
	"Travel, Tourism & Aviation": "Turismo e Aviação",
	"Pets": "Animais de Estimação",
	"Cars & Motorbikes": "Carros e Motocicletas",
	"Beer, Wine & Spirits": "Cerveja, Vinho e Bebidas Alcoólicas",
	"Art & Design": "Arte e Design",
	"Sports": "Esportes",
	"Electronics & Computers": "Eletrônicos e Computadores",
	"Healthy Lifestyle": "Estilo de Vida Saudável",
	"Shopping & Retail": "Compras e Varejo",
	"Coffee, Tea & Beverages": "Café, Chá e Bebidas Quentes",
	"Jewellery & Watches": "Joias e Relógios",
	"Luxury Goods": "Artigos de Luxo",
	"Home Decor, Furniture & Garden": "Decoração, Móveis e Jardim",
	"Wedding": "Casamento",
	"Gaming": "Jogos Digitais",
	"Business & Careers": "Negócios e Carreiras",
	"Healthcare & Medicine": "Saúde e Medicina"
}

def format_milhar(valor):
	return f"{round(valor):,}".replace(",", ".") if valor is not None else None

def get_classes_sociais_formatadas(df, nome_influencer):
    resultado = df.loc[df["influencer"] == nome_influencer, "classes_sociais_formatadas"].values
    return resultado[0] if len(resultado) > 0 else "N/A"

def get_escolaridades_formatadas(df, nome_influencer):
    resultado = df.loc[df["influencer"] == nome_influencer, "educacao_formatada"].values
    return resultado[0] if len(resultado) > 0 else "N/A"

# Função para formatar os valores com separador de milhar
formatador_milhar = FuncFormatter(lambda x, _: f'{int(x):,}'.replace(',', '.'))

abas = st.tabs(["Página Inicial 🏠", "Resumo 📄", "Influencer 👤", "Audiência 📊", "Publicações 📝"])

with abas[0]:
	st.title("Análise de influenciadores")
	st.markdown("### Introdução")
	st.markdown('''Este app tem a função de consolidar o processo de extração de dados de influenciadores anteriormente 
 				implementado manualmente, caso a caso. O resumo tradicionalmente disponibilizado está disponível na aba
	 			Resumo, com a opção de download direto de um arquivo Excel. Separamos e adicionamos, ainda, dados e visualizações
	 			relativas ao Influencer, à Audiência e às Publicações às outras abas.''')

	st.markdown("### Como utilizar")
	st.markdown('''Os arquivos de input devem ser arquivos .json extraídos
 				diretamente do IMAI. Para o processo ser bem-sucedido, os arquivos devem ser nomeados no formato
	 			json_{perfil do influenciador}.json. Para já, apenas a análise dos perfis do Instagram é funcional.''')

	# Upload de múltiplos arquivos JSON
	st.markdown("### Uploader")
	uploaded_files = st.file_uploader("Carregue os arquivos JSON dos influencers", type="json", accept_multiple_files=True)
	
	# Inicialização
	influencers = []
	influencers_ficheiros = {}
	
	if uploaded_files:
		for file in uploaded_files:
			filename = file.name
			partes = filename.split("_")
			if len(partes) > 1:
				influencer = partes[1][:-5]  # Remover .json
				influencers.append(influencer)
				influencers_ficheiros[influencer] = file
			else:
				st.warning(f"O arquivo '{filename}' não segue o padrão esperado.")
	else:
		st.info("Por favor, carregue arquivos JSON para começar.")

	# Processar dados de cidades
	df_cidades = pd.DataFrame()

	for influencer, file in influencers_ficheiros.items():
		try:
			df_json = pd.read_json(file)
			cities_entries = df_json["audience_followers"]["data"]["audience_geo"]["cities"]
			df_temp = pd.json_normalize(cities_entries)
			df_temp["influencer"] = influencer
			df_cidades = pd.concat([df_cidades, df_temp], ignore_index=True)
		except Exception as e:
			st.warning(f"Sem registro de cidades para o influencer '{influencer}' ou erro ao processar: {e}")

	if not df_cidades.empty:
		df_cidades.rename(columns={"name": "Cidade"}, inplace=True)

	# Dentro da aba onde influencers_ficheiros é definido
	st.session_state["influencers_ficheiros"] = influencers_ficheiros

with abas[2]:

    # ============================
    # SEÇÃO: Cálculo da dispersão de likes/comentários 🔗
    # ============================
	perfis = []
	perfis_e_dispersoes = {}
    
	url = "https://instagram-scraper-api2.p.rapidapi.com/v1.2/posts"
	headers = {
		"x-rapidapi-key": "7f728d8233msh6b5402b6234f32ep135c63jsn7b9cdd64c9f7",
		"x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
	}

    # Passar pelos ficheiros uploadados pelo usuário e criar uma lista de perfis
	for i in influencers_ficheiros.keys():
		try:
			perfis.append(i)


    # Iterar sobre os perfis, "zerar" as listas e puxar os dados de likes e comentários (últimos posts)
			for perfil in perfis:
				likes_por_post = []
				comments_por_post = []

				# Alterar a query para o perfil e obter a resposta
				querystring = {"username_or_id_or_url":perfil}         
				response = requests.get(url, headers=headers, params=querystring)
				results = response.json()

				# Determinar o número de posts para a iteração e os cálculos
				n_posts = min(12, len(results["data"]["items"]))

                # Adicionar os dados dos posts às listas
				for i in range(n_posts):
					likes_por_post.append(results["data"]["items"][i]["like_count"])
					comments_por_post.append(results["data"]["items"][i]["comment_count"])

                # Garante que todos os valores sejam inteiros
				likes_por_post = [int(like) if like is not None else 0 for like in likes_por_post]

                # Calcula a média, desvpad e normaliza
				media_likes = np.mean(likes_por_post)
				media_comments = np.mean(comments_por_post)
                
				desvpad_likes = np.std(likes_por_post)
				desvpad_comments = np.std(comments_por_post)
            
				desvpad_normalizado_likes = (desvpad_likes/media_likes) * 100
				desvpad_normalizado_comments = (desvpad_comments/media_comments) * 100

                # Adiciona a dispersão ao dicionário de valores
				perfis_e_dispersoes[perfil] = round((desvpad_normalizado_comments + desvpad_normalizado_likes)/2, 0)

		except Exception as e:
			st.warning(f"Erro ao processar dados de {i}: {e}")
		
	try:
	# Transformar o dicionário em uma lista de dicionários
		dist_list = [{'Perfil': k, 'Dispersão': v} for k, v in perfis_e_dispersoes.items()]
    
    # Criar DataFrame a partir da lista
		dist_df = pd.DataFrame(dist_list)

    # Exibir no Streamlit
		st.dataframe(dist_df)

	except Exception as e:
		st.warning(f"Ocorreu um erro ao criar o DataFrame: {e}")

	# ============================
    # SEÇÃO: Extração da credibilidade da audiência 👫
    # ============================
	# st.subheader("Score da Audiência 👫")
	# A desenvolver - precisamos identificar uma forma de calcular o Score a partir dos dados disponíveis
	
    # ============================
    # SEÇÃO: Estatísticas básicas (visualizações, engajamento, etc)
    # ============================
	st.subheader("Dados Básicos por Influencer 📊")

    # Dicionário para consolidar os dados
	dados_consolidados = {}
    
	for i in influencers_ficheiros.keys():
		try:
			file = influencers_ficheiros.get(i)
			file.seek(0)
			file_bytes = file.read()
            
        # Carrega o conteúdo como JSON (dict)
			data = json.load(io.BytesIO(file_bytes))
			perfil = data.get("user_profile", {})

			engagement_rate = perfil.get("engagement_rate")
			if engagement_rate is not None:
				engagement_rate_str = f"{round(engagement_rate * 100, 2)}%"
			else:
				engagement_rate_str = None
    
        # Valores numéricos formatados com separador de milhar (ponto)
			dados_consolidados[i] = {
				"Followers": format_milhar(perfil.get("followers")),
				"Engajamento (%)": engagement_rate_str,
				"Média de Likes": format_milhar(perfil.get("avg_likes")),
				"Média de Comments": format_milhar(perfil.get("avg_comments")),
				"Média de Views (Reels)": format_milhar(perfil.get("avg_reels_plays")),
			}
            
		except Exception as e:
			st.warning(f"Erro ao processar dados de {i}: {e}")

	try:
        # Converte o dicionário consolidado em DataFrame
		df_consolidado = pd.DataFrame.from_dict(dados_consolidados, orient='index')
		df_consolidado.reset_index(inplace=True)
		df_consolidado.rename(columns={"index": "influencer"}, inplace=True)
        
        # Exibir no Streamlit
		st.dataframe(df_consolidado)
        
	except:
		st.warning(f"Erro ao processar dados: {e}")

    # ============================
    # SEÇÃO: Histórico (6 meses) 📈
    # ============================
    
    # Dropdown para seleção do influenciador
	influenciador_selecionado = st.selectbox("Selecione um influenciador:", list(influencers_ficheiros.keys()))
    
	if influenciador_selecionado:
		try:
            # Recupera e carrega o arquivo do influenciador selecionado
			file = influencers_ficheiros.get(influenciador_selecionado)
			file.seek(0)
			file_bytes = file.read()
			data = json.load(io.BytesIO(file_bytes))
			perfil = data.get("user_profile", {})
			stat_history = perfil.get("stat_history", [])
    
			if not stat_history:
				st.info(f"Sem dados históricos para {influenciador_selecionado}")
			else:
                # Converte o histórico em DataFrame
				df_hist = pd.DataFrame(stat_history)
				df_hist['month'] = pd.to_datetime(df_hist['month'])
				df_hist = df_hist.sort_values('month')

				st.subheader(f"Evolução histórica - {influenciador_selecionado}")
    
				# Função para formatar valores com separador de milhar
				formatador_milhar = FuncFormatter(lambda x, _: f'{int(x):,}'.replace(',', '.'))
    
                # Gráfico: Followers
				fig1, ax1 = plt.subplots(figsize=(8, 4))
				ax1.plot(df_hist['month'], df_hist['followers'], marker='o')
				ax1.set_title('Followers')
				ax1.set_xlabel('Mês')
				ax1.set_ylabel('Followers')
				ax1.yaxis.set_major_formatter(formatador_milhar)
				ax1.grid(True)
				fig1.autofmt_xdate()
				st.pyplot(fig1)

				# Gráfico: Engajamento Médio
				fig3, ax3 = plt.subplots(figsize=(8, 4))
				ax3.plot(df_hist['month'], df_hist['avg_engagements'], color='orange', marker='o')
				ax3.set_title('Engajamento Médio')
				ax3.set_xlabel('Mês')
				ax3.set_ylabel('Engajamentos')
				ax3.yaxis.set_major_formatter(formatador_milhar)
				ax3.grid(True)
				fig3.autofmt_xdate()
				st.pyplot(fig3)
    
		except Exception as e:
			st.warning(f"Erro ao gerar gráficos para {influenciador_selecionado}: {e}")
			
	# ============================
    # SEÇÃO: Extração de interesses da audiência 👫
    # ============================
	st.subheader("Interesses da Audiência 👫")

	df_top_interesses_formatado = pd.DataFrame(columns=["influencer", "interesses_formatados"])
	
	for i in influencers_ficheiros.keys():
		try:
			file = influencers_ficheiros.get(i)
			file.seek(0)
			file_bytes = file.read()
			df_influ = pd.read_json(io.BytesIO(file_bytes))
	
			# Interesses - Top 5
			interests_entries = df_influ.get("audience_followers", {}).get("data", {}).get("audience_interests", [])
			if isinstance(interests_entries, list):
				sorted_interests = sorted(interests_entries, key=lambda x: x.get("weight", 0), reverse=True)[:5]
	
			# Formatando os interesses com tradução, vírgulas e quebras de linha
			interesses_formatados = "  \n".join([
				f"{interests_translation.get(entry['name'], entry['name'])} ({entry['weight'] * 100:.2f}%)" + ("," if idx < len(sorted_interests) - 1 else "")
				for idx, entry in enumerate(sorted_interests)
				if 'name' in entry and 'weight' in entry
			])
	
			# Montar a linha do DataFrame
			df_top_interesses_formatado = pd.concat([
				df_top_interesses_formatado,
				pd.DataFrame([{
					"influencer": i,
					"interesses_formatados": interesses_formatados
				}])
			], ignore_index=True)
	
		except Exception as e:
			st.warning(f"Erro ao processar dados de {i}: {e}")

	# Exibir no Streamlit
	st.table(df_top_interesses_formatado)

with abas[1]:
	influencers_ficheiros = st.session_state.get("influencers_ficheiros", {})
	lista_consolidada = []

	for i in influencers_ficheiros.keys():
		try:
			file = influencers_ficheiros.get(i)
			file.seek(0)
			file_bytes = file.read()
	
			# Carrega o conteúdo JSON como dicionário
			data = json.load(io.BytesIO(file_bytes))
			
			username = data["user_profile"]["username"]
			nome = data["user_profile"]["fullname"]

			dispersion = int(round(perfis_e_dispersoes.get(username, "N/A"), 0))
			alcance = format_milhar(data["user_profile"].get("avg_reels_plays"))
			classe_social = get_classes_sociais_formatadas(df_classes_formatado, username)
			escolaridade = get_escolaridades_formatadas(df_educacao_formatado, username)
	
			interesses = df_top_interesses_formatado.loc[
				df_top_interesses_formatado["influencer"] == username,
				"interesses_formatados"
			].values
			interesses = interesses[0] if len(interesses) > 0 else "N/A"
	
			lista_consolidada.append({
				"Influencer (Username)": username,
				"Influencer (Nome)": nome,
				"Dispersão de interações": dispersion,
				"Alcance médio esperado por post": alcance,
				"Interesses da audiência": interesses,
				"Classe social": classe_social,
				"Escolaridade": escolaridade
			})

		except Exception as e:
			st.error(f"❌ Erro ao processar dados de {i}: {e}")
			st.text(traceback.format_exc())
	
	# Criar DataFrame final
	df_resultado = pd.DataFrame(lista_consolidada)

	# Nome do arquivo
	file_name = "resumo_defesa_influenciadores.xlsx"
	
	# Converter o DataFrame para um objeto Excel em memória
	output = io.BytesIO()
	with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
	    df_resultado.to_excel(writer, index=False, sheet_name='Defesa Influenciadores')
	    output.seek(0)
	
	# Exibir em Streamlit
	st.title("Consolidação de Influenciadores")
	st.table(df_resultado)

	# Botão de download
	st.download_button(
	    label="📥 Baixar tabela de resumo como Excel",
	    data=output,
	    file_name=file_name,
	    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
	)

######################### Informações da audiência #################################
with abas[3]:
# Seleção do número de registros por influencer
	top_n = st.selectbox("Quantas cidades deseja exibir por influencer?", [5, 10, 15, 20], index=0)

	df_cidades_exibicao = df_cidades.copy()
	df_cidades_exibicao.drop(columns=["coords.lat", "coords.lon", "country.id", "country.code", "state.id", "state.name", "id"], inplace=True, errors="ignore")
        
    # Converter 'weight' em porcentagem formatada com símbolo %
	df_cidades_exibicao["weight"] = df_cidades_exibicao["weight"] * 100
	df_cidades_exibicao["weight"] = df_cidades_exibicao["weight"].round(2).astype(str) + "%"

	df_cidades_exibicao.rename(columns={"weight":"Porcentagem da audiência"}, inplace=True)
	df_cidades_exibicao = df_cidades_exibicao.sort_values(by=["influencer", "Porcentagem da audiência"], ascending=[True, False]).groupby("influencer").head(top_n)

    # Mostrar tabela original
	st.subheader("Cidades por Influencer 🌎")
	st.dataframe(df_cidades_exibicao)

    # Botão para exportar a tabela para Excel
	data_hoje = datetime.today().strftime("%Y-%m-%d")
	file_name = f"cidades_por_influencer_{data_hoje}.xlsx"

	output = io.BytesIO()
	with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
		df_cidades_exibicao.to_excel(writer, index=False, sheet_name='Cidades')
	output.seek(0)
	processed_data = output.getvalue()

	st.download_button(
		label="📥 Baixar tabela de cidades como Excel",
		data=processed_data,
		file_name=file_name,
		mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
	)

	# BLOCO: Análise de Classes Sociais por Influencer
		st.subheader("Análise de Classes Sociais por Influencer 🧮")

		# Importar arquivo de classes sociais
		try:
			url_excel = "https://github.com/heitorleme/vis_influ/raw/refs/heads/main/classes_sociais_por_cidade.xlsx"
			classes_por_cidade = pd.read_excel(url_excel, header=0)

			# Normalizar peso por influencer
			df_cidades["normalized_weight"] = df_cidades.groupby("influencer")["weight"].transform(lambda x: x / x.sum())

            # Merge
			df_merged = pd.merge(df_cidades, classes_por_cidade, on=["Cidade"], how="inner")

            # Cálculo ponderado das classes
			df_merged["normalized_classe_de"] = df_merged["normalized_weight"] * df_merged["Classes D e E"]
			df_merged["normalized_classe_c"] = df_merged["normalized_weight"] * df_merged["Classe C"]
			df_merged["normalized_classe_b"] = df_merged["normalized_weight"] * df_merged["Classe B"]
			df_merged["normalized_classe_a"] = df_merged["normalized_weight"] * df_merged["Classe A"]

            # Média ponderada por influencer
			result = df_merged.groupby("influencer")[["normalized_classe_de", "normalized_classe_c", "normalized_classe_b", "normalized_classe_a"]].sum() * 100
			result = result.round(2)

            # Formatar resultado como string com quebras de linha e %
			df_classes_formatado = pd.DataFrame([
				{
					"influencer": idx,
					"classes_sociais_formatadas": "  \n".join([
						f"Classes D e E: {row['normalized_classe_de']:.2f}%",
						f"Classe C: {row['normalized_classe_c']:.2f}%",
						f"Classe B: {row['normalized_classe_b']:.2f}%",
						f"Classe A: {row['normalized_classe_a']:.2f}%"
					])
				}
				for idx, row in result.iterrows()
			])
		
		    # Exibir tabela formatada
			st.table(df_classes_formatado)

		except Exception as e:
			st.error(f"Erro ao carregar ou processar a planilha de classes sociais: {e}")

    # ============================
    # SEÇÃO: Análise de Educação 📚
    # ============================
	st.subheader("Análise de Educação por Influencer 📚")

	df = pd.DataFrame()
	df_ages = pd.DataFrame()

	for i in influencers_ficheiros.keys():
		try:
			file = influencers_ficheiros.get(i)
			file.seek(0)
			file_bytes = file.read()
			df_influ = pd.read_json(io.BytesIO(file_bytes))

            # Cidades
			cities_entries = df_influ.get("audience_followers", {}).get("data", {}).get("audience_geo", {}).get("cities", [])
			df_cities = pd.json_normalize(cities_entries)
			df_cities["influencer"] = i
			df = pd.concat([df, df_cities], ignore_index=True)

            # Idades
			age_entries = df_influ.get("audience_followers", {}).get("data", {}).get("audience_genders_per_age", [])
			ages = pd.json_normalize(age_entries)
			ages["influencer"] = i
			df_ages = pd.concat([df_ages, ages], ignore_index=True)

		except Exception as e:
			st.warning(f"Erro ao processar dados de {i}: {e}")

	if df_ages.empty or df.empty:
		st.info("Dados insuficientes para análise educacional.")
	else:
        # Preparar colunas e normalizar nomes
		df_ages["male"] = pd.to_numeric(df_ages["male"], errors="coerce")
		df_ages["female"] = pd.to_numeric(df_ages["female"], errors="coerce")
		df_ages["malefemale"] = df_ages["male"] + df_ages["female"]

		df["Cidade"] = df["name"]
		df_unido = pd.merge(df, df_ages, on="influencer")
		df_unido.rename(columns={"code": "faixa etária"}, inplace=True)

		try:
            # Importar dados educacionais
			url_excel = "https://github.com/heitorleme/vis_influ/raw/refs/heads/main/educacao_por_cidade.xlsx"
			df_edu = pd.read_excel(url_excel, header=0)

            # Transformar para formato longo
			df_edu_longo = pd.melt(df_edu,
								   id_vars="Cidade",
								   var_name="grupo",
								   value_name="average_years_of_education")

			df_edu_longo['gender'] = df_edu_longo['grupo'].str.extract(r'^(Homens|Mulheres)')
			df_edu_longo['faixa etária'] = df_edu_longo['grupo'].str.extract(r'(\d+\-\d+|\d+\+|\d+\-)')

			# Calcular pesos ponderados
			df_unido["male_weighted"] = df_unido["male"] * df_unido["weight"]
			df_unido["female_weighted"] = df_unido["female"] * df_unido["weight"]

            # Merge com dados educacionais
			df_merged = pd.merge(df_unido, df_edu_longo, on=["Cidade", "faixa etária"], how="inner")

			df_merged["contribution"] = df_merged.apply(
				lambda row: row["average_years_of_education"] * row["male_weighted"] * 2
				if row["gender"] == "Homens"
				else row["average_years_of_education"] * row["female_weighted"] * 2,
				axis=1
			)

            # Resultado final por influencer
			result_edu = df_merged.groupby('influencer').agg(
				Escolaridade_Média_Ponderada=('contribution', 'sum')
			).reset_index()

			result_edu["Escolaridade_Média_Ponderada"] = result_edu["Escolaridade_Média_Ponderada"].round(2)

			st.markdown("#### Distribuição Estimada por Faixa de Escolaridade 🎓")

            # Parâmetros da distribuição normal
			std_dev = 3

            # Inicializar lista de resultados
			dist_list = []

			for index, row in result_edu.iterrows():
				influencer = row["influencer"]
				mean = row["Escolaridade_Média_Ponderada"]

				prob_less_5 = norm.cdf(5, mean, std_dev) * 100
				prob_5_9 = (norm.cdf(9, mean, std_dev) - norm.cdf(5, mean, std_dev)) * 100
				prob_9_12 = (norm.cdf(12, mean, std_dev) - norm.cdf(9, mean, std_dev)) * 100
				prob_more_12 = (1 - norm.cdf(12, mean, std_dev)) * 100
				
				dist_list.append({
					"Influencer": influencer,
					"< 5 anos": round(prob_less_5, 2),
					"5-9 anos": round(prob_5_9, 2),
					"9-12 anos": round(prob_9_12, 2),
					"> 12 anos": round(prob_more_12, 2)
				})

            # Criar DataFrame a partir da lista
			dist_df = pd.DataFrame(dist_list)
			
			# Formatar os dados em uma única célula com quebras de linha
			df_educacao_formatado = pd.DataFrame([
			    {
			        "influencer": row["Influencer"],
			        "educacao_formatada": "  \n".join([
			            f"< 5 anos: {row['< 5 anos']:.2f}%",
			            f"5–9 anos: {row['5-9 anos']:.2f}%",
			            f"9–12 anos: {row['9-12 anos']:.2f}%",
			            f"12+ anos: {row['> 12 anos']:.2f}%"
			        ])
			    }
			    for _, row in dist_df.iterrows()
			])

			# Exibir no Streamlit
			st.table(df_educacao_formatado)
		except Exception as e:
			st.error(f"Erro ao carregar ou processar a planilha de educação: {e}")

######################### Informações dos posts #################################
# Publicações do Insta
with abas[4]:
	# Dropdown para seleção do influenciador
	influencers_ficheiros = st.session_state.get("influencers_ficheiros", {})
	influenciador_selecionado = st.selectbox("Selecione um influenciador:", list(influencers_ficheiros.keys()), key="select_influencer_posts")
	
	if influenciador_selecionado:
		try:
			# Recupera e carrega o arquivo do influenciador selecionado
			file = influencers_ficheiros.get(influenciador_selecionado)
			file.seek(0)
			file_bytes = file.read()
			data = json.load(io.BytesIO(file_bytes))
			commercial_posts = data["user_profile"].get("commercial_posts", [])
			recent_posts = data["user_profile"].get("recent_posts", [])
			
			st.title("💰 Posts comerciais - {}".format(influenciador_selecionado))
			marcas_posts = []
			likes_posts = []
			comments_posts = []
			shares_posts = []

			for post in commercial_posts:
				likes_posts.append(post["stat"].get("likes", 0))
				comments_posts.append(post["stat"].get("comments", 0))
				shares_posts.append(post["stat"].get("shares", 0))
				try:
					marcas_posts.append(post["sponsor"].get("usename", 0))
				except:
					continue

			likes_total = np.mean(likes_posts)
			comments_total = np.mean(comments_posts)
			shares_total = np.mean(shares_posts)
			marcas_posts = np.unique(marcas_posts)

			# Geração do texto com links formatados em Markdown
			texto_links = ""
			for marca in marcas_posts:
			    url = f"https://www.instagram.com/{marca}"
			    texto_links += f"- [{marca}]({url})\n"

			# Exibe o quadro de texto com os links
			st.markdown("### Perfis no Instagram das marcas mencionadas:")
			st.markdown(texto_links)

			st.markdown("### Métricas das publicações identificadas na amostra:")
			col1, col2, col3 = st.columns(3)
			with col1:
				st.metric(label="👍 Média de Likes", value=f"{int(likes_total):,}")
			with col2:
				st.metric(label="💬 Média de Comentários", value=f"{int(comments_total):,}")
			with col3:
				st.metric(label="🔁 Média de Shares", value=f"{int(shares_total):,}")

			st.markdown("### Posts:")	
			# Divide os posts em linhas com 3 colunas cada
			for row_start in range(0, len(commercial_posts), 3):
				cols = st.columns(3)
				for i in range(3):
					if row_start + i >= len(commercial_posts):
						break
					post = commercial_posts[row_start + i]
					link = post.get("link", "#")
					with cols[i]:
						img_url = post.get("thumbnail") or post.get("user_picture")
						if img_url:
							st.markdown(
								f'<a href="{link}" target="_blank"><img src="{img_url}" style="width:100%; border-radius:10px;" /></a>',
								unsafe_allow_html=True
							)
						else:
							st.warning("Imagem não disponível para este post.")
			
						# Caption do post
						st.markdown(f"**{post.get('text', '')}**")
			
						# Link e estatísticas
						stats = post.get("stat", {})
						likes = stats.get("likes", 0)
						comments = stats.get("comments", 0)
						shares = stats.get("shares", 0)
			
						st.markdown(f"👍 Likes: **{likes}**")
						st.markdown(f"💬 Comentários: **{comments}**")
						st.markdown(f"🔁 Compartilhamentos: **{shares}**")
			
			st.title("⏰ Posts recentes - {}".format(influenciador_selecionado))
	
			# Divide os posts em linhas com 3 colunas cada
			for row_start in range(0, len(recent_posts), 3):
				cols = st.columns(3)
				for i in range(3):
					if row_start + i >= len(recent_posts):
						break
					post = recent_posts[row_start + i]
					link = post.get("link", "#")
					with cols[i]:
						img_url = post.get("thumbnail") or post.get("user_picture")
						if img_url:
							st.markdown(
								f'<a href="{link}" target="_blank"><img src="{img_url}" style="width:100%; border-radius:10px;" /></a>',
								unsafe_allow_html=True
							)
						else:
							st.warning("Imagem não disponível para este post.")
			
						# Caption do post
						st.markdown(f"**{post.get('text', '')}**")
			
						# Link e estatísticas
						stats = post.get("stat", {})
						likes = stats.get("likes", 0)
						comments = stats.get("comments", 0)
						shares = stats.get("shares", 0)
		
						st.markdown(f"👍 Likes: **{likes}**")
						st.markdown(f"💬 Comentários: **{comments}**")
						st.markdown(f"🔁 Compartilhamentos: **{shares}**")
					
		except Exception as e:
			st.warning(f"Erro ao buscar publicações para {influenciador_selecionado}: {e}")

