import streamlit as st
import streamlit as st

import pandas as pd
import geopandas as gpd

import plotly.express as px

import folium
from folium import Marker
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from streamlit_folium import folium_static

import math 
st.set_page_config(layout='wide')

# Carga de datos
archivo_registros_presencia = st.sidebar.file_uploader('Seleccione un archivo CSV que siga el estándar DwC')

# Se continúa con el procesamiento solo si hay un archivo de datos cargado
if archivo_registros_presencia is not None:
    # Carga de registros de presencia en un dataframe
    registros_presencia = pd.read_csv(archivo_registros_presencia, delimiter='\t')
    # Conversión del dataframe de registros de presencia a geodataframe
    registros_presencia = gpd.GeoDataFrame(registros_presencia, 
                                           geometry=gpd.points_from_xy(registros_presencia.decimalLongitude, 
                                                                       registros_presencia.decimalLatitude),
                                           crs='EPSG:4326')
                                
    
    # Carga de polígonos de cantones
    cantones = gpd.read_file("cantones.geojson")

   

    # Limpieza de datos
    # Eliminación de registros con valores nulos en la columna 'species'
    registros_presencia = registros_presencia[registros_presencia['species'].notna()]
   


    # Especificación de filtros
    # Especie
    lista_especies = registros_presencia.species.unique().tolist()
    lista_especies.sort()
    filtro_especie = st.sidebar.selectbox('Seleccione la especie', lista_especies)



     # Tabla de registros de presencia
    st.header('Registros de presencia')
    st.dataframe(registros_presencia[['family', 'species', 'eventDate', 'locality']].rename(columns = {'family':'Familia', 'species':'Especie', 'eventDate':'Fecha', 'locality':'Localidad'}))
 
   # Filtrado
    registros_presencia = registros_presencia[registros_presencia['species'] == filtro_especie]
  # Cálculo de la cantidad de registros en canton
    # "Join" espacial de las capas de ASP y registros de presencia
    cantones_contienen_registros = cantones.sjoin(registros_presencia, how="left", predicate="contains")
    # Conteo de registros de presencia en cada canton
    cantones_registros = cantones_contienen_registros.groupby("CODNUM").agg(cantidad_registros_presencia = ("gbifID","count"))
    cantones_registros = cantones_registros.reset_index() # para convertir la serie a dataframe


     # "Join" para agregar la columna con el conteo a la capa de canton
    cantones_registros = cantones_registros.join(cantones.set_index('CODNUM'), on='CODNUM', rsuffix='_b')
    # Dataframe filtrado para usar en graficación
    cantones_registros_grafico = cantones_registros.loc[cantones_registros['cantidad_registros_presencia'] > 0, 
                                                            ["provincia", "cantidad_registros_presencia"]].sort_values("cantidad_registros_presencia", ascending=[False]).head(15)
    cantones_registros_grafico = cantones_registros_grafico.set_index('provincia')  


   
    st.header('Registros por provincia')

    fig = px.bar(cantones_registros_grafico, 
                    labels={'provincia':'Provincia', 'cantidad_registros_presencia':'Registros de presencia'})
    st.plotly_chart(fig)  
    
         # "Join" para agregar la columna con el conteo a la capa de canton
    cantones_registros = cantones_registros.join(cantones.set_index('CODNUM'), on='CODNUM', rsuffix='_b')
    # Dataframe filtrado para usar en graficación
    cantones_registros_grafico = cantones_registros.loc[cantones_registros['cantidad_registros_presencia'] > 0, 
                                                            ["NCANTON", "cantidad_registros_presencia"]].sort_values("cantidad_registros_presencia", ascending=[False]).head(15)
    cantones_registros_grafico = cantones_registros_grafico.set_index('NCANTON')  

    st.header('Registros por canton')
        
    fig = px.bar(cantones_registros_grafico, 
                    labels={'NCANTON':'Cantón', 'cantidad_registros_presencia':'Registros de presencia'})
    st.plotly_chart(fig)  



# Mapa de coropletas de registros de presencia en cantones
    st.header('Mapa de cantidad de registros en cantones')

        # Capa base
    m = folium.Map(location=[9.6, -84.2], tiles='CartoDB positron', zoom_start=8)
    folium.TileLayer(
    tiles='Stamen Terrain', 
    name='Stamen Terrain').add_to(m)
        # Capa de coropletas
    folium.Choropleth(
            name="Cantidad de registros en Cantones",
            geo_data=cantones,
            data=cantones_registros,
            columns=['CODNUM', 'cantidad_registros_presencia'],
            bins=8,
            key_on='feature.properties.CODNUM',
            fill_color='Reds', 
            fill_opacity=0.5, 
            line_opacity=1,
            legend_name='Cantidad de registros de presencia',
            smooth_factor=0).add_to(m)
       # Adición de puntos agrupados
    mc = MarkerCluster()

    cantones_contienen_registros["popup"] = cantones_contienen_registros["species"] + " " + cantones_contienen_registros["stateProvince"]+ " " + cantones_contienen_registros["NCANTON"]+ " " + cantones_contienen_registros["eventDate"] 
    for idx, row in cantones_contienen_registros.iterrows():
        if not math.isnan(row['decimalLongitude']) and not math.isnan(row['decimalLatitude']):
         
            mc.add_child(Marker([row['decimalLatitude'], row['decimalLongitude']], popup=row['popup'])).add_to(m)
    m.add_child(mc)
        # Control de capas
    folium.LayerControl().add_to(m)        
        # Despliegue del mapa
    folium_static(m)   

    