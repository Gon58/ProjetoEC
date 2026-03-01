import os
import time

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def test_steam_ingestion(appid, limit_samples=50):
    """
    Testa a recolha de reviews da Steam focadas no mercado de skins.
    """
    # Keywords para garantir relevância ao Sistema de Suporte à Decisão
    target_keywords = [
        'skin', 'market', 'case', 'knife', 'trade', 'price', 'sticker', 
        'float', 'key', 'wear', 'pattern', 'buff', 'investment', 'stattrak',
        'fn', 'mw', 'ft', 'ww', 'bs', 'fade', 'doppler', 'souvenir'
    ]
    
    url = f'https://store.steampowered.com/appreviews/{appid}?json=1&filter=recent&language=english'
    cursor = '*'
    
    total_found = 0
    relevant_found = 0
    samples = []

    print(f"--- A iniciar teste de ingestão para AppID: {appid} ---")

    # Fazemos apenas algumas iterações para teste de amostragem
    for i in range(5): 
        params = {'cursor': cursor, 'day_range': 30, 'num_per_page': 100}
        response = requests.get(url, params=params).json()
        
        if not response.get('reviews'):
            break
            
        reviews = response['reviews']
        cursor = response['cursor']
        
        for r in reviews:
            total_found += 1
            text = r.get('review', '').lower()
            
            # Validação Semântica: Verifica se a review fala de algo relevante para o SSD
            if any(key in text for key in target_keywords):
                relevant_found += 1
                if len(samples) < limit_samples:
                    samples.append(text[:100].replace('\n', ' ')) # Guarda amostra curta

        print(f"Lote {i+1}: Analisadas {total_found} reviews... (Relevantes: {relevant_found})")
        time.sleep(0.5) # Evitar rate limit agressivo

    print("\n--- Resultados do Teste ---")
    print(f"Total de reviews lidas: {total_found}")
    print(f"Reviews úteis para o RAG (com keywords): {relevant_found}")
    if total_found > 0:
        print(f"Taxa de relevância: {(relevant_found/total_found)*100:.2f}%")
        print("\n--- Amostra de Dados (Primeiros 5 úteis) ---")
        for s in samples[:5]:
            print(f"-> {s}...")
    else:
        print("Nenhuma review encontrada para análise.")

    return (total_found > 0)

def run_ingestion(appid, target_total=55000):
    client = MongoClient(host=os.getenv("MONGO_HOST", "ec-project-mongo"), port=27017)
    db = client[os.getenv("MONGO_DB", "ec_project")]
    collection = db["steam_reviews"]

    logs_collection = db["system_logs"]

    keywords = ['skin', 'market', 'case', 'knife', 'trade', 'price', 'sticker', 'float', 'key']
    
    cursor = '*'
    count = collection.count_documents({}) # Conta o que já está na bd
    
    print(f"--- Ingestão iniciada: Alvo {target_total} (Já existem {count} na BD) ---")

    while count < target_total:
        url = f'https://store.steampowered.com/appreviews/{appid}'
        params = {
            'json': 1,
            'filter': 'all', # 'all' para volume, (mais para a frente usar'recent' para novidades) 
            'language': 'english',
            'cursor': cursor,
            'num_per_page': 100,
            'purchase_type': 'all'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('success') != 1 or not data.get('reviews'):
                print("Fim dos dados disponíveis ou erro da API.")
                break
            
            reviews = data['reviews']
            next_cursor = data.get('cursor')
            
            if next_cursor == cursor:
                print("Cursor não avançou. A interromper para evitar duplicados.")
                break
            
            cursor = next_cursor
            batch = []
            for r in reviews:
                text = r.get('review', '').lower()
                r['is_market_related'] = any(key in text for key in keywords)
                r['source'] = 'steam_reviews_api'
                batch.append(r)
            
            if batch:
                for doc in batch:
                    collection.update_one(
                        {"recommendationid": doc["recommendationid"]}, 
                        {"$set": doc}, 
                        upsert=True # evita erros de duplicados
                    )
                count = collection.count_documents({})
                print(f"Progresso: {count}/{target_total} documentos na BD...")

            time.sleep(1.5) # Respeitar rate limit da steam
            
        except Exception as e:
            print(f"Erro na recolha: {e}")
            break

    logs_collection.insert_one({
        "event": "ingestion_run",
        "appid": appid,
        "records_reached": count,
        "status": "success",
        "timestamp": time.time()
    })

    print(f"--- Processo terminado com {count} registos na coleção ---")

if __name__ == "__main__":
    
    steam_id = int(os.getenv("STEAM_APP_ID", 123))

    is_api_healthy = test_steam_ingestion(appid=steam_id, limit_samples=10)
    
    if is_api_healthy:
        print(f"✅ API is healthy. Starting full ingestion for appid {steam_id}...")
        run_ingestion(appid=steam_id)
    else:
        print("❌ Ingestion aborted: API connectivity issues.")

