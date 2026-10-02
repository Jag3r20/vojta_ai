from fastapi import FastAPI

app = FastAPI(
    title="graph-tools",
    description="Nástroje pro zápis do Excelu a OneNotu v Microsoft 365 přes Microsoft Graph.",
    version="0.1.0",
)


@app.get("/health", operation_id="health")
def health() -> dict[str, str]:
    return {"status": "ok"}
