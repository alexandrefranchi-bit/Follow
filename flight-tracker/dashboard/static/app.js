const fmtBRL = (v) => (v == null ? "–" : `R$ ${Number(v).toFixed(2)}`);

async function loadStats() {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("m-total").textContent = data.total ?? "0";
    document.getElementById("m-min").textContent = fmtBRL(data.min_price);
    document.getElementById("m-avg").textContent = fmtBRL(data.avg_price);
    document.getElementById("m-max").textContent = fmtBRL(data.max_price);
}

async function loadBestCombinations() {
    const res = await fetch("/api/best-combinations?limit=10");
    const rows = await res.json();
    const tbody = document.querySelector("#best-table tbody");
    tbody.innerHTML = "";
    rows.forEach((r) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${r.origin} → ${r.destination}</td>
            <td>${r.departure_date}</td>
            <td>${r.return_date}</td>
            <td>${r.airline}</td>
            <td>${fmtBRL(r.price)}</td>
            <td>${r.direct ? "Sim" : "Não"}</td>
            <td><a href="${r.link}" target="_blank" rel="noopener">Ver</a></td>
        `;
        tbody.appendChild(tr);
    });
    return rows;
}

async function loadRecommendation() {
    const res = await fetch("/api/recommendation");
    const data = await res.json();
    const el = document.getElementById("recommendation-card").querySelector("#recommendation");
    const best = data.best_combination;
    if (!best) {
        el.textContent = "Ainda não há dados suficientes para recomendar.";
        return;
    }
    const rec = best.recommendation;
    el.parentElement.querySelector("#recommendation").className = `recommendation ${rec.color}`;
    el.innerHTML = `<b>${rec.label}</b> — ${rec.reason}<br>
        Melhor combo: ${best.origin} → ${best.destination}, ida ${best.departure_date} / volta ${best.return_date}
        (preço esperado ${fmtBRL(best.expected_price)}, confiança ${best.confidence}%)`;
}

let trendChart;
async function loadTrendChart(bestRows) {
    if (!bestRows || !bestRows.length) return;
    const top = bestRows[0];
    const res = await fetch(
        `/api/history?origin=${top.origin}&destination=${top.destination}` +
        `&departure_date=${top.departure_date}&return_date=${top.return_date}`
    );
    const history = await res.json();
    const labels = history.map((h) => new Date(h.timestamp).toLocaleString("pt-BR"));
    const prices = history.map((h) => h.price);

    const ctx = document.getElementById("trend-chart");
    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: `${top.origin} → ${top.destination}`,
                data: prices,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,.15)",
                tension: 0.3,
                fill: true,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#eef1f8" } } },
            scales: {
                x: { ticks: { color: "#8b93a7" }, grid: { color: "#212a3d" } },
                y: { ticks: { color: "#8b93a7" }, grid: { color: "#212a3d" } },
            },
        },
    });
}

async function refreshAll() {
    await loadStats();
    const bestRows = await loadBestCombinations();
    await loadRecommendation();
    await loadTrendChart(bestRows);
}

refreshAll();
setInterval(refreshAll, 60_000);
