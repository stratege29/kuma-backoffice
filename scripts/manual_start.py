#!/usr/bin/env python3
"""
Démarrage manuel avec diagnostic complet
"""

import subprocess
import sys
import os
import time

def run_command_with_output(cmd, description):
    """Execute une commande et affiche le résultat"""
    print(f"\n🔧 {description}")
    print(f"💻 Commande: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Code de retour: {result.returncode}")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - commande trop longue")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🎭 Diagnostic Streamlit Kuma")
    print("=" * 50)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    simple_test = os.path.join(script_dir, 'simple_test.py')
    
    # Test 1: Version Python
    run_command_with_output([sys.executable, '--version'], "Version Python")
    
    # Test 2: Streamlit version
    run_command_with_output([sys.executable, '-m', 'streamlit', 'version'], "Version Streamlit")
    
    # Test 3: Test config Streamlit
    run_command_with_output([sys.executable, '-m', 'streamlit', 'config', 'show'], "Configuration Streamlit")
    
    # Test 4: Ports en écoute
    try:
        import socket
        for port in [8501, 8502, 8503]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                print(f"⚠️ Port {port} déjà utilisé")
            else:
                print(f"✅ Port {port} libre")
            sock.close()
    except Exception as e:
        print(f"❌ Erreur test ports: {e}")
    
    print("\n" + "=" * 50)
    print("🚀 Tentative de lancement Streamlit...")
    
    # Essai avec différents ports
    for port in [8504, 8505, 8506]:
        print(f"\n🔄 Essai sur port {port}")
        
        cmd = [
            sys.executable, '-m', 'streamlit', 'run',
            simple_test,
            '--server.port', str(port),
            '--server.address', '127.0.0.1',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false'
        ]
        
        print(f"💻 Commande: {' '.join(cmd)}")
        
        try:
            # Lancer en arrière-plan
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Attendre un peu
            time.sleep(5)
            
            # Vérifier si le processus fonctionne
            if process.poll() is None:
                print(f"✅ Streamlit semble démarré sur port {port}")
                print(f"🌐 Essayez d'ouvrir: http://localhost:{port}")
                
                # Garder le processus en vie
                print("⏰ Streamlit fonctionne... Appuyez sur Ctrl+C pour arrêter")
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 Arrêt par l'utilisateur")
                    process.terminate()
                    process.wait()
                break
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Streamlit a échoué sur port {port}")
                if stdout:
                    print("STDOUT:", stdout[:500])
                if stderr:
                    print("STDERR:", stderr[:500])
                    
        except Exception as e:
            print(f"❌ Erreur lancement port {port}: {e}")
    
    print("\n🏁 Diagnostic terminé")

if __name__ == "__main__":
    main()