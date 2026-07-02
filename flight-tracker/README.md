# ✈️ Flight Tracker

Sistema de rastreamento de passagens aéreas com previsões inteligentes, criado
para monitorar a rota **Presidente Prudente → Rio de Janeiro** rumo ao
**Rock in Rio 2026** (5 de setembro).

O sistema coleta preços a cada 30 minutos, guarda tudo em SQLite, envia
alertas por email quando o preço cai e recomenda o melhor momento para
comprar com base em análise de tendência.

> **Nota sobre a coleta de preços:** este projeto usa um gerador de preços
> simulado (`scraper/flight_scraper.py`) em vez de scraping direto de
> Google Flights/Skyscanner/Kayak, que violaria os Termos de Uso desses
> sites. Toda a arquitetura (banco, dashboard, alertas, ML) já funciona de
> ponta a ponta com os dados simulados; para usar dados reais, troque a
> função `fetch_prices()` por uma chamada a uma API oficial (Amadeus
> Self-Service, Skyscanner via RapidAPI, AviationStack etc.) — a assinatura
> da função permanece a mesma.

## Setup

```bash
cd flight-tracker

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edite o .env com seu email e App Password do Gmail
# gerar em: https://myaccount.google.com/apppasswords

python main.py
```

Depois de rodar, abra: http://127.0.0.1:5000

## Estrutura

```
flight-tracker/
├── main.py              # Entry point: scheduler + dashboard
├── config.py            # Configurações centralizadas (rota, datas, alertas)
├── requirements.txt
├── .env.example
├── database/            # Schema SQLite + funções CRUD
├── scraper/              # Coleta de preços (simulada, ver nota acima)
├── alerts/               # Envio de emails (queda de preço, melhor combo, relatório)
├── dashboard/            # Flask + templates + APIs JSON
├── ml/                   # Análise de tendência e recomendação de compra
├── data/                 # flights.db (criado automaticamente)
└── logs/                 # flight_tracker.log
```

## Configuração (`config.py`)

```python
DEPARTURE_DATES = ["2026-09-03", "2026-09-04", "2026-09-05"]
RETURN_DATES = ["2026-09-07", "2026-09-08", "2026-09-09"]
SCHEDULER_INTERVAL_MINUTES = 30
PRICE_DROP_THRESHOLD = 10   # %
DAILY_REPORT_TIME = "12:00"
```

## Alertas

- **Queda de preço** — dispara quando o preço cai ≥10% em relação ao menor
  preço já registrado para aquela combinação.
- **Nova melhor combinação** — dispara quando surge um preço mais baixo do
  que qualquer um já visto.
- **Relatório diário** — enviado às 12h com o top 5 de passagens, estatísticas
  e a recomendação atual.

## Machine Learning

`ml/predictor.py` roda uma regressão linear sobre o histórico de preços de
cada combinação para estimar tendência (alta/queda/estável) e confiança, e
gera uma recomendação:

- 🟢 **COMPRE AGORA** — preço abaixo da média histórica
- 🟡 **MONITORANDO** — sem sinal claro
- 🔴 **AGUARDE MAIS** — tendência de queda com alta confiança

A confiança tende a melhorar com mais dados coletados (ideal: 50+ pontos,
1–2 semanas de rastreamento).

## Troubleshooting

| Problema | Solução |
|----------|---------|
| `Module not found` | `pip install -r requirements.txt` novamente |
| Erro de autenticação do Gmail | Use um App Password, não a senha normal da conta |
| Scheduler não roda | Verifique `SCHEDULER_ENABLED = True` em `config.py` |
| Dashboard não abre | Porta 5000 ocupada? Mude `FLASK_PORT` em `config.py`/`.env` |
| Sem dados no dashboard | Aguarde a primeira coleta (roda automaticamente ao iniciar) |
