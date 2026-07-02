"""Servidor Flask do dashboard + APIs JSON."""
import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))  # permite rodar este arquivo diretamente

from flask import Flask, jsonify, render_template, request

import config
from database import db
from ml import predictor

logger = logging.getLogger("flight_tracker.dashboard")
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)


@app.route("/")
def index():
    return render_template(
        "index.html",
        origin=config.ORIGIN,
        destinations=config.DESTINATIONS,
        event_name=config.EVENT_NAME,
        event_date=config.EVENT_DATE,
    )


@app.route("/api/stats")
def api_stats():
    return jsonify(db.get_stats())


@app.route("/api/best-combinations")
def api_best_combinations():
    limit = int(request.args.get("limit", 10))
    return jsonify(db.get_best_combinations(limit=limit))


@app.route("/api/latest")
def api_latest():
    limit = int(request.args.get("limit", 50))
    return jsonify(db.get_latest_prices(limit=limit))


@app.route("/api/history")
def api_history():
    origin = request.args.get("origin", config.ORIGIN)
    destination = request.args.get("destination")
    departure_date = request.args.get("departure_date")
    return_date = request.args.get("return_date")
    if not (destination and departure_date and return_date):
        return jsonify({"error": "destination, departure_date e return_date são obrigatórios"}), 400
    return jsonify(db.get_price_history(origin, destination, departure_date, return_date))


@app.route("/api/recommendation")
def api_recommendation():
    result = predictor.predict_best_day_to_buy(
        config.ORIGIN, config.DESTINATIONS, config.DEPARTURE_DATES, config.RETURN_DATES
    )
    return jsonify(result)


def create_app() -> Flask:
    db.init_db()
    return app


if __name__ == "__main__":
    create_app().run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG)
