"""
Steam CS2 Market Scraper
========================
Estratégia: dividir por categorias do CS2 para nunca ultrapassar o limite de ~5000 itens por query.
Sem proxies, com delays conservadores para não ser bloqueado.

Uso:
    python steam_cs2_scraper.py

Output:
    cs2_market_prices.json  — todos os itens no schema da DB
    cs2_market_prices.csv   — mesma coisa em CSV
    scraper_progress.json   — progresso (permite retomar se parar)
"""

import requests
import json
import time
import csv
import random
import logging
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

APP_ID = 730  # CS2
CURRENCY = 1  # 1 = USD
COUNT = 100   # itens por página (máximo da API)

# Delays entre requests (segundos) — conservador para não ser banido
DELAY_MIN = 1.5
DELAY_MAX = 3.0

# Delay extra depois de um rate limit (429)
RATE_LIMIT_WAIT = 60  # segundos

# Ficheiros de output
OUTPUT_JSON = "cs2_market_prices.json"
OUTPUT_CSV  = "cs2_market_prices.csv"
PROGRESS_FILE = "scraper_progress.json"

# ─── Logging ──────────────────────────────────────────────────────────────────

import sys
import io

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper.log", encoding="utf-8"),
        logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")),
    ]
)
log = logging.getLogger(__name__)

# ─── Categorias CS2 ───────────────────────────────────────────────────────────
# Cada entrada é um dict de params de filtro para o endpoint search/render.
# Dividimos ao máximo para garantir que cada subset < 5000 itens.
# A Steam usa: category_730_Type[], category_730_Weapon[], category_730_Exterior[]

CATEGORIES = [
    # ── Weapons por tipo ──────────────────────────────────────────────────────
    {"label": "Rifles",           "params": {"category_730_Type[]": "tag_CSGO_Type_Rifle"}},
    {"label": "Pistols",          "params": {"category_730_Type[]": "tag_CSGO_Type_Pistol"}},
    {"label": "SMGs",             "params": {"category_730_Type[]": "tag_CSGO_Type_SMG"}},
    {"label": "Shotguns",         "params": {"category_730_Type[]": "tag_CSGO_Type_Shotgun"}},
    {"label": "Snipers",          "params": {"category_730_Type[]": "tag_CSGO_Type_SniperRifle"}},
    {"label": "Machinegun",       "params": {"category_730_Type[]": "tag_CSGO_Type_Machinegun"}},
    # ── Knives por exterior (muitos itens, dividimos por wear) ────────────────
    {"label": "Knives_FN",        "params": {"category_730_Type[]": "tag_CSGO_Type_Knife", "category_730_Exterior[]": "tag_WearCategory0"}},
    {"label": "Knives_MW",        "params": {"category_730_Type[]": "tag_CSGO_Type_Knife", "category_730_Exterior[]": "tag_WearCategory1"}},
    {"label": "Knives_FT",        "params": {"category_730_Type[]": "tag_CSGO_Type_Knife", "category_730_Exterior[]": "tag_WearCategory2"}},
    {"label": "Knives_WW",        "params": {"category_730_Type[]": "tag_CSGO_Type_Knife", "category_730_Exterior[]": "tag_WearCategory3"}},
    {"label": "Knives_BS",        "params": {"category_730_Type[]": "tag_CSGO_Type_Knife", "category_730_Exterior[]": "tag_WearCategory4"}},
    # ── Gloves por exterior ───────────────────────────────────────────────────
    {"label": "Gloves_FN",        "params": {"category_730_Type[]": "tag_CSGO_Type_Hands", "category_730_Exterior[]": "tag_WearCategory0"}},
    {"label": "Gloves_MW",        "params": {"category_730_Type[]": "tag_CSGO_Type_Hands", "category_730_Exterior[]": "tag_WearCategory1"}},
    {"label": "Gloves_FT",        "params": {"category_730_Type[]": "tag_CSGO_Type_Hands", "category_730_Exterior[]": "tag_WearCategory2"}},
    {"label": "Gloves_WW",        "params": {"category_730_Type[]": "tag_CSGO_Type_Hands", "category_730_Exterior[]": "tag_WearCategory3"}},
    {"label": "Gloves_BS",        "params": {"category_730_Type[]": "tag_CSGO_Type_Hands", "category_730_Exterior[]": "tag_WearCategory4"}},
    # ── Stickers (muitos! dividimos por raridade) ─────────────────────────────
    {"label": "Stickers_High",    "params": {"category_730_Type[]": "tag_CSGO_Type_Spray",   "category_730_ItemSet[]": "tag_set_sticker_pack"}},
    {"label": "Stickers",         "params": {"category_730_Type[]": "tag_CSGO_Type_Sticker"}},
    # ── Outros ────────────────────────────────────────────────────────────────
    {"label": "Cases",            "params": {"category_730_Type[]": "tag_CSGO_Type_WeaponCase"}},
    {"label": "Keys",             "params": {"category_730_Type[]": "tag_CSGO_Type_WeaponCase_KeyTag"}},
    {"label": "Agents",           "params": {"category_730_Type[]": "tag_CSGO_Type_CustomPlayer"}},
    {"label": "Patches",          "params": {"category_730_Type[]": "tag_CSGO_Type_Patch"}},
    {"label": "Graffiti",         "params": {"category_730_Type[]": "tag_CSGO_Type_Spray"}},
    {"label": "MusicKits",        "params": {"category_730_Type[]": "tag_CSGO_Type_MusicKit"}},
    {"label": "Collectibles",     "params": {"category_730_Type[]": "tag_CSGO_Type_Collectible"}},
    {"label": "Gifts",            "params": {"category_730_Type[]": "tag_CSGO_Type_Gift"}},
    {"label": "Tools",            "params": {"category_730_Type[]": "tag_CSGO_Type_Tool"}},
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://steamcommunity.com/market/search?appid=730",
})


def build_url(start: int, category_params: dict) -> tuple[str, dict]:
    base = f"https://steamcommunity.com/market/search/render/"
    params = {
        "appid": APP_ID,
        "norender": 1,
        "count": COUNT,
        "start": start,
        "currency": CURRENCY,
        **category_params,
    }
    return base, params


def fetch_page(start: int, category_params: dict, retries: int = 5) -> dict | None:
    url, params = build_url(start, category_params)
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=15)
            if r.status_code == 429:
                wait = RATE_LIMIT_WAIT * (attempt + 1)
                log.warning(f"Rate limited (429). A aguardar {wait}s...")
                time.sleep(wait)
                continue
            if r.status_code == 200:
                return r.json()
            log.warning(f"Status {r.status_code} em start={start}. Tentativa {attempt+1}/{retries}")
            time.sleep(5)
        except Exception as e:
            log.error(f"Erro em start={start}: {e}. Tentativa {attempt+1}/{retries}")
            time.sleep(5)
    return None


def parse_items(data: dict) -> list[dict]:
    """Converte a resposta da Steam para o schema da DB."""
    items = []
    for result in data.get("results", []):
        try:
            sell_price_raw = result.get("sell_price", 0)
            sell_price = round(sell_price_raw / 100, 2)  # Steam devolve em cêntimos
            sell_listings = result.get("sell_listings", 0)
            name = result.get("hash_name", result.get("name", ""))

            items.append({
                "market_hash_name": name,
                "currency": "USD",
                "min_price": sell_price,
                "max_price": sell_price,
                "mean_price": sell_price,
                "median_price": sell_price,
                "quantity_sold": sell_listings,
                "source": "steam_market",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            log.error(f"Erro a parsear item: {e} — {result}")
    return items


def load_progress() -> dict:
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed_labels": [], "all_items": {}}


def save_progress(progress: dict):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)


def save_outputs(all_items: dict):
    items_list = list(all_items.values())

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(items_list, f, ensure_ascii=False, indent=2)

    if items_list:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=items_list[0].keys())
            writer.writeheader()
            writer.writerows(items_list)

    log.info(f"💾 Guardado: {len(items_list)} itens únicos → {OUTPUT_JSON} + {OUTPUT_CSV}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def scrape_category(label: str, params: dict, progress: dict) -> list[dict]:
    """Faz scraping de uma categoria completa, página a página."""
    log.info(f"━━━ Categoria: {label} ━━━")
    items = []
    start = 0

    while True:
        log.info(f"  [{label}] start={start}...")
        data = fetch_page(start, params)

        if data is None:
            log.error(f"  [{label}] Falha a obter página start={start}. A saltar.")
            break

        total = data.get("total_count", 0)
        results = data.get("results", [])

        if not results:
            log.info(f"  [{label}] Sem mais resultados (total={total}).")
            break

        page_items = parse_items(data)
        items.extend(page_items)
        n = len(page_items)
        log.info(f"  [{label}] +{n} itens | total desta cat: {len(items)}/{total}")

        # Avanca pelo numero real de itens devolvidos (a Steam pode devolver menos que COUNT)
        step = n if n > 0 else COUNT
        next_start = start + step

        if next_start >= total or next_start >= 4900:
            # 4900 como safety margin ao limite de 5000
            if next_start < total:
                log.warning(f"  [{label}] Atingido limite de 5000! Ficaram por buscar {total - next_start} itens.")
                log.warning(f"  [{label}] Considera subdividir mais esta categoria.")
            break

        start = next_start
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    log.info(f"  [{label}] ✓ {len(items)} itens recolhidos.")
    return items


def main():
    log.info("🚀 Steam CS2 Market Scraper iniciado")
    progress = load_progress()
    completed = set(progress["completed_labels"])
    all_items = progress["all_items"]  # dict market_hash_name -> item (dedup automático)

    total_categories = len(CATEGORIES)

    for i, cat in enumerate(CATEGORIES, 1):
        label = cat["label"]
        params = cat["params"]

        if label in completed:
            log.info(f"[{i}/{total_categories}] A saltar {label} (já completo)")
            continue

        log.info(f"[{i}/{total_categories}] A processar: {label}")
        items = scrape_category(label, params, progress)

        # Dedup por market_hash_name
        for item in items:
            all_items[item["market_hash_name"]] = item

        completed.add(label)
        progress["completed_labels"] = list(completed)
        progress["all_items"] = all_items
        save_progress(progress)
        save_outputs(all_items)

        # Pausa entre categorias
        if i < total_categories:
            pause = random.uniform(3, 6)
            log.info(f"⏸  Pausa entre categorias: {pause:.1f}s")
            time.sleep(pause)

    log.info(f"✅ Scraping completo! {len(all_items)} itens únicos recolhidos.")
    save_outputs(all_items)

    # Limpar ficheiro de progresso
    Path(PROGRESS_FILE).unlink(missing_ok=True)
    log.info("Ficheiro de progresso removido.")


if __name__ == "__main__":
    main()