from flask import Blueprint, request, jsonify
from shared import _spotify_get_token
import requests

# Definición del Blueprint para Playlists
playlists_bp = Blueprint('playlists', __name__, url_prefix='/playlists')

# ----------------------------------------------------
# 1. GET /playlists/search?q=<query> (Buscar Playlist)
# ----------------------------------------------------
@playlists_bp.route('/search', methods=['GET'])
def spotify_search_playlist():
    """
    Busca playlists en Spotify y mapea al formato de la App.
    Nota: Este archivo no requiere guardar nada en MySQL, 
    solo consulta la API externa.
    """
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "Parámetro 'q' requerido"}), 400

    token = _spotify_get_token()
    if not token:
        return jsonify({"error": "Token de Spotify no disponible"}), 500

    try:
        # Nota: Asegúrate que la URL de Spotify en tu código original sea la correcta
        # (Cambié la URL de ejemplo 'googleusercontent' por la real de Spotify API)
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": q, "type": "playlist", "limit": 5},
            timeout=10,
        )
    except Exception as e:
        return jsonify({"error": "Error de red con Spotify", "details": str(e)}), 503

    if resp.status_code != 200:
        return jsonify({"error": "Spotify API Error", "details": resp.text}), 502

    spotify_data = resp.json()
    mapped_playlists = []
    
    spotify_items = spotify_data.get('playlists', {}).get('items', [])
    
    for item in spotify_items:
        if item is None: continue
            
        image_url = item.get('images')[0].get('url', "") if item.get('images') else ""
        external_url = item.get('external_urls', {}).get('spotify', "")
        
        mapped_playlists.append({
            "id": item.get('id'),
            "name": item.get('name'),
            "image_url": image_url, 
            "tracks_count": item.get('tracks', {}).get('total', 0), 
            "external_url": external_url 
        })

    return jsonify({"playlists": mapped_playlists}), 200
