document.addEventListener('DOMContentLoaded', () => {
    const createBotBtn = document.getElementById('createBotBtn');
    const newBotIdInput = document.getElementById('newBotId');
    const datasetSelect = document.getElementById('datasetSelect');
    const botsContainer = document.getElementById('botsContainer');
    const globalMessage = document.getElementById('globalMessage');

    // Funzione per caricare i dataset disponibili
    async function loadDatasets() {
        try {
            const response = await fetch('/list_datasets');
            const datasets = await response.json();
            datasetSelect.innerHTML = datasets.map(d => `<option value="${d}">${d}</option>`).join('');
            if (datasets.length === 0) {
                datasetSelect.innerHTML = '<option value="">Nessun CSV trovato in /data</option>';
            }
        } catch (error) {
            console.error('Errore caricamento dataset:', error);
            datasetSelect.innerHTML = '<option value="">Errore caricamento</option>';
        }
    }

    // Funzione per mostrare messaggi globali
    function showMessage(msg, type = 'info') {
        globalMessage.textContent = msg;
        globalMessage.style.color = type === 'error' ? 'red' : (type === 'success' ? 'green' : 'black');
        setTimeout(() => { globalMessage.textContent = ''; }, 5000);
    }

    // Funzione per creare un nuovo bot
    async function createBot() {
        const botId = newBotIdInput.value.trim();
        const dataFile = datasetSelect.value;

        if (!botId) {
            showMessage('Inserisci un ID per il bot.', 'error');
            return;
        }
        if (!dataFile) {
            showMessage('Seleziona un dataset.', 'error');
            return;
        }

        createBotBtn.disabled = true;
        createBotBtn.textContent = 'Avvio in corso...';

        try {
            const response = await fetch('/start_bot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    bot_id: botId, 
                    data_file: dataFile,
                    symbol: dataFile.split('.')[0] // Usa il nome del file come simbolo di default
                })
            });
            const data = await response.json();

            if (response.ok) {
                showMessage(data.message, 'success');
                newBotIdInput.value = '';
                refreshDashboard();
            } else {
                showMessage(`Errore: ${data.message}`, 'error');
            }
        } catch (error) {
            showMessage(`Errore di rete: ${error.message}`, 'error');
        } finally {
            createBotBtn.disabled = false;
            createBotBtn.textContent = 'Avvia Nuovo Bot';
        }
    }

    // Funzione per fermare un bot specifico
    async function stopBot(botId) {
        if (!confirm(`Sei sicuro di voler fermare il bot ${botId}?`)) return;

        try {
            const response = await fetch('/stop_bot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bot_id: botId })
            });
            const data = await response.json();

            if (response.ok) {
                showMessage(data.message, 'success');
                refreshDashboard();
            } else {
                showMessage(`Errore stop: ${data.message}`, 'error');
            }
        } catch (error) {
            showMessage(`Errore di rete stop: ${error.message}`, 'error');
        }
    }

    // Funzione principale di aggiornamento dashboard
    async function refreshDashboard() {
        try {
            const response = await fetch('/status');
            const botsData = await response.json();

            if (Object.keys(botsData).length === 0) {
                botsContainer.innerHTML = '<p style="color: #777;">Nessun bot attivo al momento.</p>';
                return;
            }

            let htmlContent = '';
            for (const [botId, data] of Object.entries(botsData)) {
                const statusColor = data.bot_running ? 'green' : 'red';
                const statusText = data.bot_running ? 'In Esecuzione' : 'Fermo/Errore';
                
                const portfolio = data.portfolio_value ? parseFloat(data.portfolio_value).toFixed(2) : '--';
                const lastPrice = data.last_close ? parseFloat(data.last_close).toFixed(4) : '--';
                
                // Genera HTML per i log
                const logsHtml = (data.recent_logs || []).map(log => 
                    `<div class="log-entry">${log}</div>`
                ).reverse().join(''); // Reverse per vedere i più recenti in alto

                htmlContent += `
                    <div class="bot-card" id="card-${botId}">
                        <div class="bot-header">
                            <span class="bot-title">${botId}</span>
                            <span class="bot-status" style="color: ${statusColor}">${statusText}</span>
                        </div>
                        <div class="bot-metrics">
                            <span class="metric-label">Portafoglio:</span>
                            <span class="metric-value">${portfolio}</span>
                            <span class="metric-label">Ultimo Prezzo:</span>
                            <span class="metric-value">${lastPrice}</span>
                        </div>
                        <div class="logs-container">
                            ${logsHtml || '<div style="color: #555;">In attesa di log...</div>'}
                        </div>
                        <button class="btn-stop" onclick="window.stopBotDelegated('${botId}')">Ferma Bot</button>
                    </div>
                `;
            }
            botsContainer.innerHTML = htmlContent;

        } catch (error) {
            console.error('Errore aggiornamento dashboard:', error);
        }
    }

    // Event Listeners
    if (createBotBtn) {
        createBotBtn.addEventListener('click', createBot);
    }

    window.stopBotDelegated = stopBot;

    // Inizializzazione
    loadDatasets();
    setInterval(refreshDashboard, 2000);
    refreshDashboard();
});
