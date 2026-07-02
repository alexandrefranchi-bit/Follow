"""Entry point do Flight Tracker: roda o scheduler e o dashboard web."""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from alerts import email_alerts
from dashboard.server import create_app
from database import db
from ml import predictor
from scraper import flight_scraper

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("flight_tracker.main")


def scrape_job() -> None:
    logger.info("Iniciando coleta de preços…")
    offers = flight_scraper.run_full_scrape()

    for offer in offers:
        history = db.get_price_history(
            offer["origin"], offer["destination"], offer["departure_date"], offer["return_date"]
        )
        previous_min = min((h["price"] for h in history), default=None)

        db.insert_flight_price(offer)

        if previous_min is not None:
            drop_pct = (previous_min - offer["price"]) / previous_min * 100
            if drop_pct >= config.PRICE_DROP_THRESHOLD:
                email_alerts.send_price_drop_alert(offer, previous_min)
            elif offer["price"] < previous_min:
                email_alerts.send_new_best_price_alert(offer)
        elif offer["price"]:
            email_alerts.send_new_best_price_alert(offer)

        updated_history = history + [offer]
        prices = [h["price"] for h in updated_history]
        db.insert_price_trend(
            {
                "origin": offer["origin"],
                "destination": offer["destination"],
                "departure_date": offer["departure_date"],
                "return_date": offer["return_date"],
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "timestamp": datetime.now().isoformat(),
            }
        )

    logger.info("Coleta concluída: %d ofertas processadas.", len(offers))


def daily_report_job() -> None:
    logger.info("Gerando relatório diário…")
    top_offers = db.get_best_combinations(limit=5)
    stats = db.get_stats()
    prediction = predictor.predict_best_day_to_buy(
        config.ORIGIN, config.DESTINATIONS, config.DEPARTURE_DATES, config.RETURN_DATES
    )
    best = prediction.get("best_combination")
    recommendation = best["recommendation"] if best else {"label": "SEM DADOS", "reason": ""}
    email_alerts.send_daily_report(top_offers, stats, recommendation)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_job, "interval", minutes=config.SCHEDULER_INTERVAL_MINUTES, id="scrape_job")

    hour, minute = config.DAILY_REPORT_TIME.split(":")
    scheduler.add_job(
        daily_report_job,
        CronTrigger(hour=int(hour), minute=int(minute)),
        id="daily_report_job",
    )
    scheduler.start()
    logger.info(
        "Scheduler iniciado: coleta a cada %d min, relatório diário às %s.",
        config.SCHEDULER_INTERVAL_MINUTES, config.DAILY_REPORT_TIME,
    )
    return scheduler


def main() -> None:
    app = create_app()
    scrape_job()  # primeira coleta imediata ao iniciar

    if config.SCHEDULER_ENABLED:
        start_scheduler()

    logger.info("Dashboard disponível em http://%s:%d", config.FLASK_HOST, config.FLASK_PORT)
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG, use_reloader=False)


if __name__ == "__main__":
    main()
