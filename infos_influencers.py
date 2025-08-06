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

st.set_page_config(layout="wide")
abas = st.tabs(["Página Inicial 🏠", "Resumo 📄", "Posts 📸"])

with abas[0]:
	st.title("Análise de influenciadores")
	st.markdown("### Introdução")
	st.markdown('''Este app tem a função de consolidar o processo de extração de dados de influenciadores anteriormente 
 				implementado manualmente, caso a caso. O resumo tradicionalmente disponibilizado está disponível na aba
	 			Resumo, com a opção de download direto de um arquivo Excel. Num futuro próximo planejamos separar e adicionar, ainda, dados e visualizações
	 			relativas ao Influencer, à Audiência e às Publicações a outras abas.''')

	st.markdown("### Como utilizar")
	st.markdown('''Os arquivos de input devem ser arquivos .json extraídos
 				diretamente do IMAI. Para o processo ser bem-sucedido, os arquivos devem ser nomeados no formato
	 			```json_{perfil do influenciador}.json```. Para já, apenas a análise dos perfis do Instagram é funcional.''')

	# Upload de múltiplos arquivos JSON
	st.markdown("### Uploader")
	uploaded_files = st.file_uploader("Carregue os arquivos JSON dos influencers", type="json", accept_multiple_files=True)
	
	# Inicialização
	influencers = []
	ficheiros = []
	dados_brutos = {}
	df_cidades = pd.DataFrame()
	
	if uploaded_files:
		for file in uploaded_files:
			filename = file.name
			if "desktop.ini" in filename:
				continue
			else:
				ficheiros.append(file)
				partes = filename.split("_")
				if len(partes) > 1:  # Verifica se há pelo menos dois elementos após o split
					influencers.append(partes[1].replace(".json", ""))
				else:
					print(f"Aviso: O arquivo '{filename}' não segue o padrão esperado.")
		influencers_ficheiros = dict(zip(influencers, ficheiros))

		dados_brutos = {}

		for influencer, arquivo_json in influencers_ficheiros.items():
			try:
				dados_brutos[influencer] = json.load(arquivo_json)
			except:
				st.warning("Erro ao processar o arquivo para o influenciador {}".format(influencer))

		for influencer in dados_brutos.keys():
			try:
				cities_entries = dados_brutos.get(influencer)["audience_followers"]["data"]["audience_geo"]["cities"]
				df_temp = pd.json_normalize(cities_entries)
				df_temp["influencer"] = influencer
				df_cidades = pd.concat([df_cidades, df_temp])
			except Exception as e:
				st.warning(f"Sem registro de cidades para '{influencer}': {e}")

		try:
			df_cidades = df_cidades[df_cidades["country.code"] == "BR"]
			df_cidades.rename(columns={"name":"Cidade"}, inplace=True)
		except:
			st.warning("Sem dados de cidade para um ou mais dos influencers")
		
	else:
		st.info("Por favor, carregue arquivos JSON para começar.")

	try:
		st.session_state["dados_brutos"] = dados_brutos
		st.session_state["influencers_ficheiros"] = influencers_ficheiros
		st.session_state["df_cidades"] = df_cidades
	except:
		pass

with abas[1]:
	if uploaded_files:
		# Importar os session states relevantes
		dados_brutos = st.session_state["dados_brutos"]
		df_cidades = st.session_state["df_cidades"]
		
		############ Classes sociais ############
		classes_por_cidade = pd.read_excel(r"./dados/classes_sociais_por_cidade.xlsx")
		classes_por_cidade.drop(columns=["Unnamed: 0"], inplace=True)
	
		df_classes_influ = df_cidades.copy()
		# Primeiro, soma total de weight por influencer
		total_weight_por_influencer = df_classes_influ.groupby("influencer")["weight"].transform("sum")
		
		# Depois, soma de weight por influencer + cidade
		total_weight_por_cidade = df_classes_influ.groupby(["influencer", "Cidade"])["weight"].transform("sum")
		
		# Agora, atribuímos o weight normalizado (valor da cidade dividido pela soma total do influencer)
		df_classes_influ["normalized_weight"] = total_weight_por_cidade / total_weight_por_influencer
	
		df_merged_classes = pd.merge(df_classes_influ, classes_por_cidade, on=["Cidade"], how="inner")

		# Recalcular 'normalized_weight' após merge
		df_merged_classes["total_weight"] = df_merged_classes.groupby("influencer")["normalized_weight"].transform("sum")
		df_merged_classes["normalized_weight"] = df_merged_classes["normalized_weight"] / df_merged_classes["total_weight"]
		
		# Remover coluna auxiliar
		df_merged_classes.drop(columns="total_weight", inplace=True)
	
		df_merged_classes["normalized_classe_de"] = df_merged_classes["normalized_weight"] * df_merged_classes["Classes D e E"]
		df_merged_classes["normalized_classe_c"] = df_merged_classes["normalized_weight"] * df_merged_classes["Classe C"]
		df_merged_classes["normalized_classe_b"] = df_merged_classes["normalized_weight"] * df_merged_classes["Classe B"]
		df_merged_classes["normalized_classe_a"] = df_merged_classes["normalized_weight"] * df_merged_classes["Classe A"]
	
		result_classes = df_merged_classes.groupby("influencer")[[
																    "normalized_classe_de",
																    "normalized_classe_c",
																    "normalized_classe_b",
																    "normalized_classe_a"
																]].sum()
		result_classes = result_classes.round(2)

		result_classes.columns= ["Classes D e E", "Classe C", "Classe B", "Classe A"]
		
		result_classes[["Classes D e E", "Classe C", "Classe B", "Classe A"]] /= 100
	
		result_classes["distribuicao_formatada"] = result_classes.apply(
		    lambda row: f"Classes D e E: {row['Classes D e E']:.2%},  \n"
		                f"Classe C: {row['Classe C']:.2%},  \n"
		                f"Classe B: {row['Classe B']:.2%},  \n"
		                f"Classe A: {row['Classe A']:.2%}",
		    axis=1
		)
		
		# Trocar ponto por vírgula para notação percentual brasileira
		result_classes["distribuicao_formatada"] = result_classes["distribuicao_formatada"].str.replace('.', ',', regex=False)
		result_classes = result_classes.reset_index()
		st.session_state["result_classes"] = result_classes
		
		# Converter em dicionário
		classes_sociais_dict = result_classes.set_index('influencer')['distribuicao_formatada'].to_dict()
		st.session_state["classes_sociais_dict"] = classes_sociais_dict
	
		############ Educação ############
		# Importar educação por cidade
		educacao_por_cidade = pd.read_excel(r"./dados/educacao_por_cidade.xlsx")
		
		# Copiar df_cidades
		df_cidades_edu = df_cidades.copy()
		
		# Extrair gênero e idade das audiências
		df_demografia_audiencia = pd.DataFrame()
	
		for influencer in dados_brutos.keys():
		    try:
		        cities_entries = dados_brutos.get(influencer)["audience_followers"]["data"]["audience_genders_per_age"]
		        df_temp = pd.json_normalize(cities_entries)
		        df_temp["influencer"] = influencer
		        df_demografia_audiencia = pd.concat([df_demografia_audiencia, df_temp])
		    except Exception as e:
		        st.warning(f"Sem registro de cidades para '{influencer}': {e}")
		
		# Unir os DataFrames de Cidades e Idades
		df_unido = pd.merge(df_cidades_edu, df_demografia_audiencia, on="influencer")
		df_unido.rename(columns={"code":"faixa etária"}, errors="raise", inplace=True)
		
		# Primeiro, soma total de weight por influencer
		total_weight_por_influencer = df_unido.groupby("influencer")["weight"].transform("sum")
		
		# Depois, soma de weight por influencer + cidade
		total_weight_por_cidade = df_unido.groupby(["influencer", "Cidade"])["weight"].transform("sum")
		
		# Agora, atribuímos o weight normalizado (valor da cidade dividido pela soma total do influencer)
		df_unido["weight_normalized"] = total_weight_por_cidade / total_weight_por_influencer
		
		# Normalizar os pesos dos gêneros
		df_unido["male_weighted"] = df_unido["male"] * df_unido["weight_normalized"]
		df_unido["female_weighted"] = df_unido["female"] * df_unido["weight_normalized"]
		
		# Verificar o dataframe
		df_unido.rename(columns={"faixa etária":"Grupo Etário", "male":"Proporção Male", "female":"Proporção Female"}, inplace=True)
		
		# Unir com educação
		df_unido_edu = df_unido.merge(educacao_por_cidade, on=["Cidade", "Grupo Etário"], how="left")
		df_unido_edu.drop(columns=["Unnamed: 0"], inplace=True)
		
		# Construir anos_female e anos_male
		df_unido_edu["anos_female"] = df_unido_edu["female_weighted"] * df_unido_edu["female"]
		df_unido_edu["anos_male"] = df_unido_edu["male_weighted"] * df_unido_edu["male"]
		
		# Consolidar a média de anos de estudo, por influenciador
		df_unido_edu.groupby("influencer")[["anos_female", "anos_male"]].sum().sum(axis=1)
		
		# Agrupar e somar anos de educação (feminino + masculino)
		total_anos_por_influencer = df_unido_edu.groupby("influencer")[["anos_female", "anos_male"]].sum().sum(axis=1)
		
		# Criar distribuição normal para os anos de educação
		std_dev = 3
		samples = 1000
		
		# Lista para armazenar os dados
		data = []
		
		# Iterar sobre os valores
		for influencer, total_anos in total_anos_por_influencer.items():
		    mean = total_anos  # Ajuste se necessário
		    std_dev = std_dev       # Defina o desvio padrão
		
		    prob_less_5 = norm.cdf(5, mean, std_dev)
		    prob_5_9 = norm.cdf(9, mean, std_dev) - norm.cdf(5, mean, std_dev)
		    prob_9_12 = norm.cdf(12, mean, std_dev) - norm.cdf(9, mean, std_dev)
		    prob_more_12 = 1 - norm.cdf(12, mean, std_dev)
		
		    # Adicionar ao dataset
		    data.append({
		        "Influencer": influencer,
		        "< 5 anos": prob_less_5,
		        "5-9 anos": prob_5_9,
		        "9-12 anos": prob_9_12,
		        "> 12 anos": prob_more_12
		    })
		
		# Criar DataFrame
		result_edu = pd.DataFrame(data)
		
		# Adicionar coluna de distribuição formatada
		result_edu["distribuicao_formatada"] = result_edu.apply(
		    lambda row: f"< 5 anos: {row['< 5 anos']:.2%},  \n"
		                f"5-9 anos: {row['5-9 anos']:.2%},  \n"
		                f"9-12 anos: {row['9-12 anos']:.2%},  \n"
		                f"acima de 12 anos: {row['> 12 anos']:.2%}",
		    axis=1
		)
		
		# Trocar ponto por vírgula na formatação percentual
		result_edu["distribuicao_formatada"] = result_edu["distribuicao_formatada"].str.replace('.', ',', regex=False)
		escolaridade_dict = result_edu.set_index('Influencer')['distribuicao_formatada'].to_dict()
	
		st.session_state["escolaridade_dict"] = escolaridade_dict
	
		############ Dispersão ############
		# Inicializar um dicionário para armazenar os resultados
		dispersao_influencers = {}
		
		# Criar um for para obter os dados para cada influencer
		for influencer in dados_brutos.keys():
			try:
		        # Reiniciar listas
				likes = []
				comments = []
		        
		        # Obter os dados
				recent_posts = dados_brutos.get(influencer)["user_profile"]["recent_posts"]
				df_temp = pd.json_normalize(recent_posts)
		
		        # Append os valores de likes e comments às listas
				for i in range(df_temp.shape[0]):
					comments.append(df_temp.loc[i, "stat.comments"])
					try:
						likes.append(df_temp.loc[i, "stat.likes"])
					except:
						continue
		
		        # Garante que valores sejam inteiros, ou 0 se vazios
				likes = [int(like) if not (like is None or np.isnan(like)) else 0 for like in likes]
				comments = [int(comment) if not (comment is None or np.isnan(comment)) else 0 for comment in comments]
		
		        # Calcular dispersão apenas se houver dados válidos
				if len(likes) == 0 and len(comments) == 0:
					raise ValueError("Sem dados de likes nem comments")
		
		        # Inicializar variáveis
				media_likes = media_comments = 0
				desvpad_normalizado_likes = desvpad_normalizado_comments = 0
		
				if len(likes) > 0 and np.sum(likes) > 0:
					media_likes = np.mean(likes)
					desvpad_likes = np.std(likes)
					desvpad_normalizado_likes = (desvpad_likes / media_likes) * 100 if media_likes != 0 else 0
		
				if len(comments) > 0 and np.sum(comments) > 0:
					media_comments = np.mean(comments)
					desvpad_comments = np.std(comments)
					desvpad_normalizado_comments = (desvpad_comments / media_comments) * 100 if media_comments != 0 else 0
		
		        # Adicionar ao dicionário
				if desvpad_normalizado_likes > 0:
					dispersao_influencers[influencer] = round((desvpad_normalizado_comments + desvpad_normalizado_likes) / 2, 0)
				else:
					dispersao_influencers[influencer] = round(desvpad_normalizado_comments, 0)
		
			except Exception as e:
				print(f"Sem registros para '{influencer}': {e}")
		
		df_dispersao = pd.DataFrame.from_dict(dispersao_influencers, orient="index").reset_index()
		df_dispersao.rename(columns={"index":"Influencer", 0:"Dispersão"}, inplace=True)
		df_dispersao["Dispersão"] = df_dispersao["Dispersão"].astype(int)
	
		st.session_state["dispersao_influencers"] = dispersao_influencers
		st.session_state["df_dispersao"] = df_dispersao
	
		############ Interesses ############
		# Consolidar interesses
		df_interesses = pd.DataFrame()
		
		for influencer in dados_brutos.keys():
			try:
				audience_interests = dados_brutos[influencer]["audience_followers"]["data"]["audience_interests"]
				df_temp = pd.json_normalize(audience_interests)
				df_temp["influencer"] = influencer
				df_interesses = pd.concat([df_interesses, df_temp])
			except Exception as e:
				print(e)
	
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
	
		# Traduzir o interesse
		df_interesses["name"] = df_interesses["name"].replace(interests_translation)
		df_interesses["weight"] = df_interesses["weight"] * 100
	
		# Para cada influenciador, obter os top 5 interesses formatados
		def format_top_interests(group):
			top5 = group.nlargest(5, "weight").reset_index(drop=True)
			lines = []
			for i, row in top5.iterrows():
			# Formata com vírgula decimal
				formatted_weight = f"{row['weight']:.2f}".replace(".", ",")
	        # Adiciona vírgula ao final se não for o último item
				suffix = "," if i < len(top5) - 1 else ""
				lines.append(f"{row['name']} ({formatted_weight}%){suffix}")
			return "  \n".join(lines)
	
		# Aplica a função a cada grupo
		result_interesses = df_interesses.groupby("influencer").apply(format_top_interests).reset_index()
		
		# Renomeia a coluna com os resultados
		result_interesses.columns = ["influencer", "top_interesses"]
		st.session_state["result_interesses"] = result_interesses
		
		# Converter em dicionário
		interesses_dict = result_interesses.set_index('influencer')['top_interesses'].to_dict()
		st.session_state["interesses_dict"] = interesses_dict
	
		############ Outros dados ############
		nomes_influenciadores = {}
		score_audiencia_influenciadores = {}
		alcance_medio_influenciadores = {}
	
		for influencer in dados_brutos.keys():
	    # Encontrar nome do influenciador
			try:
				nomes_influenciadores[influencer] = dados_brutos[influencer]["user_profile"]["fullname"]
			except:
				nomes_influenciadores[influencer] = influencer
				print("Não foi possível encontrar o nome do influenciador {}".format(influencer))
	
			st.session_state["nomes_influenciadores"] = nomes_influenciadores
		
		    # Encontrar credibilidade da audiência
			try:
				score[influencer] = dados_brutos[influencer]["audience_followers"]["data"]["audience_credibility"]
				if score[influencer] == 0:
					score[influencer] = score[influencer].str.replace("0", "N/A")
				else:
					score_audiencia_influenciadores[influencer] = int(score * 100)
			except:
				score_audiencia_influenciadores["influencer"] = "N/A"
				print("Não foi possível encontrar a credibilidade da audiência do influenciador {}".format(influencer))
		
			st.session_state["score_audiencia_influenciadores"] = score_audiencia_influenciadores
		
		    # Encontrar e formatar média de Plays em Reels
			try:
			    # Primeira hipótese
			    valor = dados_brutos[influencer]["user_profile"]["avg_reels_plays"]
			except KeyError:
			    try:
			        # Segunda hipótese
			        valor = dados_brutos[influencer]["user_profile"]["avg_views"]
			    except KeyError:
			        valor = None
			
			if valor is not None:
			    alcance_medio_influenciadores[influencer] = f"{valor:,}".replace(",", ".")
			else:
			    alcance_medio_influenciadores[influencer] = "N/A"
			    print("Não foi possível encontrar o alcance do influenciador {}".format(influencer))
		
			st.session_state["alcance_medio_influenciadores"] = alcance_medio_influenciadores
	
		############ Consolidar o DF final ############
		# Lista para armazenar os dados de cada influenciador
		resumo_influenciadores = []
		
		for influencer in dados_brutos.keys():
			resumo_influenciadores.append({
				"Username do influenciador": influencer,
				"Nome do influenciador": nomes_influenciadores.get(influencer),
				"Score da audiência": int(score_audiencia_influenciadores.get(influencer, 0)),
				"Dispersão de interações": int(dispersao_influencers.get(influencer, 0)),
				"Alcance médio esperado": alcance_medio_influenciadores.get(influencer),
				"Interesses da audiência": interesses_dict.get(influencer),
				"Classes sociais": classes_sociais_dict.get(influencer),
				"Escolaridade": escolaridade_dict.get(influencer),
			})
		
		# Criar o DataFrame
		df_resumo = pd.DataFrame(resumo_influenciadores)
		st.session_state["df_resumo"] = df_resumo

		st.markdown("## Consolidação de dados para os influenciadores 👨‍💻\n \n")
		st.table(df_resumo)

		if not df_resumo.empty:			
			agora = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
			file_name = "resumo_defesa_influenciadores_{}.xlsx".format(agora)
			output = io.BytesIO()
			with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
				df_resumo.to_excel(writer, index=False, sheet_name='Defesa Influenciadores')
			output.seek(0)
			st.download_button(label="📥 Baixar o resumo em formato .xlsx",
							  data=output,
							  file_name=file_name,
							  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
	else:
		st.warning("Por favor, faça o upload de arquivos JSON válidos na primeira aba")


with abas[2]:
	def exibir_cards_de_posts(lista_posts):
		for row_start in range(0, len(lista_posts), 3):
			cols = st.columns(3)
			for i in range(3):
				if row_start + i >= len(lista_posts):
					break
				post = lista_posts[row_start + i]
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
	
					st.markdown(f"**{post.get('text', '')}**")
	
					stat = post.get("stat", {})
					st.markdown(f"👍 Likes: **{stat.get('likes', 0)}**")
					st.markdown(f"💬 Comentários: **{stat.get('comments', 0)}**")
					st.markdown(f"🔁 Compartilhamentos: **{stat.get('shares', 0)}**")

	def exibir_posts(influencer, dados_brutos):
		recent_posts = dados_brutos[influencer]["user_profile"]["recent_posts"]
		
		try:
			commercial_posts = dados_brutos[influencer]["user_profile"]["commercial_posts"]

			likes_posts = []
			comments_posts = []
			shares_posts = []
			marcas_posts = []
		
			for post in commercial_posts:
				stat = post.get("stat", {})
				likes_posts.append(stat.get("likes", 0))
				comments_posts.append(stat.get("comments", 0))
				shares_posts.append(stat.get("shares", 0))
				
				sponsor = post.get("sponsor", {})
				marca = sponsor.get("usename")
				if marca:
					marcas_posts.append(marca)
		    
		    # Cálculos - Posts comerciais
			likes_total_comercial = np.sum(likes_posts) if likes_posts else 0
			comments_total_comercial = np.sum(comments_posts) if comments_posts else 0
			shares_total_comercial = np.sum(shares_posts) if shares_posts else 0
			marcas_posts = np.unique(marcas_posts)
		
		    # Subtítulo
			st.markdown("### Posts comerciais:")
		
		    # Mostrar métricas
			st.markdown("### Métricas das publicações identificadas na amostra:")
			col1, col2, col3 = st.columns(3)
			with col1:
				st.metric("👍 Média de Likes", f"{int(likes_total_comercial):,}".replace(",", "."))
			with col2:
				st.metric("💬 Média de Comentários", f"{int(comments_total_comercial):,}".replace(",", "."))
			with col3:
				st.metric("🔁 Média de Shares", f"{int(shares_total_comercial):,}".replace(",", "."))
		
			exibir_cards_de_posts(commercial_posts)
			
		except:
			st.warning("Não há posts comerciais identificados para o influenciador {}".format(influencer))
	    
		likes_posts = []
		comments_posts = []
		shares_posts = []
	
		for post in recent_posts:
			stat = post.get("stat", {})
			likes_posts.append(stat.get("likes", 0))
			comments_posts.append(stat.get("comments", 0))
			shares_posts.append(stat.get("shares", 0))
	    
	    # Cálculos - Posts recentes
		likes_total_recentes = np.sum(likes_posts) if likes_posts else 0
		comments_total_recentes = np.sum(comments_posts) if comments_posts else 0
		shares_total_recentes = np.sum(shares_posts) if shares_posts else 0
	
	    # Subtítulo
		st.markdown("\n\n### Posts recentes:")
	
	    # Mostrar métricas
		st.markdown("### Métricas das publicações identificadas na amostra:")
		col1, col2, col3 = st.columns(3)
		with col1:
			st.metric("👍 Média de Likes", f"{int(likes_total_recentes):,}".replace(",", "."))
		with col2:
			st.metric("💬 Média de Comentários", f"{int(comments_total_recentes):,}".replace(",", "."))
		with col3:
			st.metric("🔁 Média de Shares", f"{int(shares_total_recentes):,}".replace(",", "."))
	
		exibir_cards_de_posts(recent_posts)

	if uploaded_files:
		dados_brutos = st.session_state["dados_brutos"]
		nomes_influenciadores = st.session_state["nomes_influenciadores"]
		
		influenciador_selecionado = st.selectbox(
				"Influenciador:", 
				nomes_influenciadores, 
				key="select_influencer_posts"
		)
	    
		if influenciador_selecionado:
			exibir_posts(
				influencer=influenciador_selecionado,
				dados_brutos=st.session_state["dados_brutos"]
			)
	
	else:
		st.warning("Por favor, faça o upload de arquivos JSON válidos na primeira aba")












