"""Análise de tendências e recomendação de compra.

Usa regressão linear simples (scikit-learn) sobre o histórico de preços de
cada combinação origem/destino/datas para estimar se o preço está subindo,
caindo ou estável, e recomenda a melhor ação.
"""
import logging
from datetime import datetime
from statistics import mean, pstdev

import numpy as np
from sklearn.linear_model import LinearRegression

import config
from database import db

logger = logging.getLogger("flight_tracker.ml")


def analyze_trend(origin: str, destination: str, departure_date: str, return_date: str) -> dict:
    history = db.get_price_history(origin, destination, departure_date, return_date)

    if len(history) < 3:
        return {"trend": "insufficient_data", "confidence": 0, "expected_price": None, "n": len(history)}

    prices = np.array([h["price"] for h in history])
    x = np.arange(len(prices)).reshape(-1, 1)

    model = LinearRegression().fit(x, prices)
    slope = model.coef_[0]
    expected_next = float(model.predict([[len(prices)]])[0])

    volatility = pstdev(prices) if len(prices) > 1 else 0
    avg_price = mean(prices)
    confidence = max(0, min(100, 100 - (volatility / avg_price * 100 if avg_price else 0)))

    if slope < -1:
        trend = "down"
    elif slope > 1:
        trend = "up"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "slope": round(float(slope), 3),
        "confidence": round(confidence, 1),
        "expected_price": round(expected_next, 2),
        "avg_price": round(avg_price, 2),
        "n": len(history),
    }


def recommend(origin: str, destination: str, departure_date: str, return_date: str) -> dict:
    trend_info = analyze_trend(origin, destination, departure_date, return_date)
    history = db.get_price_history(origin, destination, departure_date, return_date)

    if not history:
        return {"label": "SEM DADOS", "reason": "Ainda não há coleta suficiente.", "color": "gray"}

    current_price = history[-1]["price"]
    avg_price = trend_info.get("avg_price") or current_price

    if current_price <= avg_price * 0.9:
        return {
            "label": "COMPRE AGORA",
            "reason": f"Preço atual (R$ {current_price:.2f}) está {round((1 - current_price / avg_price) * 100, 1)}% abaixo da média.",
            "color": "green",
        }
    if trend_info["trend"] == "down" and trend_info["confidence"] >= config.ML_MIN_CONFIDENCE:
        return {
            "label": "AGUARDE MAIS",
            "reason": "Tendência de queda com alta confiança — o preço deve cair ainda mais.",
            "color": "red",
        }
    return {
        "label": "MONITORANDO",
        "reason": "Preço estável, sem sinal claro de queda ou alta.",
        "color": "yellow",
    }


def predict_best_day_to_buy(origin: str, destinations: list, departure_dates: list, return_dates: list) -> dict:
    predictions = []
    for destination in destinations:
        for departure_date in departure_dates:
            for return_date in return_dates:
                trend = analyze_trend(origin, destination, departure_date, return_date)
                rec = recommend(origin, destination, departure_date, return_date)
                predictions.append(
                    {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                        "return_date": return_date,
                        **trend,
                        "recommendation": rec,
                    }
                )

    valid = [p for p in predictions if p.get("expected_price") is not None]
    best = min(valid, key=lambda p: p["expected_price"]) if valid else None

    return {
        "generated_at": datetime.now().isoformat(),
        "best_combination": best,
        "predictions": predictions,
    }
