import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# --- Configuration de la page ---
st.set_page_config(page_title="IRAT - Résilience Agricole Togo", layout="wide")

# --- Chargement des données (mis en cache pour aller plus vite) ---
@st.cache_data
def charger_donnees():
    df = pd.read_csv("data/irat_final.csv")
    geo = gpd.read_file("data/irat_cantons.geojson")
    return df, geo

df, geo = charger_donnees()

# --- Titre ---
st.title("🌾 IRAT — Indice de Résilience Agricole Territoriale")
st.caption("Dashboard interactif — infrastructures agricoles du Togo")

# --- Barre latérale : filtres ---
st.sidebar.header("Filtres")
regions = st.sidebar.multiselect(
    "Région(s)", options=df['region'].unique(), default=df['region'].unique()
)
df_filtre = df[df['region'].isin(regions)]

# --- KPI en haut de page ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cantons analysés", len(df_filtre))
#col2.metric("Distance médiane abattoir", f"{df_filtre['distance_abattoir_km'].median():.1f} km")
col3.metric("Cantons vulnérables", (df_filtre['IRAT'] < 25).sum())
col4.metric("IRAT moyen", f"{df_filtre['IRAT'].mean():.1f}")

st.divider()

# --- Deux colonnes : carte + graphique ---
col_carte, col_graph = st.columns([1.3, 1])

with col_carte:
    st.subheader("Carte des cantons")
    geo_filtre = geo[geo['canton'].isin(df_filtre['canton'])]
    
    centre = geo_filtre.total_bounds
    m = folium.Map(location=[(centre[1]+centre[3])/2, (centre[0]+centre[2])/2], zoom_start=7)
    
    folium.Choropleth(
        geo_data=geo_filtre,
        data=geo_filtre,
        columns=['canton', 'IRAT'],
        key_on='feature.properties.canton',
        fill_color='RdYlGn',
        fill_opacity=0.7,
        legend_name='Score IRAT'
    ).add_to(m)
    
   # st_folium(m, width=700, height=450)

with col_graph:
    st.subheader("Répartition par statut")
    repartition = df_filtre['statut'].value_counts().reset_index()
    repartition.columns = ['statut', 'nombre']
    
    fig = px.pie(
        repartition, values='nombre', names='statut', hole=0.4,
        color='statut',
        color_discrete_map={'Vulnérable': '#C62828', 'Intermédiaire': '#F9A825', 'Résilient': '#2E7D32'}
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Tableaux top 10 ---
tab1, tab2, tab3 = st.tabs(["🏆 Top 10 résilients", "⚠️ Top 10 vulnérables", "💰 Top 10 investissement"])

with tab1:
    st.dataframe(
        df_filtre.nlargest(10, 'IRAT')[['canton', 'prefecture', 'region', 'IRAT']],
        use_container_width=True, hide_index=True
    )

with tab2:
    st.dataframe(
        df_filtre.nsmallest(10, 'IRAT')[['canton', 'prefecture', 'region', 'IRAT']],
        use_container_width=True, hide_index=True
    )

with tab3:
    df_filtre['nb_infra_total'] = (df_filtre['nb_eau'] + df_filtre['nb_elevage'] + 
                                     df_filtre['nb_pisciculture'] + df_filtre['nb_abattoir'])
    candidats = df_filtre[df_filtre['nb_infra_total'] > 0].copy()
    candidats['score_priorite'] = 100 - candidats['IRAT']
    st.dataframe(
        candidats.nlargest(10, 'score_priorite')[['canton', 'prefecture', 'region', 'IRAT', 'nb_infra_total']],
        use_container_width=True, hide_index=True
    )