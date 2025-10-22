#!/usr/bin/env python3
"""
Script de veille immobilière Genève
- Charge un JSON de nouvelles annonces
- Fusionne avec les anciennes
- Déduplique
- Trie et exporte
- Push vers GitHub/Netlify
"""

import json
import subprocess
from datetime import datetime
from collections import OrderedDict

def load_json(filename):
    """Charge un fichier JSON"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_json(data, filename):
    """Sauvegarde en JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Sauvegardé : {filename}")

def deduplicate(annonces):
    """Déduplique par adresse (garde ImmoScout24 en priorité)"""
    seen = {}
    for ann in sorted(annonces, key=lambda x: x.get('Portail') == 'ImmoScout24', reverse=True):
        addr = ann.get('Adresse', '').lower().strip()
        if addr not in seen:
            seen[addr] = ann
    return list(seen.values())

def sort_annonces(annonces):
    """Trie par loyer, puis surface"""
    return sorted(annonces, key=lambda x: (float(x.get('Loyer', 0)), float(x.get('Surface', 0))))

def merge_new_with_old(new_file, old_file='data.json'):
    """Fusionne nouvelles annonces avec les anciennes"""
    old = load_json(old_file)
    new = load_json(new_file)
    
    # Fusionne
    merged = old + new
    
    # Déduplique + trie
    merged = deduplicate(merged)
    merged = sort_annonces(merged)
    
    return merged

def export_to_csv(annonces, filename='data.csv'):
    """Exporte en CSV"""
    if not annonces:
        return
    
    import csv
    headers = list(annonces[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(annonces)
    
    print(f"✅ CSV exporté : {filename}")

def git_push():
    """Push vers GitHub automatiquement"""
    try:
        subprocess.run(['git', 'add', 'data.json', 'data.csv'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Auto: veille immobilière {datetime.now().strftime("%Y-%m-%d")}'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Pushé vers GitHub")
    except Exception as e:
        print(f"⚠️ Erreur Git : {e}")

def main():
    print("=" * 80)
    print("🏠 VEILLE IMMOBILIÈRE GENÈVE - Traitement Données")
    print("=" * 80)
    
    # 1. Fusion nouvelles + anciennes
    print("\n1️⃣ Fusion données...")
    merged = merge_new_with_old('new_data.json', 'data.json')
    print(f"   Total après fusion : {len(merged)} annonces")
    
    # 2. Sauvegarde
    print("\n2️⃣ Sauvegarde...")
    save_json(merged, 'data.json')
    export_to_csv(merged, 'data.csv')
    
    # 3. Statistiques
    print("\n3️⃣ Statistiques...")
    if merged:
        loyers = [float(a.get('Loyer', 0)) for a in merged]
        print(f"   Loyer min : CHF {min(loyers):.0f}")
        print(f"   Loyer max : CHF {max(loyers):.0f}")
        print(f"   Loyer moy : CHF {sum(loyers)/len(loyers):.0f}")
    
    # 4. Push GitHub
    print("\n4️⃣ Push vers GitHub...")
    git_push()
    
    print("\n" + "=" * 80)
    print("✅ VEILLE TERMINÉE - Netlify redéploiera automatiquement!")
    print("=" * 80)

if __name__ == '__main__':
    main()
