"""Envio de alertas por email (queda de preço, melhor combinação, relatório diário)."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from database import db

logger = logging.getLogger("flight_tracker.alerts")


def _send_email(subject: str, html_body: str) -> bool:
    if not config.EMAIL_SENDER or not config.EMAIL_APP_PASSWORD:
        logger.warning("Email não configurado (.env vazio) — pulando envio: %s", subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(config.EMAIL_SENDER, config.EMAIL_APP_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECIPIENT, msg.as_string())
        logger.info("Email enviado: %s", subject)
        return True
    except Exception:
        logger.exception("Falha ao enviar email: %s", subject)
        return False


def send_price_drop_alert(offer: dict, previous_price: float) -> None:
    drop_pct = round((previous_price - offer["price"]) / previous_price * 100, 1)
    subject = f"📉 Queda de preço: {offer['origin']}→{offer['destination']} caiu {drop_pct}%"
    html = f"""
    <h2>Queda de preço detectada!</h2>
    <p><b>Rota:</b> {offer['origin']} → {offer['destination']}</p>
    <p><b>Datas:</b> ida {offer['departure_date']} / volta {offer['return_date']}</p>
    <p><b>Companhia:</b> {offer['airline']}</p>
    <p><b>Preço anterior:</b> R$ {previous_price:.2f}</p>
    <p><b>Novo preço:</b> R$ {offer['price']:.2f}</p>
    <p><b>Economia:</b> {drop_pct}%</p>
    <p><a href="{offer['link']}">Ver passagem</a></p>
    """
    if _send_email(subject, html):
        db.insert_alert("price_drop", subject, config.EMAIL_RECIPIENT)


def send_new_best_price_alert(offer: dict) -> None:
    subject = f"🏆 Nova melhor combinação: {offer['origin']}→{offer['destination']} por R$ {offer['price']:.2f}"
    html = f"""
    <h2>Nova melhor combinação encontrada!</h2>
    <p><b>Rota:</b> {offer['origin']} → {offer['destination']}</p>
    <p><b>Datas:</b> ida {offer['departure_date']} / volta {offer['return_date']}</p>
    <p><b>Companhia:</b> {offer['airline']}</p>
    <p><b>Preço:</b> R$ {offer['price']:.2f}</p>
    <p><a href="{offer['link']}">Ver passagem</a></p>
    """
    if _send_email(subject, html):
        db.insert_alert("new_best_price", subject, config.EMAIL_RECIPIENT)


def send_daily_report(top_offers: list, stats: dict, recommendation: dict) -> None:
    rows = "".join(
        f"<tr><td>{o['origin']}→{o['destination']}</td><td>{o['departure_date']}</td>"
        f"<td>{o['return_date']}</td><td>{o['airline']}</td><td>R$ {o['price']:.2f}</td></tr>"
        for o in top_offers[:5]
    )
    subject = f"📊 Relatório diário Flight Tracker — {config.EVENT_NAME}"
    html = f"""
    <h2>Relatório Diário — Flight Tracker</h2>
    <p><b>Total de registros:</b> {stats.get('total', 0)}</p>
    <p><b>Menor preço já visto:</b> R$ {(stats.get('min_price') or 0):.2f}</p>
    <p><b>Preço médio:</b> R$ {(stats.get('avg_price') or 0):.2f}</p>
    <h3>Top 5 passagens</h3>
    <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>Rota</th><th>Ida</th><th>Volta</th><th>Companhia</th><th>Preço</th></tr>
        {rows}
    </table>
    <h3>Recomendação</h3>
    <p>{recommendation.get('label', 'MONITORANDO')}: {recommendation.get('reason', '')}</p>
    """
    if _send_email(subject, html):
        db.insert_alert("daily_report", subject, config.EMAIL_RECIPIENT)
