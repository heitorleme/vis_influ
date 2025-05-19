import pandas as pd
import numpy as np
import streamlit as st
import json

# Upload de múltiplos arquivos JSON
uploaded_files = st.file_uploader("Carregue os arquivos JSON dos influencers", type="json", accept_multiple_files=True)


# Inicialização
influencers = []
influencers_ficheiros = {}

if uploaded_files:
    for file in uploaded_files:
        filename = file.name
        partes = filename.split("_")
        if len(partes) > 1:
            influencer = partes[1][:-5]  # Remove .json
            influencers.append(influencer)
            influencers_ficheiros[influencer] = file
        else:
            st.warning(f"O arquivo '{filename}' não segue o padrão esperado.")

    # Seleção do número de registros por influencer
    top_n = st.selectbox("Quantas cidades deseja exibir por influencer?", [5, 10, 15, 20], index=0)

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

        # Mostrar tabela original
        st.subheader("Cidades por Influencer")
        st.dataframe(df_cidades)

        # Ordenar e selecionar as N cidades com maiores pesos por influencer
        result = df_cidades.sort_values(by=["influencer", "weight"], ascending=[True, False])\
                           .groupby("influencer")\
                           .head(top_n)

        # Reformatar para tabela pivot
        result["rank"] = result.groupby("influencer").cumcount() + 1
        pivot_df = result.pivot(index="influencer", columns="rank", values=["Cidade", "weight"])
        pivot_df.columns = [f"{col[0]} #{col[1]}" for col in pivot_df.columns]
        pivot_df.reset_index(inplace=True)

        # Mostrar tabela reformulada
        st.subheader(f"Top {top_n} Cidades por Influencer (ordenadas por peso)")
        st.dataframe(pivot_df)
    else:
        st.info("Nenhum dado de cidades encontrado nos arquivos.")
else:
    st.info("Por favor, carregue arquivos JSON para começar.")
