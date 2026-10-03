# Hlasový AI asistent pro Microsoft 365

Self-hosted chat (Open WebUI) s hlasovým vstupem, který na pokyn zapisuje do
Excelu a OneNotu v Microsoft 365 přes vlastní službu `graph-tools`.

Architektura a plán milníků jsou v zadání; tento README popisuje jen spuštění.

## Služby

- **open-webui** – chat, PWA, hlasový vstup
- **litellm** – brána k LLM, STT a TTS modelům, vnitřní síť (port 4000 není
  publikovaný na hostitele)
- **graph-tools** – jediná služba, která mluví s Microsoft Graph API
  (Excel, OneNote)

## Spuštění (lokální vývoj)

1. Zkopíruj `.env.example` do `.env` a vyplň chybějící hodnoty (viz
   komentáře uvnitř souboru). `GRAPH_TOOLS_API_KEY`, `TOKEN_ENCRYPTION_KEY`,
   `LITELLM_MASTER_KEY` a `WEBUI_SECRET_KEY` si můžeš vygenerovat:

   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Chat modely (`asistent-rychly`, `asistent-velky`) jsou nastavené na
   DeepSeek (`deepseek-chat` / `deepseek-reasoner`), přepis řeči (`prepis`)
   na Groq `whisper-large-v3-turbo` a hlasová odpověď (`hlas`) na OpenAI
   `tts-1`. Do `.env` vlož `LLM_API_KEY` (DeepSeek), `STT_API_KEY` (Groq, z
   `console.groq.com`) a `TTS_API_KEY` (OpenAI, z `platform.openai.com`).

3. Spusť:

   ```bash
   docker compose up -d
   ```

4. Ověř healthchecky:

   ```bash
   docker compose ps
   ```

   Všechny tři služby by měly být `healthy`.

5. Otevři `http://localhost:3000`, vytvoř první (jediný) účet a v
   **Admin Settings → Connections** ověř, že je vidět OpenAI-kompatibilní
   připojení na `http://litellm:4000/v1` s modely `asistent-rychly`,
   `asistent-velky`, `prepis`, `hlas`.

6. V **Admin Settings → Audio** nastav:
   - **Speech-to-Text**: engine OpenAI, API base URL `http://litellm:4000/v1`,
     API key = `LITELLM_MASTER_KEY`, model `prepis`, jazyk `cs`.
   - **Text-to-Speech**: engine OpenAI, API base URL `http://litellm:4000/v1`,
     API key = `LITELLM_MASTER_KEY`, model `hlas`, voice např. `alloy`.

   Browser-native TTS (Web Speech API) je nespolehlivé napříč platformami
   (hlavně Linux desktop bez systémových hlasů) – proto jde hlasová
   odpověď přes `hlas` model stejně jako STT, ne přes vestavěný hlas
   prohlížeče.

7. Po vytvoření prvního účtu vypni registraci v
   **Admin Settings → General → Enable New Sign Ups**.

Tool server pro `graph-tools` (Admin Settings → Tool Servers) se připojuje
až od milníku M3, kdy existují první nástroje k zavolání.

## Testy graph-tools

```bash
cd graph-tools
pip install -e ".[dev]"
pytest
```

## Milník M1 – stav

Hotovo a ověřeno end-to-end (chat, hlasový vstup i hlasová odpověď funkční
v prohlížeči):

- [x] `compose.yml`, `compose.prod.yml`, `.env.example`, `.gitignore`
- [x] `graph-tools` běží jako FastAPI služba s `/health`
- [x] `litellm/config.yaml` s aliasy `asistent-rychly`, `asistent-velky`, `prepis`, `hlas`
- [x] Chat modely na DeepSeek, přepis řeči na Groq `whisper-large-v3-turbo`,
  hlasová odpověď na OpenAI `tts-1`; všechny klíče vyplněné lokálně v `.env`
- [x] `docker compose up` ověřeno, všechny tři služby `healthy`
- [x] Admin nastavení v Open WebUI (Connections, Audio STT i TTS, vypnutí
  registrace) projito a otestováno živě přes voice mode

## Milník M2 – stav

- [x] `/auth/login`, `/auth/callback`, `/auth/status` (MSAL, authorization
  code flow, delegovaná oprávnění)
- [x] Token cache šifrovaná Fernetem (`TOKEN_ENCRYPTION_KEY`), uložená do
  `DATA_DIR/token_cache.bin`, přežije restart kontejneru
- [x] Chybějící `TENANT_ID`/`CLIENT_ID`/`CLIENT_SECRET` hlásí srozumitelnou
  českou chybu místo pádu
- [x] Testy (mockovaný MSAL): login redirect, chybějící/neplatný callback,
  úspěšný zápis šifrované cache, `/auth/status`
- [ ] Registrace aplikace v Entra (`docs/entra-setup.md`) – potřeba
  provést v tenantu, dokument je hotový, zbývá reálně projít a doplnit
  `TENANT_ID`/`CLIENT_ID`/`CLIENT_SECRET` do `.env`

Další kroky a provozní dokumentace: `docs/entra-setup.md` (M2),
`docs/deploy-vps.md` (M7), `docs/system-prompt.md`.
