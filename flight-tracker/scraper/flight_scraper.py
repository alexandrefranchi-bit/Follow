"""Coleta de preços de passagens aéreas.

IMPORTANTE:
Fazer scraping direto de Google Flights, Skyscanner ou Kayak viola os Termos
de Uso desses sites e é tecnicamente frágil (páginas dinâmicas, proteção
anti-bot, mudam sem aviso). Este módulo usa um GERADOR SIMULADO de preços
(realista, com tendência e ruído) para que todo o resto do sistema — banco,
dashboard, alertas e ML — funcione de ponta a ponta desde já.

Quando quiser dados reais, troque `_generate_simulated_offers()` por uma
chamada a uma API oficial de voos (ex: Amadeus Self-Service, Skyscanner via
RapidAPI, ou AviationStack) mantendo a mesma assinatura de `fetch_prices()`.
"""
import logging
import math
import random
from datetime import datetime

import config

logger = logging.getLogger("flight_tracker.scraper")

AIRLINES = ["LATAM", "Gol", "Azul"]
SOURCES = ["Google Flights", "Skyscanner", "Kayak"]

# Preço-base por rota, usado como âncora do gerador simulado.
_BASE_PRICE = {
    "GIG": 780.0,
    "SDU": 850.0,
}


def _price_seed(origin: str, destination: str, departure_date: str, return_date: str) -> int:
    """Seed determinístico por combinação, para gerar uma tendência estável ao longo do tempo."""
    key = f"{origin}-{destination}-{departure_date}-{return_date}"
    return sum(ord(c) for c in key)


def _generate_simulated_offers(origin: str, destination: str, departure_date: str, return_date: str) -> list:
    base = _BASE_PRICE.get(destination, 800.0)
    seed = _price_seed(origin, destination, departure_date, return_date)
    rng = random.Random(seed + int(datetime.now().timestamp() // 1800))  # muda a cada 30 min

    # Componente de tendência: oscila lentamente ao longo dos dias (simula mercado)
    day_of_year = datetime.now().timetuple().tm_yday
    trend = math.sin(day_of_year / 12 + seed) * 60

    offers = []
    for airline in AIRLINES:
        noise = rng.uniform(-45, 45)
        airline_markup = {"LATAM": 40, "Gol": 0, "Azul": 15}[airline]
        price = round(max(base + trend + noise + airline_markup, 250.0), 2)
        direct = rng.random() > 0.4
        offers.append(
            {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "price": price,
                "airline": airline,
                "departure_time": f"{rng.randint(5, 22):02d}:{rng.choice(['00', '15', '30', '45'])}",
                "arrival_time": f"{rng.randint(5, 22):02d}:{rng.choice(['00', '15', '30', '45'])}",
                "duration_minutes": rng.randint(90, 130) if direct else rng.randint(240, 420),
                "direct": direct,
                "link": f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}",
                "source": rng.choice(SOURCES),
                "timestamp": datetime.now().isoformat(),
            }
        )
    return offers


def fetch_prices(origin: str, destination: str, departure_date: str, return_date: str) -> list:
    """Retorna uma lista de ofertas (dict) para a combinação informada.

    Assinatura estável: substitua o corpo por uma chamada de API real quando
    disponível, sem precisar alterar quem chama esta função.
    """
    try:
        offers = _generate_simulated_offers(origin, destination, departure_date, return_date)
        logger.info(
            "Coletadas %d ofertas para %s->%s (%s / %s)",
            len(offers), origin, destination, departure_date, return_date,
        )
        return offers
    except Exception:
        logger.exception("Falha ao coletar preços para %s->%s", origin, destination)
        return []


def run_full_scrape() -> list:
    """Roda a coleta para todas as combinações configuradas em config.py."""
    all_offers = []
    for destination in config.DESTINATIONS:
        for departure_date in config.DEPARTURE_DATES:
            for return_date in config.RETURN_DATES:
                all_offers.extend(
                    fetch_prices(config.ORIGIN, destination, departure_date, return_date)
                )
    return all_offers
