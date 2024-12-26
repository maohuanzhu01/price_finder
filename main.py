from price_scraper import PriceScraper
import pandas as pd

def main():
    scraper = PriceScraper()
    
    # File di input e output
    input_file = "prodotti.csv"
    output_file = "risultati_ricerca.csv"
    
    # Processa la lista dei prodotti
    scraper.process_product_list(input_file, output_file)
    print("Ricerca completata! I risultati sono stati salvati in:")
    print(f"- {output_file}")
    print(f"- {output_file.replace('.csv', '.xlsx')}")
    
    scraper.driver.quit()

if __name__ == "__main__":
    main() 