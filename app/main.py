from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import auth, circulars, scraper, downloads, api_keys
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(circulars.router, prefix=f"{settings.API_V1_STR}/circulars", tags=["circulars"])
app.include_router(scraper.router, prefix=f"{settings.API_V1_STR}/scraper", tags=["scraper"])
app.include_router(downloads.router, prefix=f"{settings.API_V1_STR}/downloads", tags=["downloads"])
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api-keys", tags=["api-keys"])

@app.get("/")
def root():
    return {"message": "Welcome to RBI Circular Scrapper API"}
