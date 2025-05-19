import pandas as pd
import numpy as np
import streamlit as st
import json
import io
from datetime import datetime

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
        df_cidades_exibicao = df_cidades.copy()
        df_cidades_exibicao.drop(columns=["id", "coords.lat", "coords.lon", "country.id", "country.code", "state.id", "state.name"], inplace=True)
        
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
else:
    st.info("Por favor, carregue arquivos JSON para começar.")
