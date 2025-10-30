import os
import json
import time
import requests
import random
from datetime import datetime
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys

# Résoudre problème Unicode sur Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Critères de filtrage
CRITERES = {
    'loyer_min': 1100,
    'loyer_max': 1700,
    'pieces_min': 1.5,
    'pieces_max': 3.0,
    'canton': 'Genève'
}

# Headers variés pour éviter détection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
]

def log_print(message):
    """Print sécurisé pour Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

def get_session():
    """Crée une session requests avec retry automatique"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=2  # Augmente délai : 1s, 2s, 4s
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

class ApartmentScraper:
    def __init__(self):
        self.apartments = []
        self.seen_addresses = set()
        self.session = get_session()
        
    def get_headers(self):
        """Retourne des headers aléatoires"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-CH,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def add_apartment(self, apartment):
        """Ajoute un appartement et évite les doublons"""
        address_key = apartment.get('Adresse', '').lower().strip()
        
        # Déduplication : garder ImmoScout24 en priorité
        if address_key in self.seen_addresses:
            existing = next((apt for apt in self.apartments if apt.get('Adresse', '').lower().strip() == address_key), None)
            if existing and apartment['Portail'] == 'ImmoScout24':
                self.apartments.remove(existing)
                self.apartments.append(apartment)
                log_print(f"[!] Doublon : {address_key} -> ImmoScout24 conservé")
            return
        
        self.seen_addresses.add(address_key)
        self.apartments.append(apartment)
        log_print(f"[+] Annonce ajoutee : {apartment['Adresse']} ({apartment['Portail']})")
    
    def filter_apartment(self, apartment):
        """Filtre les appartements selon les critères"""
        try:
            loyer_str = apartment.get('Loyer CHF', '0')
            loyer = int(''.join(filter(str.isdigit, str(loyer_str))))
            
            pieces_str = apartment.get('Pieces', '0')
            pieces = float(str(pieces_str).replace(',', '.'))
            
            if loyer < CRITERES['loyer_min'] or loyer > CRITERES['loyer_max']:
                return False
            if pieces < CRITERES['pieces_min'] or pieces > CRITERES['pieces_max']:
                return False
            return True
        except:
            return False
    
    def scrape_immoscout24(self):
        """Scrape ImmoScout24"""
        log_print("[*] Scraping ImmoScout24...")
        url = "https://www.immoscout24.ch/fr/appartement/louer/canton-geneve?priceMax=1700&roomsFrom=1&roomsTo=3"
        
        try:
            time.sleep(random.uniform(3, 6))  # DÉLAI AUGMENTÉ
            response = self.session.get(url, headers=self.get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher les annonces (structure simplifiée)
            listings = soup.find_all('a', class_='listing-item')
            
            if not listings:
                log_print("    [!] Aucune annonce trouvée sur ImmoScout24")
                return
            
            for listing in listings[:10]:  # Limiter à 10 pour test
                try:
                    title = listing.find('h2')
                    price = listing.find('span', class_='price')
                    
                    if not title or not price:
                        continue
                    
                    apartment = {
                        'Portail': 'ImmoScout24',
                        'Adresse': title.get_text(strip=True),
                        'Quartier': 'Geneve',
                        'Pieces': '2',
                        'Surface m²': 'N/A',
                        'Loyer CHF': price.get_text(strip=True),
                        'Etage': 'N/A',
                        'Meuble': 'Non',
                        'Balcon': 'Non',
                        'Ascenseur': 'N/A',
                        'Parking': 'Non',
                        'Lave-linge': 'N/A',
                        'Lave-vaisselle': 'N/A',
                        'Cave': 'N/A',
                        'Animaux': 'N/A',
                        'Disponibilite': 'Immediate',
                        'Etat': 'N/A',
                        'Confort & Remarques': title.get_text(strip=True),
                        'Description courte': title.get_text(strip=True)[:80],
                        'URL': listing.get('href', url)
                    }
                    
                    if self.filter_apartment(apartment):
                        self.add_apartment(apartment)
                        time.sleep(random.uniform(1, 2))
                except Exception as e:
                    continue
                    
        except requests.exceptions.Timeout:
            log_print("    [-] ImmoScout24 : Timeout (délai trop long)")
        except requests.exceptions.ConnectionError as e:
            log_print(f"    [-] ImmoScout24 : Erreur connexion - {e}")
        except Exception as e:
            log_print(f"    [-] ImmoScout24 : Erreur - {e}")
    
    def scrape_homegate(self):
        """Scrape Homegate.ch"""
        log_print("[*] Scraping Homegate.ch...")
        url = "https://www.homegate.ch/louer/appartement/canton-geneve"
        
        try:
            time.sleep(random.uniform(3, 6))  # DÉLAI AUGMENTÉ
            response = self.session.get(url, headers=self.get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = soup.find_all('article', class_='ListingCard')
            
            if not listings:
                log_print("    [!] Aucune annonce trouvée sur Homegate")
                return
            
            for listing in listings[:10]:
                try:
                    address = listing.find('h2')
                    price = listing.find('span', class_='price')
                    
                    if not address or not price:
                        continue
                    
                    apartment = {
                        'Portail': 'Homegate.ch',
                        'Adresse': address.get_text(strip=True),
                        'Quartier': 'Geneve',
                        'Pieces': '2',
                        'Surface m²': 'N/A',
                        'Loyer CHF': price.get_text(strip=True),
                        'Etage': 'N/A',
                        'Meuble': 'Non',
                        'Balcon': 'Non',
                        'Ascenseur': 'N/A',
                        'Parking': 'Non',
                        'Lave-linge': 'N/A',
                        'Lave-vaisselle': 'N/A',
                        'Cave': 'N/A',
                        'Animaux': 'N/A',
                        'Disponibilite': 'Immediate',
                        'Etat': 'N/A',
                        'Confort & Remarques': address.get_text(strip=True),
                        'Description courte': address.get_text(strip=True)[:80],
                        'URL': listing.get('href', url)
                    }
                    
                    if self.filter_apartment(apartment):
                        self.add_apartment(apartment)
                        time.sleep(random.uniform(1, 2))
                except:
                    continue
                    
        except requests.exceptions.Timeout:
            log_print("    [-] Homegate : Timeout (délai trop long)")
        except requests.exceptions.ConnectionError as e:
            log_print(f"    [-] Homegate : Erreur connexion - {e}")
        except Exception as e:
            log_print(f"    [-] Homegate : Erreur - {e}")
    
    def sort_apartments(self):
        """Trie les appartements par loyer croissant, puis surface"""
        def sort_key(apt):
            try:
                loyer = int(''.join(filter(str.isdigit, str(apt['Loyer CHF']))))
            except:
                loyer = 9999
            
            try:
                surface = int(''.join(filter(str.isdigit, str(apt['Surface m²'])))) if apt['Surface m²'] != 'N/A' else 9999
            except:
                surface = 9999
            
            return (loyer, surface)
        
        self.apartments.sort(key=sort_key)
        log_print(f"[+] Tri effectue : {len(self.apartments)} appartements")
    
    def save_to_json(self, filename='data.json'):
        """Sauvegarde les données en JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.apartments, f, ensure_ascii=False, indent=2)
            log_print(f"[+] Fichier sauvegarde : {filename} ({len(self.apartments)} annonces)")
            return True
        except Exception as e:
            log_print(f"[-] Erreur sauvegarde JSON : {e}")
            return False
    
    def run(self):
        """Lance le scraping complet"""
        log_print("=" * 60)
        log_print("SCRAPER VEILLE IMMOBILIÈRE GENÈVE")
        log_print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_print("=" * 60)
        log_print(f"[*] Criteres : {CRITERES['loyer_min']}-{CRITERES['loyer_max']} CHF, {CRITERES['pieces_min']}-{CRITERES['pieces_max']} pieces")
        log_print("")
        
        # Scraper les différentes sources
        self.scrape_immoscout24()
        
        self.scrape_homaget()
        
        # Tri et sauvegarde
        self.sort_apartments()
        self.save_to_json()
        
        log_print("")
        log_print("=" * 60)
        log_print("RÉSUMÉ FINAL")
        log_print("=" * 60)
        log_print(f"Total annonces trouvees : {len(self.apartments)}")
        
        if self.apartments:
            try:
                prices = [int(''.join(filter(str.isdigit, str(apt['Loyer CHF'])))) for apt in self.apartments if apt['Loyer CHF'] != 'N/A']
                if prices:
                    log_print(f"Prix min : {min(prices)} CHF")
                    log_print(f"Prix max : {max(prices)} CHF")
                    log_print(f"Prix moyen : {sum(prices)//len(prices)} CHF")
            except:
                pass
        
        log_print("=" * 60)
        log_print("[OK] Scraping termine !")

if __name__ == "__main__":
    try:
        scraper = ApartmentScraper()
        scraper.run()
    except Exception as e:
        log_print(f"[ERREUR] {e}")
