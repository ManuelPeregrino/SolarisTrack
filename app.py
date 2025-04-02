import streamlit as st
from streamlit_folium import st_folium
import folium
import geocoder
import json

COORDS_FILE = "coords.json"

def save_coords(lat, lon):
    with open(COORDS_FILE, "w") as f:
        json.dump({"latitude": lat, "longitude": lon}, f)

def main():
    st.title("Mapa interactivo con coordenadas")
    
    # Obtener la ubicación del usuario
    g = geocoder.ip('me')
    user_location = g.latlng if g.ok else [19.4326, -99.1332]  # Default: CDMX
    
    # Crear un mapa centrado en la ubicación del usuario
    m = folium.Map(location=user_location, zoom_start=12)
    m.add_child(folium.LatLngPopup())
    
    # Mostrar el mapa en la app
    map_data = st_folium(m, height=500, width=700)
    
    # Mostrar coordenadas seleccionadas
    if map_data and map_data["last_clicked"]:
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.write(f"Coordenadas seleccionadas: {lat}, {lon}")
        
        # Guardar las coordenadas en un archivo JSON
        save_coords(lat, lon)

if __name__ == "__main__":
    main()
