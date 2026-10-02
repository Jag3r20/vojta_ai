# Hlasový AI asistent pro Microsoft 365

Self-hosted chat (Open WebUI) s hlasovým vstupem, který na pokyn zapisuje do
Excelu a OneNotu v Microsoft 365 přes vlastní službu `graph-tools`.

Architektura a plán milníků jsou v zadání; tento README popisuje jen spuštění.

## Služby

- **open-webui** – chat, PWA, hlasový vstup
- **litellm** – brána k LLM a STT modelům, vnitřní síť (port 4000 není
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
   DeepSeek (`deepseek-chat` / `deepseek-reasoner`) – do `.env` vlož
   `LLM_API_KEY` s DeepSeek klíčem. Přepis řeči (`prepis`) ještě čeká na
   vybraného STT poskytovatele – doplň model v `litellm/config.yaml` a
   `STT_API_KEY` v `.env`.

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
   `asistent-velky`, `prepis`.

6. V **Admin Settings → Audio → Speech-to-Text** nastav engine OpenAI,
   API base URL `http://litellm:4000/v1`, API key = `LITELLM_MASTER_KEY`,
   model `prepis`, jazyk `cs`.

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

- [x] `compose.yml`, `compose.prod.yml`, `.env.example`, `.gitignore`
- [x] `graph-tools` běží jako FastAPI služba s `/health`
- [x] `litellm/config.yaml` s aliasy `asistent-rychly`, `asistent-velky`, `prepis`
- [x] Chat modely nastavené na DeepSeek, `LLM_API_KEY` vyplněný lokálně v `.env`
- [ ] Přepis řeči – vyžaduje vybraného STT poskytovatele a `STT_API_KEY`

Další kroky a provozní dokumentace: `docs/entra-setup.md` (M2),
`docs/deploy-vps.md` (M7), `docs/system-prompt.md`.
