# 🎵 Vinyl Arbitrage Scanner

Bot automatico che scansiona Discogs ogni 3 ore cercando vinili sottoprezzati
con ROI ≥ 40% e li segnala via Telegram.

---

## 📁 Struttura file

```
vinyl-arbitrage-scanner/
├── scanner.py          ← Motore principale (entry point)
├── discogs_client.py   ← Tutte le chiamate API Discogs
├── scorer.py           ← Calcolo ROI, score 1-10, rarità
├── telegram_alerts.py  ← Notifiche Telegram
├── database.py         ← SQLite: opportunità, acquisti, vendite
├── config.py           ← Soglie di business e variabili env
├── watchlist.py        ← Artisti/label da monitorare
├── requirements.txt    ← Solo: requests
└── .github/
    └── workflows/
        └── scanner.yml ← GitHub Actions (esecuzione ogni 3h)
```

---

## 🚀 Setup — Guida Passo Passo

### PASSO 1 — Crea le API key (10 minuti)

#### Discogs Token (GRATIS)
1. Vai su https://www.discogs.com/settings/developers
2. Clicca **"Generate new token"**
3. Copia il token (es: `AbCdEfGhIjKlMnOpQrSt`)

#### Bot Telegram (GRATIS)
1. Apri Telegram e cerca **@BotFather**
2. Scrivi `/newbot`
3. Dai un nome al bot (es: `VinylArbitrage`) e un username (es: `vinyl_arb_bot`)
4. Copia il **token** (es: `7123456789:AABBccDDeeFFggHHiiJJkk...`)

#### Chat ID Telegram
1. Cerca su Telegram **@userinfobot**
2. Scrivi `/start`
3. Copia il numero "Id:" (es: `123456789`)

---

### PASSO 2 — Crea il repository su GitHub (5 minuti)

1. Vai su https://github.com/new
2. Nome repository: `vinyl-arbitrage-scanner`
3. Seleziona **Private**
4. Clicca **Create repository**

---

### PASSO 3 — Carica i file su GitHub (5 minuti)

Hai due opzioni:

**Opzione A — GitHub Web (più semplice)**
1. Nella pagina del tuo repository, clicca **"Add file" → "Upload files"**
2. Carica tutti i file della cartella (trascina tutto)
3. Clicca **Commit changes**
4. Per il file `.github/workflows/scanner.yml`, devi crearlo manualmente:
   - Clicca **"Add file" → "Create new file"**
   - Nome file: `.github/workflows/scanner.yml`
   - Incolla il contenuto del file
   - Commit

**Opzione B — Terminale (se hai Git installato)**
```bash
git clone https://github.com/TUO_USERNAME/vinyl-arbitrage-scanner.git
cd vinyl-arbitrage-scanner
# Copia tutti i file dentro questa cartella
git add .
git commit -m "Initial setup"
git push
```

---

### PASSO 4 — Aggiungi i Secrets su GitHub (3 minuti)

I secret sono le API key — non vanno mai nel codice!

1. Nel tuo repository GitHub, vai su **Settings → Secrets and variables → Actions**
2. Clicca **"New repository secret"** per ciascuno:

| Secret Name          | Valore                        |
|---------------------|-------------------------------|
| `DISCOGS_TOKEN`      | Il token Discogs copiato prima |
| `TELEGRAM_BOT_TOKEN` | Il token del bot Telegram      |
| `TELEGRAM_CHAT_ID`   | Il tuo ID Telegram numerico    |

---

### PASSO 5 — Primo test manuale (2 minuti)

1. Nel tuo repository, vai su **Actions**
2. Seleziona **"Vinyl Arbitrage Scanner"** dalla lista sinistra
3. Clicca **"Run workflow" → "Run workflow"**
4. Guarda i log in tempo reale mentre scansiona
5. Se tutto va bene, ricevi un messaggio Telegram!

Da questo momento il bot parte **automaticamente ogni 3 ore**.

---

## ⚙️ Personalizzazione

### Cambia la frequenza di scan
In `.github/workflows/scanner.yml`:
```yaml
# Ogni 3 ore (default)
- cron: "0 */3 * * *"

# Ogni ora
- cron: "0 * * * *"

# Due volte al giorno (alle 9 e alle 21)
- cron: "0 9,21 * * *"
```

### Cambia le soglie di business
In `config.py`:
```python
MIN_ROI = 0.40          # Alza a 0.50 per filtro più severo
MIN_PROFIT_EUR = 15.0   # Profitto minimo in euro
MIN_SCORE = 7.0         # Score minimo per alert (abbassa a 6 per più alert)
```

### Aggiungi un artista alla watchlist
In `watchlist.py`:
```python
{"name": "Nome Artista", "type": "artist", "id": DISCOGS_ARTIST_ID, "tier": "A"},
```
Per trovare l'ID Discogs di un artista:
1. Cerca l'artista su discogs.com
2. Guarda l'URL: `discogs.com/artist/53449-Miles-Davis` → ID = `53449`

---

## 💰 Registra acquisti e vendite

Lo scanner trova le opportunità, tu decidi se comprare.
Per tracciare i tuoi acquisti nel database, crea un file `track.py` e usa:

```python
from database import log_purchase, log_sale

# Hai comprato un disco trovato dal bot (opportunity_id dal DB)
log_purchase(
    opportunity_id=1,
    purchase_price=15.0,
    condition_received="Very Good Plus (VG+)",
    platform="discogs",
    shipping_in=5.50,
    notes="Ricevuto in ottime condizioni"
)

# Hai venduto quel disco (purchase_id dal DB)
log_sale(
    purchase_id=1,
    sale_price=48.0,
    platform="discogs",
    fees_paid=5.28,     # 11% di 48
    shipping_paid=7.0,
    notes="Venduto a buyer tedesco"
)
```

---

## 🔧 Troubleshooting

**Il bot non manda messaggi Telegram**
- Verifica che i secret siano scritti esattamente come in tabella
- Controlla che il bot non sia stato bloccato (manda `/start` al bot prima)
- Guarda i log in Actions per errori specifici

**Errore 401 da Discogs**
- Il token Discogs è scaduto o errato — rigeneralo e aggiorna il secret

**Nessuna opportunità trovata**
- Normale nelle prime ore: il db è vuoto e deve costruire storico
- Abbassa `MIN_SCORE` a 6.0 in `config.py` per vedere più risultati
- Controlla i log in Actions per vedere cosa analizza

**Rate limit Discogs (429)**
- Il bot lo gestisce automaticamente (attende 60 secondi)
- Se persiste, aumenta `RATE_LIMIT_SLEEP` a 2.0 in `config.py`

---

## 📊 Esempio di alert Telegram

```
🎵 VINYL ARBITRAGE ALERT

🎯 Score: 8.5/10
🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜

💿 Miles Davis — Kind of Blue
🏷️  Columbia · 1959 · UK
📀  Condizione: Near Mint (NM or M-)

━━━━━━━━━━━━━━━━━━━━
💸 ANALISI ECONOMICA
━━━━━━━━━━━━━━━━━━━━
• Prezzo listing:    €32.00
• Mediana Discogs:   €95.00
• Vendi stimato a:   €89.00
• Profitto netto:    €38.00
• ROI:              🔥 118%

━━━━━━━━━━━━━━━━━━━━
📊 MERCATO
━━━━━━━━━━━━━━━━━━━━
• Want: 4,821   |   In vendita: 3

━━━━━━━━━━━━━━━━━━━━
✨ SEGNALI RARITÀ
━━━━━━━━━━━━━━━━━━━━
  ✨ original uk
  ✨ first press (matrix A1/B1 detected)

👉 APRI LISTING SU DISCOGS
```

---

## 💡 Costo totale: €0

| Servizio        | Piano gratuito include             |
|----------------|------------------------------------|
| GitHub Actions | 2.000 minuti/mese (abbondanti)     |
| Discogs API    | 60 req/min autenticato             |
| Telegram Bot   | Illimitato                         |
