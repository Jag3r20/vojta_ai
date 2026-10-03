from fastapi import FastAPI

from app.auth import router as auth_router

app = FastAPI(
    title="graph-tools",
    description="Nástroje pro zápis do Excelu a OneNotu v Microsoft 365 přes Microsoft Graph.",
    version="0.1.0",
)
app.include_router(auth_router)


@app.get("/health", operation_id="health")
def health() -> dict[str, str]:
    return {"status": "ok"}
