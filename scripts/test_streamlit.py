#!/usr/bin/env python3
"""
Test simple pour vérifier que Streamlit fonctionne
"""

import streamlit as st
import sys
import os

def main():
    st.title("🔧 Test Streamlit")
    st.success("✅ Streamlit fonctionne correctement!")
    
    st.subheader("Informations système")
    st.write(f"**Python version:** {sys.version}")
    st.write(f"**Streamlit version:** {st.__version__}")
    st.write(f"**Répertoire actuel:** {os.getcwd()}")
    
    st.subheader("Test des dépendances")
    
    try:
        import firebase_admin
        st.success("✅ Firebase Admin SDK disponible")
    except ImportError:
        st.error("❌ Firebase Admin SDK manquant")
    
    try:
        import pandas
        st.success("✅ Pandas disponible")
    except ImportError:
        st.error("❌ Pandas manquant")
    
    try:
        from PIL import Image
        st.success("✅ Pillow disponible")
    except ImportError:
        st.error("❌ Pillow manquant")
    
    st.subheader("Test Firebase Credentials")
    firebase_paths = [
        '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json',
        '/Users/arnaudkossea/development/kumacodex/firebase-credentials.json'
    ]
    
    found = False
    for path in firebase_paths:
        if os.path.exists(path):
            st.success(f"✅ Credentials trouvés: {path}")
            found = True
            break
    
    if not found:
        st.warning("⚠️ Aucun fichier de credentials Firebase trouvé")
    
    st.markdown("---")
    st.info("🎭 Si ce test fonctionne, le backoffice Kuma devrait fonctionner aussi!")

if __name__ == "__main__":
    main()