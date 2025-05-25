from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime
import logging
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="ChopExpress API",
    description="Bot de Commande & Livraison via WhatsApp pour le Cameroun",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables d'environnement
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "chopexpress_verify_token")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
CINETPAY_API_KEY = os.getenv("CINETPAY_API_KEY", "")

@app.get("/")
async def root():
    """Point d'entrée principal de l'API"""
    return {
        "message": "ChopExpress API - Bot WhatsApp pour commandes et livraisons",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ChopExpress Backend",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Vérification du webhook WhatsApp (GET)"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    logger.info(f"Webhook verification - Mode: {mode}, Token: {token}")
    
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook vérifié avec succès")
        return int(challenge)
    else:
        logger.error("Échec de la vérification du webhook")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Réception des messages WhatsApp (POST)"""
    try:
        body = await request.json()
        logger.info(f"Message WhatsApp reçu: {body}")
        
        # Traitement des messages entrants
        if "entry" in body:
            for entry in body["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            await process_whatsapp_message(change["value"])
        
        return JSONResponse(content={"status": "success"}, status_code=200)
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

async def process_whatsapp_message(message_data: Dict[str, Any]):
    """Traitement des messages WhatsApp entrants"""
    try:
        if "messages" in message_data:
            for message in message_data["messages"]:
                phone_number = message["from"]
                message_type = message["type"]
                
                logger.info(f"Message de {phone_number}, type: {message_type}")
                
                if message_type == "text":
                    text_content = message["text"]["body"]
                    logger.info(f"Contenu du message: {text_content}")
                    
                    # Logique de traitement des commandes
                    await handle_text_message(phone_number, text_content)
                
                elif message_type == "interactive":
                    # Traitement des boutons et listes interactives
                    await handle_interactive_message(phone_number, message["interactive"])
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message: {str(e)}")

async def handle_text_message(phone_number: str, text: str):
    """Gestion des messages texte"""
    text_lower = text.lower().strip()
    
    # Commandes de base
    if text_lower in ["commander", "menu", "bonjour", "salut", "hi", "hello"]:
        await send_welcome_message(phone_number)
    elif text_lower in ["aide", "help"]:
        await send_help_message(phone_number)
    else:
        await send_default_response(phone_number, text)

async def handle_interactive_message(phone_number: str, interactive_data: Dict[str, Any]):
    """Gestion des messages interactifs (boutons, listes)"""
    logger.info(f"Message interactif de {phone_number}: {interactive_data}")
    # TODO: Implémenter la logique des interactions

async def send_welcome_message(phone_number: str):
    """Envoi du message de bienvenue"""
    logger.info(f"Envoi du message de bienvenue à {phone_number}")
    # TODO: Implémenter l'envoi via WhatsApp API

async def send_help_message(phone_number: str):
    """Envoi du message d'aide"""
    logger.info(f"Envoi du message d'aide à {phone_number}")
    # TODO: Implémenter l'envoi via WhatsApp API

async def send_default_response(phone_number: str, original_message: str):
    """Réponse par défaut pour les messages non reconnus"""
    logger.info(f"Réponse par défaut à {phone_number} pour: {original_message}")
    # TODO: Implémenter l'envoi via WhatsApp API

# Routes API pour le dashboard
@app.get("/api/restaurants")
async def get_restaurants():
    """Récupération de la liste des restaurants"""
    # TODO: Intégration Supabase
    return {"restaurants": []}

@app.get("/api/orders")
async def get_orders():
    """Récupération des commandes"""
    # TODO: Intégration Supabase
    return {"orders": []}

@app.post("/api/orders")
async def create_order(request: Request):
    """Création d'une nouvelle commande"""
    # TODO: Intégration Supabase + CinetPay
    return {"status": "created"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )