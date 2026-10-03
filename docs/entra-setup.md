# Registrace aplikace v Microsoft Entra (lokální vývoj)

Postup pro testovací tenant, se kterým se vyvíjí a testuje `graph-tools`
lokálně. Pro produkční nasazení na VPS proveď samostatnou registraci podle
`deploy-vps.md` (jiný redirect URI, souhlas správce v produkčním tenantu).

## 1. Registrace aplikace

1. Otevři [Microsoft Entra admin center](https://entra.microsoft.com) a
   přihlas se účtem s právy alespoň Application Developer.
2. **Identity → Applications → App registrations → New registration.**
3. **Name**: např. `vojta-ai-graph-tools-dev`.
4. **Supported account types**: **Accounts in this organizational directory
   only (Single tenant)** — odpovídá `GRAPH_SCOPES`/`TENANT_ID` v `.env`.
5. **Redirect URI**: platforma **Web**, hodnota
   `http://localhost:8000/auth/callback`.
6. Klikni **Register**.

## 2. Client secret

1. V aplikaci: **Manage → Certificates & secrets → Client secrets → New
   client secret**.
2. Popis libovolný, platnost např. 6 měsíců (po vypršení je potřeba
   vygenerovat nový a aktualizovat `.env`).
3. Hodnotu secretu zkopíruj **hned po vytvoření** (podruhé se nezobrazí) do
   `.env` jako `CLIENT_SECRET`.

## 3. API Permissions (delegovaná oprávnění)

1. **Manage → API permissions → Add a permission → Microsoft Graph →
   Delegated permissions.**
2. Přidej:
   - `User.Read`
   - `Files.ReadWrite.All`
   - `Notes.ReadWrite`
   - `offline_access` (obvykle přidané automaticky)
3. **Grant admin consent for \<tenant\>** → Yes. Bez tohoto kroku přihlášení
   skončí chybou `AADSTS65001` (souhlas nebyl udělen).

## 4. Hodnoty do `.env`

Z **Overview** stránky aplikace:

```
TENANT_ID=<Directory (tenant) ID>
CLIENT_ID=<Application (client) ID>
CLIENT_SECRET=<hodnota z kroku 2>
GRAPH_REDIRECT_URI=http://localhost:8000/auth/callback
GRAPH_SCOPES=User.Read Files.ReadWrite.All Notes.ReadWrite offline_access
```

## 5. Ověření přihlášení

1. `docker compose up -d` (pokud ještě neběží).
2. Otevři `http://localhost:8000/auth/login` v prohlížeči.
3. Přihlas se účtem z testovacího tenantu, odsouhlas oprávnění.
4. Po přesměrování zpět uvidíš „Přihlášeno" a můžeš okno zavřít.
5. Ověř stav: `curl http://localhost:8000/auth/status` →
   `{"logged_in": true, "account": "<tvůj e-mail>"}`.
6. Token cache se ukládá zašifrovaná (Fernet, klíč `TOKEN_ENCRYPTION_KEY`) do
   `data/graph-tools/token_cache.bin` a přežije restart kontejneru
   (`docker compose restart graph-tools`).

## Testovací data

Pro M3+ potřebuješ v OneDrive testovacího účtu:

- Soubor `Klienti-TEST.xlsx` s tabulkou (Vložit → Tabulka, ne jen rozsah
  buněk) nazvanou `Klienti`, sloupce: Jméno, Příjmení, Firma, Telefon,
  E-mail, Poznámka.
- OneNote sešit se sekcí `Poznámky`.
