from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re

class PriceScraper:
    def __init__(self):
        # Configurazione delle opzioni di Chrome
        chrome_options = webdriver.ChromeOptions()
        
        # Opzioni base per evitare il rilevamento dell'automazione
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')
        
        # Aggiungi opzioni per gestire i cookie
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.cookies": 1,
            "profile.block_third_party_cookies": False,
            "profile.cookie_controls_mode": 0
        })
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Inizializza il driver con le opzioni
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Accetta automaticamente i cookie di Google
        try:
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Clicca "Accetta tutto"
            accept_buttons = [
                "//button[contains(text(), 'Accetta tutto')]",
                "//button[contains(., 'Accetta tutto')]",
                "//*[@id='L2AGLb']",  # ID comune del pulsante "Accetta tutto"
                "//button[contains(@class, 'tHlp8d')]"  # Classe comune del pulsante
            ]
            
            for xpath in accept_buttons:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    button.click()
                    print("Cookie accettati con successo")
                    break
                except:
                    continue
        except Exception as e:
            print(f"Errore nell'accettazione automatica dei cookie: {e}")
        
        # Pattern regex per trovare i prezzi in vari formati
        self.price_patterns = [
            r'€\s*[\d.,]+',  # Formato: € 999,99 o €999.99
            r'[\d.,]+\s*€',  # Formato: 999,99 € o 999.99€
            r'EUR\s*[\d.,]+',  # Formato: EUR 999,99
            r'[\d.,]+\s*EUR',  # Formato: 999,99 EUR
        ]
        
    def extract_price(self, text):
        """
        Estrae il prezzo dal testo utilizzando pattern regex
        Restituisce il prezzo più basso trovato
        """
        prices = []
        for pattern in self.price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                price_str = match.group(0)
                # Pulisce la stringa del prezzo
                price_str = price_str.replace('€', '').replace('EUR', '').strip()
                # Converte le virgole in punti per i decimali
                price_str = price_str.replace(',', '.')
                try:
                    # Estrae solo il primo numero trovato
                    price = float(re.search(r'[\d.]+', price_str).group(0))
                    prices.append(price)
                except (ValueError, AttributeError):
                    continue
        
        return min(prices) if prices else None

    def search_product_price(self, product_name):
        try:
            # Modifica la query di ricerca per essere più specifica
            encoded_name = product_name.replace(' ', '+')
            search_url = f"https://www.google.com/search?q={encoded_name}+prezzo+acquista&tbm=shop"
            print(f"Cercando: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(5)  # Aumentato il tempo di attesa
            
            # Dizionario per memorizzare i dati del prodotto
            product_data = {
                'nome_prodotto': product_name,
                'prezzo_minimo': None,
                'prezzo_massimo': None,
                'prezzo_medio': None,
                'fornitori': set(),
                'voto_medio': None,
                'prezzi_per_fornitore': {}
            }
            
            # Cerca i prezzi usando diversi selettori
            price_selectors = [
                "span.a8Pemb",                    # Prezzo principale
                "span.T14wmb",                    # Prezzo alternativo
                "span[aria-label*='€']",          # Prezzi con simbolo euro
                "span[aria-label*='EUR']",        # Prezzi in EUR
                ".g9WBQb",                        # Contenitore prezzo
                "span.HRLxBb",                    # Altro formato prezzo
                ".dD8iuc"                         # Contenitore prodotto
            ]
            
            prices = []
            
            # Prova tutti i selettori
            for selector in price_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            # Prova sia il testo che l'attributo aria-label
                            price_text = element.text or element.get_attribute("aria-label")
                            if price_text:
                                print(f"Testo trovato: {price_text}")  # Debug
                                price = self.extract_price(price_text)
                                if price:
                                    # Trova il fornitore per questo prezzo
                                    try:
                                        merchant = "Sconosciuto"
                                        merchant_element = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'sh-dgr__content')]//div[contains(@class, 'IuHnof')]")
                                        merchant = merchant_element.text
                                    except:
                                        pass
                                    
                                    prices.append(price)
                                    print(f"Prezzo trovato per {product_name}: {price}€ da {merchant}")
                                    
                                    # Aggiungi il fornitore e il prezzo
                                    product_data['fornitori'].add(merchant)
                                    if merchant not in product_data['prezzi_per_fornitore']:
                                        product_data['prezzi_per_fornitore'][merchant] = []
                                    product_data['prezzi_per_fornitore'][merchant].append(price)
                        except Exception as e:
                            print(f"Errore nell'elaborazione del prezzo: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Errore con il selettore {selector}: {str(e)}")
                    continue
            
            # Calcola le statistiche dei prezzi
            if prices:
                product_data['prezzo_minimo'] = min(prices)
                product_data['prezzo_massimo'] = max(prices)
                product_data['prezzo_medio'] = sum(prices) / len(prices)
                
                print(f"\nStatistiche prezzi per {product_name}:")
                print(f"Min: {product_data['prezzo_minimo']}€")
                print(f"Max: {product_data['prezzo_massimo']}€")
                print(f"Media: {product_data['prezzo_medio']}€")
                print("Prezzi per fornitore:")
                for merchant, merchant_prices in product_data['prezzi_per_fornitore'].items():
                    print(f"- {merchant}: {min(merchant_prices)}€ - {max(merchant_prices)}€")
            else:
                print(f"Nessun prezzo trovato per {product_name}")
            
            return product_data
                
        except Exception as e:
            print(f"Errore durante la ricerca: {str(e)}")
            return {
                'nome_prodotto': product_name,
                'prezzo_minimo': None,
                'prezzo_massimo': None,
                'prezzo_medio': None,
                'fornitori': set(),
                'voto_medio': None
            }
    
    def process_product_list(self, input_file, output_file):
        # Leggi il file di input
        df = pd.read_csv(input_file)
        
        # Lista per memorizzare i risultati
        results = []
        
        # Cerca i prezzi per ogni prodotto
        for product in df['nome_prodotto']:
            data = self.search_product_price(product)
            # Converti il set dei fornitori in stringa
            data['fornitori'] = ', '.join(data['fornitori']) if data['fornitori'] else 'Non trovato'
            results.append(data)
        
        # Crea il DataFrame con i risultati
        results_df = pd.DataFrame(results)
        
        # Formatta i prezzi come valuta
        for col in ['prezzo_minimo', 'prezzo_massimo', 'prezzo_medio']:
            results_df[col] = results_df[col].apply(lambda x: f'€ {x:.2f}' if pd.notnull(x) else 'Non trovato')
        
        # Formatta il voto medio
        results_df['voto_medio'] = results_df['voto_medio'].apply(lambda x: f'{x:.1f}/5.0' if pd.notnull(x) else 'Non trovato')
        
        # Salva i risultati
        results_df.to_csv(output_file, index=False)
        
        # Salva anche in formato Excel
        excel_file = output_file.replace('.csv', '.xlsx')
        results_df.to_excel(excel_file, index=False)
    
    def __del__(self):
        self.driver.quit() 
    
    def is_valid_price(self, price, product_name):
        """
        Verifica se il prezzo è valido in base al tipo di prodotto
        """
        # Prezzi tipici per categoria di prodotto
        food_keywords = ['ramune', 'buldak', 'pocky', 'noodles', 'snack', 'food']
        tech_keywords = ['iphone', 'samsung', 'sony', 'nintendo', 'macbook']
        
        product_lower = product_name.lower()
        
        # Per prodotti alimentari
        if any(keyword in product_lower for keyword in food_keywords):
            return 0.5 <= price <= 50  # Prezzi tra 0.50€ e 50€
            
        # Per prodotti tech
        if any(keyword in product_lower for keyword in tech_keywords):
            return 100 <= price <= 5000  # Prezzi tra 100€ e 5000€
            
        # Per prodotti non categorizzati
        return 0.5 <= price <= 10000
    
    def filter_outliers(self, prices):
        """
        Filtra gli outlier usando il metodo IQR
        """
        if len(prices) < 4:  # Se ci sono pochi prezzi, non filtrare
            return prices
            
        prices = sorted(prices)
        q1 = prices[len(prices)//4]
        q3 = prices[3*len(prices)//4]
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        return [x for x in prices if lower_bound <= x <= upper_bound]
    
    def extract_rating(self, item, product_data):
        """
        Estrae e verifica il rating del prodotto
        """
        try:
            rating_selectors = [
                ".QIrs8[aria-label*='su 5']",
                "span[aria-label*='su 5']",
                ".QRbC1e"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = item.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_element.get_attribute("aria-label") or rating_element.text
                    if rating_text:
                        rating_match = re.search(r'(\d+[.,]\d+)(?:\s*su\s*5)', rating_text.replace(',', '.'))
                        if rating_match:
                            rating_value = float(rating_match.group(1))
                            if 0 <= rating_value <= 5:
                                if not product_data['voto_medio'] or rating_value > product_data['voto_medio']:
                                    product_data['voto_medio'] = rating_value
                                    return
                except:
                    continue
        except:
            pass 