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
	ficheiros = []
	
	if uploaded_files:
		for file in uploaded_files:
			if "desktop.ini" in file:
				continue
			else:
				ficheiros.append(file)
				partes = file.split("_")
				if len(partes) > 1:  # Verifica se há pelo menos dois elementos após o split
					influencers.append(partes[1][:-5])
				else:
					print(f"Aviso: O arquivo '{file}' não segue o padrão esperado.")
		influencers_ficheiros = dict(zip(influencers, ficheiros))
		st.session_state["influencers_ficheiros"] = influencers_ficheiros

		dados_brutos = {}

		for influencer, arquivo_json in influencer_ficheiros.items():
			try:
				with open(arquivo_json, "r", encoding="utf-8") as arquivo:
					dados_brutos[influencer] = json.load(arquivo)
			except:
				print("Erro ao processar o arquivo para o influenciador {}".format(influencer))
		st.session_state["dados_brutos"] = dados_brutos
		
	else:
		st.info("Por favor, carregue arquivos JSON para começar.")
