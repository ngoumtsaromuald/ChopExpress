from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import os
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
# import ChopExpress.backend.models as models # Commenté car nous utilisons principalement l'API Supabase
import ChopExpress.backend.schemas as schemas

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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
CINETPAY_API_KEY = os.getenv("CINETPAY_API_KEY")

# Initialisation du client Supabase
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    logger.error("SUPABASE_URL et/ou SUPABASE_KEY ne sont pas configurés. Le client Supabase ne sera pas initialisé.")

@app.get("/")
async def root():
    return {
        "message": "ChopExpress API - Bot WhatsApp pour commandes et livraisons",
        "version": "1.0.0",
        "status": "active" if supabase else "degraded (Supabase non configuré)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    db_status = "non configuré"
    if supabase:
        try:
            # Pour un vrai test de santé, vous pourriez vouloir faire une petite requête.
            # Par exemple, essayer de lister les tables ou une vérification similaire.
            # Pour l'instant, si le client est là, on suppose une configuration basique.
            # Note: ceci ne vérifie pas la validité des identifiants ou la connectivité réseau.
            test_query = supabase.table("users").select("id").limit(1).execute()
            # Si la requête ci-dessus ne lève pas d'exception, on considère que c'est bon.
            db_status = "connecté"
        except Exception as e:
            logger.error(f"Erreur de connexion à Supabase lors du health check: {e}")
            db_status = "erreur de connexion"
            
    return {
        "status": "healthy" if db_status == "connecté" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "service": "ChopExpress Backend",
        "dependencies": {
            "supabase_database": db_status
        },
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    logger.info(f"Vérification du Webhook - Mode: {mode}, Token reçu: {token}")
    
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook vérifié avec succès.")
        return challenge
    else:
        logger.error(f"Échec de la vérification du Webhook. Mode: {mode}, Token Attendu: {WHATSAPP_VERIFY_TOKEN}, Token Reçu: {token}")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        body = await request.json()
        logger.info(f"Message WhatsApp reçu: {body}")
        
        if "entry" in body:
            for entry in body["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            await process_whatsapp_message(change["value"])
        
        return JSONResponse(content={"status": "success"}, status_code=200)
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {str(e)}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": "Internal Server Error"}, status_code=500)

async def get_or_create_user(phone_number: str, name: Optional[str] = None) -> schemas.User:
    if not supabase:
        logger.error("Supabase client non initialisé dans get_or_create_user.")
        raise Exception("Supabase client non initialisé.")
    try:
        response = supabase.table("users").select("*").eq("phone_number", phone_number).maybe_single().execute()
        
        if response.data:
            logger.info(f"Utilisateur trouvé: {response.data['id']} pour le numéro {phone_number}")
            return schemas.User.model_validate(response.data)
        else:
            logger.info(f"Utilisateur non trouvé pour le numéro {phone_number}. Création...")
            user_data_to_create = {"phone_number": phone_number}
            if name:
                user_data_to_create["name"] = name
            
            insert_response = supabase.table("users").insert(user_data_to_create).execute()
            
            if insert_response.data:
                created_user_data = insert_response.data[0]
                logger.info(f"Utilisateur créé: {created_user_data['id']} pour le numéro {phone_number}")
                return schemas.User.model_validate(created_user_data)
            else:
                error_msg = f"Échec de la création de l'utilisateur pour {phone_number}. Aucune donnée retournée par Supabase."
                logger.error(error_msg)
                raise Exception(error_msg) 
                
    except Exception as e:
        logger.error(f"Erreur dans get_or_create_user pour {phone_number}: {str(e)}", exc_info=True)
        raise

async def process_whatsapp_message(message_data: Dict[str, Any]):
    if not supabase:
        logger.error("Supabase client non initialisé. Impossible de traiter le message WhatsApp.")
        return

    try:
        if "messages" in message_data:
            for message in message_data["messages"]:
                phone_number = message["from"]
                message_type = message["type"]
                
                logger.info(f"Message de {phone_number}, type: {message_type}")
                
                current_user: Optional[schemas.User] = None
                try:
                    current_user = await get_or_create_user(phone_number)
                    logger.info(f"Utilisateur {current_user.id} (tél: {phone_number}) traité/créé.")
                except Exception as user_exc:
                    logger.error(f"Échec de get_or_create_user pour {phone_number}: {str(user_exc)}. Le message ne sera pas traité.", exc_info=True)
                    return # Arrêter si l'utilisateur ne peut être identifié

                if message_type == "text":
                    text_content = message["text"]["body"]
                    logger.info(f"Contenu du message: {text_content}")
                    await handle_text_message(current_user, phone_number, text_content)
                
                elif message_type == "interactive":
                    # TODO: Implémenter la gestion des messages interactifs
                    await handle_interactive_message(current_user, phone_number, message["interactive"])
    
    except Exception as e:
        logger.error(f"Erreur majeure lors du traitement du message WhatsApp: {str(e)}", exc_info=True)

async def handle_text_message(user: schemas.User, phone_number: str, text: str):
    text_lower = text.lower().strip()
    logger.info(f"Gestion du message texte de l'utilisateur {user.id} ({phone_number}): '{text_lower}'")
    
    # TODO: Implémenter la logique de conversation du bot (menu, commande, etc.)
    if text_lower in ["commander", "menu", "bonjour", "salut", "hi", "hello"]:
        await send_welcome_message(phone_number)
    elif text_lower in ["aide", "help"]:
        await send_help_message(phone_number)
    else:
        await send_default_response(phone_number, text)

async def handle_interactive_message(user: schemas.User, phone_number: str, interactive_data: Dict[str, Any]):
    logger.info(f"Gestion du message interactif de l'utilisateur {user.id} ({phone_number}): {interactive_data}")
    # TODO: Implémenter la logique des interactions (boutons, listes)

async def send_welcome_message(phone_number: str):
    logger.info(f"Envoi du message de bienvenue à {phone_number}")
    # TODO: Implémenter l'envoi via l'API WhatsApp Business

async def send_help_message(phone_number: str):
    logger.info(f"Envoi du message d'aide à {phone_number}")
    # TODO: Implémenter l'envoi via l'API WhatsApp Business

async def send_default_response(phone_number: str, original_message: str):
    logger.info(f"Réponse par défaut à {phone_number} pour: '{original_message}'")
    # TODO: Implémenter l'envoi via l'API WhatsApp Business

# --- Endpoints pour Restaurants (Tableau de bord Admin) ---
@app.get("/api/restaurants", response_model=schemas.RestaurantListResponse)
async def get_restaurants_api(): # Renommé pour éviter conflit avec variable globale
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        response = supabase.table("restaurants").select("*").eq("is_active", True).execute()
        restaurant_list = [schemas.Restaurant.model_validate(r_data) for r_data in response.data] if response.data else []
        return schemas.RestaurantListResponse(restaurants=restaurant_list)
    except Exception as e:
        logger.error(f"Erreur API - Récupération des restaurants: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.post("/api/restaurants", response_model=schemas.Restaurant, status_code=201)
async def create_restaurant_api(restaurant_data: schemas.RestaurantCreate): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        restaurant_dict = restaurant_data.model_dump()
        response = supabase.table("restaurants").insert(restaurant_dict).execute()
        if response.data:
            return schemas.Restaurant.model_validate(response.data[0])
        else:
            logger.error(f"API Erreur - Insertion restaurant n'a pas retourné de données. Supabase response: {response}")
            raise HTTPException(status_code=400, detail="Impossible de créer le restaurant.")
    except Exception as e: # Attraper une exception plus générique au cas où la réponse Supabase n'est pas comme attendue
        logger.error(f"Erreur API - Création restaurant: {str(e)}", exc_info=True)
        if "duplicate key value violates unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Un restaurant avec des informations similaires (ex: numéro WhatsApp) existe déjà.")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.get("/api/restaurants/{restaurant_id}", response_model=schemas.Restaurant)
async def get_restaurant_by_id_api(restaurant_id: int): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        response = supabase.table("restaurants").select("*").eq("id", restaurant_id).eq("is_active", True).maybe_single().execute()
        if response.data:
            return schemas.Restaurant.model_validate(response.data)
        else:
            raise HTTPException(status_code=404, detail=f"Restaurant ID {restaurant_id} non trouvé ou inactif.")
    except Exception as e:
        logger.error(f"Erreur API - Récupération restaurant ID {restaurant_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.put("/api/restaurants/{restaurant_id}", response_model=schemas.Restaurant)
async def update_restaurant_api(restaurant_id: int, restaurant_data: schemas.RestaurantUpdate): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        update_dict = restaurant_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="Aucune donnée fournie pour la mise à jour.")
        
        check_exists = supabase.table("restaurants").select("id").eq("id", restaurant_id).maybe_single().execute()
        if not check_exists.data:
            raise HTTPException(status_code=404, detail=f"Restaurant ID {restaurant_id} non trouvé.")

        response = supabase.table("restaurants").update(update_dict).eq("id", restaurant_id).execute()
        if response.data:
            return schemas.Restaurant.model_validate(response.data[0])
        else:
            logger.warning(f"API MàJ restaurant ID {restaurant_id} n'a pas retourné de données, mais restaurant existe. Supabase resp: {response}")
            # Cela peut arriver si RLS empêche de voir le résultat de l'update. Récupérer à nouveau pour confirmer.
            refetched_data = supabase.table("restaurants").select("*").eq("id", restaurant_id).maybe_single().execute()
            if refetched_data.data:
                return schemas.Restaurant.model_validate(refetched_data.data)
            raise HTTPException(status_code=400, detail="Impossible de mettre à jour ou récupérer le restaurant après MàJ.")
    except Exception as e:
        logger.error(f"Erreur API - MàJ restaurant ID {restaurant_id}: {str(e)}", exc_info=True)
        if "duplicate key value violates unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Conflit de données (ex: numéro WhatsApp).")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.delete("/api/restaurants/{restaurant_id}", status_code=204)
async def delete_restaurant_api(restaurant_id: int): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        check_response = supabase.table("restaurants").select("id, is_active").eq("id", restaurant_id).maybe_single().execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail=f"Restaurant ID {restaurant_id} non trouvé.")
        if not check_response.data["is_active"]:
            return 
            
        response = supabase.table("restaurants").update({"is_active": False}).eq("id", restaurant_id).execute()
        if not response.data: 
            logger.error(f"API Échec désactivation restaurant ID {restaurant_id}. Supabase resp: {response}")
            raise HTTPException(status_code=500, detail="Impossible de désactiver le restaurant.")
        return
    except Exception as e:
        logger.error(f"Erreur API - Suppression logique restaurant ID {restaurant_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

# --- Endpoints pour MenuItems (Tableau de bord Admin) ---
@app.post("/api/restaurants/{restaurant_id}/menu-items", response_model=schemas.MenuItem, status_code=201)
async def create_menu_item_for_restaurant_api(restaurant_id: int, menu_item_data: schemas.MenuItemCreate): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        r_response = supabase.table("restaurants").select("id").eq("id", restaurant_id).eq("is_active", True).maybe_single().execute()
        if not r_response.data:
            raise HTTPException(status_code=404, detail=f"Restaurant parent ID {restaurant_id} non trouvé ou inactif.")

        menu_item_dict = menu_item_data.model_dump()
        menu_item_dict["restaurant_id"] = restaurant_id
        
        response = supabase.table("menu_items").insert(menu_item_dict).execute()
        if response.data:
            return schemas.MenuItem.model_validate(response.data[0])
        else:
            logger.error(f"API Erreur - Insertion menu item n'a pas retourné de données. Supabase resp: {response}")
            raise HTTPException(status_code=400, detail="Impossible de créer l'article de menu.")
    except Exception as e:
        logger.error(f"Erreur API - Création menu item pour restaurant ID {restaurant_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.get("/api/restaurants/{restaurant_id}/menu-items", response_model=schemas.MenuItemListResponse)
async def list_menu_items_for_restaurant_api(restaurant_id: int): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        r_response = supabase.table("restaurants").select("id").eq("id", restaurant_id).eq("is_active", True).maybe_single().execute()
        if not r_response.data:
            raise HTTPException(status_code=404, detail=f"Restaurant parent ID {restaurant_id} non trouvé ou inactif.")

        response = supabase.table("menu_items").select("*").eq("restaurant_id", restaurant_id).eq("is_available", True).execute()
        menu_item_list = [schemas.MenuItem.model_validate(item) for item in response.data] if response.data else []
        return schemas.MenuItemListResponse(menu_items=menu_item_list)
    except Exception as e:
        logger.error(f"Erreur API - Listage menu items pour restaurant ID {restaurant_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.get("/api/menu-items/{item_id}", response_model=schemas.MenuItem)
async def get_menu_item_by_id_api(item_id: int): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        response = supabase.table("menu_items").select("*, restaurants(is_active)").eq("id", item_id).eq("is_available", True).maybe_single().execute()
        
        if response.data:
            # Vérifier si le restaurant parent est actif via la jointure (restaurants(is_active))
            # La structure de response.data avec jointure : response.data['restaurants']['is_active']
            if not response.data.get("restaurants") or not response.data["restaurants"]["is_active"]:
                 raise HTTPException(status_code=403, detail=f"L'article de menu ID {item_id} appartient à un restaurant inactif.")
            
            # Retirer la donnée de jointure 'restaurants' avant validation si elle n'est pas dans le schéma MenuItem
            item_data_for_validation = {k: v for k, v in response.data.items() if k != 'restaurants'}
            return schemas.MenuItem.model_validate(item_data_for_validation)
        else:
            raise HTTPException(status_code=404, detail=f"Article de menu ID {item_id} non trouvé ou indisponible.")
    except Exception as e:
        logger.error(f"Erreur API - Récupération menu item ID {item_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.put("/api/menu-items/{item_id}", response_model=schemas.MenuItem)
async def update_menu_item_api(item_id: int, item_data: schemas.MenuItemUpdate): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        update_dict = item_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="Aucune donnée fournie pour la mise à jour.")
        
        check_exists = supabase.table("menu_items").select("id, restaurant_id").eq("id", item_id).maybe_single().execute()
        if not check_exists.data:
            raise HTTPException(status_code=404, detail=f"Article de menu ID {item_id} non trouvé.")
        
        # Vérifier si le restaurant parent est actif avant de permettre la MàJ de l'item
        parent_restaurant_id = check_exists.data["restaurant_id"]
        parent_r_active = supabase.table("restaurants").select("id").eq("id", parent_restaurant_id).eq("is_active", True).maybe_single().execute()
        if not parent_r_active.data:
            raise HTTPException(status_code=403, detail=f"Impossible de mettre à jour l'article car son restaurant (ID: {parent_restaurant_id}) est inactif.")

        response = supabase.table("menu_items").update(update_dict).eq("id", item_id).execute()
        if response.data:
            return schemas.MenuItem.model_validate(response.data[0])
        else:
            logger.warning(f"API MàJ menu item ID {item_id} n'a pas retourné de données. Supabase resp: {response}")
            refetched_data = supabase.table("menu_items").select("*").eq("id", item_id).maybe_single().execute()
            if refetched_data.data:
                return schemas.MenuItem.model_validate(refetched_data.data)
            raise HTTPException(status_code=400, detail="Impossible de mettre à jour ou récupérer l'article après MàJ.")
    except Exception as e:
        logger.error(f"Erreur API - MàJ menu item ID {item_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.delete("/api/menu-items/{item_id}", status_code=204)
async def delete_menu_item_api(item_id: int): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        check_response = supabase.table("menu_items").select("id, is_available").eq("id", item_id).maybe_single().execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail=f"Article de menu ID {item_id} non trouvé.")
        if not check_response.data["is_available"]:
            return 
            
        response = supabase.table("menu_items").update({"is_available": False}).eq("id", item_id).execute()
        if not response.data:
            logger.error(f"API Échec désactivation menu item ID {item_id}. Supabase resp: {response}")
            raise HTTPException(status_code=500, detail="Impossible de désactiver l'article de menu.")
        return
    except Exception as e:
        logger.error(f"Erreur API - Suppression logique menu item ID {item_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

# --- Endpoints pour Users (Tableau de bord Admin) ---
@app.get("/api/users", response_model=schemas.UserListResponse)
async def list_users_api(): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        response = supabase.table("users").select("*").execute()
        user_list = [schemas.User.model_validate(u_data) for u_data in response.data] if response.data else []
        return schemas.UserListResponse(users=user_list)
    except Exception as e:
        logger.error(f"Erreur API - Listage utilisateurs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.get("/api/users/{user_id}", response_model=schemas.User)
async def get_user_by_id_api(user_id: int): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        response = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()
        if response.data:
            return schemas.User.model_validate(response.data)
        else:
            raise HTTPException(status_code=404, detail=f"Utilisateur ID {user_id} non trouvé.")
    except Exception as e:
        logger.error(f"Erreur API - Récupération utilisateur ID {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

@app.post("/api/users", response_model=schemas.User, status_code=201)
async def create_user_api(user_data: schemas.UserCreate): # Renommé
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        existing_user_check = supabase.table("users").select("id").eq("phone_number", user_data.phone_number).maybe_single().execute()
        if existing_user_check.data:
            raise HTTPException(status_code=409, detail=f"Un utilisateur avec le numéro de téléphone {user_data.phone_number} existe déjà.")

        new_user_dict = user_data.model_dump()
        response = supabase.table("users").insert(new_user_dict).execute()
        if response.data:
            return schemas.User.model_validate(response.data[0])
        else:
            logger.error(f"API Erreur - Insertion utilisateur via endpoint n'a pas retourné de données. Supabase resp: {response}")
            raise HTTPException(status_code=400, detail="Impossible de créer l'utilisateur.")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Erreur API - Création utilisateur via endpoint: {str(e)}", exc_info=True)
        if "duplicate key value violates unique constraint" in str(e).lower(): # Devrait être intercepté par la vérification ci-dessus
            raise HTTPException(status_code=409, detail=f"Un utilisateur avec le numéro de téléphone {user_data.phone_number} existe déjà (contrainte DB).")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

# --- Endpoints pour Orders (Tableau de bord Admin & Bot) ---
@app.post("/api/orders", response_model=schemas.Order, status_code=201)
async def create_order_api(order_data: schemas.OrderCreate, current_user_id: int): # current_user_id à remplacer par auth
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    
    try:
        # 1. Valider l'existence et l'activité du client (utilisateur)
        user_response = supabase.table("users").select("id").eq("id", current_user_id).maybe_single().execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail=f"Client avec ID {current_user_id} non trouvé.")

        # 2. Valider l'existence et l'activité du restaurant
        restaurant_response = supabase.table("restaurants").select("id, is_active").eq("id", order_data.restaurant_id).maybe_single().execute()
        if not restaurant_response.data:
            raise HTTPException(status_code=404, detail=f"Restaurant ID {order_data.restaurant_id} non trouvé.")
        if not restaurant_response.data["is_active"]:
            raise HTTPException(status_code=400, detail=f"Le restaurant ID {order_data.restaurant_id} est actuellement inactif.")

        if not order_data.items:
            raise HTTPException(status_code=400, detail="Une commande doit contenir au moins un article.")

        order_items_to_create_db = []
        calculated_total_amount = 0.0

        # 3. Valider chaque article de la commande et calculer le prix
        for item_in_payload in order_data.items:
            menu_item_response = supabase.table("menu_items") \
                .select("id, name, price, is_available, restaurant_id") \
                .eq("id", item_in_payload.menu_item_id) \
                .maybe_single().execute()
            
            if not menu_item_response.data:
                raise HTTPException(status_code=404, detail=f"Article de menu ID {item_in_payload.menu_item_id} non trouvé.")
            
            menu_item_db = menu_item_response.data
            if not menu_item_db["is_available"]:
                raise HTTPException(status_code=400, detail=f"L'article '{menu_item_db['name']}' (ID: {menu_item_db['id']}) n'est plus disponible.")
            if menu_item_db["restaurant_id"] != order_data.restaurant_id:
                 raise HTTPException(status_code=400, detail=f"L'article '{menu_item_db['name']}' (ID: {menu_item_db['id']}) n'appartient pas au restaurant ID {order_data.restaurant_id}.")

            price_at_order = menu_item_db["price"]
            calculated_total_amount += price_at_order * item_in_payload.quantity
            
            order_items_to_create_db.append({
                "menu_item_id": item_in_payload.menu_item_id,
                "quantity": item_in_payload.quantity,
                "price_at_order": price_at_order, # Prix au moment de la commande
                "notes": item_in_payload.notes
            })
        
        # 4. Créer l'enregistrement Order principal
        # Note: customer_id est current_user_id pour l'instant
        order_header_payload = {
            "customer_id": current_user_id, 
            "restaurant_id": order_data.restaurant_id,
            "total_amount": calculated_total_amount,
            "status": "pending", # Statut initial par défaut
            "payment_status": "pending", # Statut de paiement initial par défaut
            "delivery_address": order_data.delivery_address,
            "delivery_latitude": order_data.delivery_latitude,
            "delivery_longitude": order_data.delivery_longitude,
            "notes": order_data.notes
        }
        order_header_insert_response = supabase.table("orders").insert(order_header_payload).execute()

        if not order_header_insert_response.data or not order_header_insert_response.data[0]:
            logger.error(f"Échec création en-tête commande pour client {current_user_id}. Supabase: {order_header_insert_response}")
            raise HTTPException(status_code=500, detail="Impossible de créer l'en-tête de la commande.")
        
        created_order_header_db = order_header_insert_response.data[0]
        new_order_id = created_order_header_db["id"]

        # 5. Créer les OrderItems associés
        for item_db_payload in order_items_to_create_db:
            item_db_payload["order_id"] = new_order_id
        
        order_items_insert_response = supabase.table("order_items").insert(order_items_to_create_db).execute()

        if not order_items_insert_response.data or len(order_items_insert_response.data) != len(order_items_to_create_db):
            logger.error(f"Échec insertion articles pour commande ID {new_order_id}. Supabase: {order_items_insert_response}. Tentative d'annulation de l'en-tête.")
            # Tentative de compensation : supprimer l'en-tête de commande créé
            supabase.table("orders").delete().eq("id", new_order_id).execute()
            raise HTTPException(status_code=500, detail="Impossible de créer tous les articles de la commande. La commande a été annulée.")

        # 6. Préparer la réponse : combiner l'en-tête de commande et les articles créés
        # Les données des articles créés sont dans order_items_insert_response.data
        created_order_items_for_response = [schemas.OrderItem.model_validate(item) for item in order_items_insert_response.data]
        
        # Construire l'objet Order Pydantic complet pour la réponse
        final_order_response_data = {**created_order_header_db, "items": created_order_items_for_response}
        
        return schemas.Order.model_validate(final_order_response_data)

    except HTTPException as http_exc:
        raise http_exc # Repropager les erreurs HTTP déjà formatées
    except Exception as e:
        logger.error(f"Erreur majeure API - Création commande pour client {current_user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur lors de la création de la commande.")

@app.get("/api/orders", response_model=schemas.OrderListResponse)
async def list_orders_api(): # Renommé pour clarté
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        # Récupérer tous les en-têtes de commande, triés par date de création (plus récent d'abord)
        orders_header_response = supabase.table("orders").select("*").order("created_at", desc=True).execute()
        
        if not orders_header_response.data:
            return schemas.OrderListResponse(orders=[]) # Retourner une liste vide si aucune commande

        orders_for_response = []
        for order_header_db in orders_header_response.data:
            order_id = order_header_db["id"]
            
            # Récupérer les articles pour cette commande spécifique
            # Idéalement, cela devrait être fait avec une jointure Supabase `select("*, order_items(*)")`
            # Mais pour la clarté et pour s'assurer de la compatibilité avec Pydantic, faisons-le séparément pour l'instant.
            items_response = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
            
            order_items_list_for_response = []
            if items_response.data:
                order_items_list_for_response = [schemas.OrderItem.model_validate(item) for item in items_response.data]
            
            # Combiner l'en-tête de commande et ses articles
            # S'assurer que tous les champs requis par schemas.Order sont présents dans order_header_db
            # ou sont ajoutés/transformés ici.
            full_order_data_for_validation = {**order_header_db, "items": order_items_list_for_response}
            orders_for_response.append(schemas.Order.model_validate(full_order_data_for_validation))
            
        return schemas.OrderListResponse(orders=orders_for_response)

    except Exception as e:
        logger.error(f"Erreur API - Listage de toutes les commandes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur lors du listage des commandes.")

@app.get("/api/orders/{order_id}", response_model=schemas.Order)
async def get_order_by_id_api(order_id: int):
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        # Récupérer l'en-tête de la commande
        # Idéalement, utiliser Supabase select("*, order_items(*)") pour une seule requête
        order_header_response = supabase.table("orders").select("*").eq("id", order_id).maybe_single().execute()

        if not order_header_response.data:
            raise HTTPException(status_code=404, detail=f"Commande avec ID {order_id} non trouvée.")

        order_header_db = order_header_response.data

        # Récupérer les articles associés à cette commande
        items_response = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
        
        order_items_list_for_response = []
        if items_response.data:
            order_items_list_for_response = [schemas.OrderItem.model_validate(item) for item in items_response.data]
        
        # Combiner l'en-tête et les articles pour la réponse
        full_order_data_for_validation = {**order_header_db, "items": order_items_list_for_response}
        
        return schemas.Order.model_validate(full_order_data_for_validation)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Erreur API - Récupération de la commande ID {order_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur lors de la récupération de la commande.")

@app.put("/api/orders/{order_id}", response_model=schemas.Order)
async def update_order_api(order_id: int, order_update_data: schemas.OrderUpdate):
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        update_dict = order_update_data.model_dump(exclude_unset=True) # Ne met à jour que les champs fournis

        if not update_dict:
            raise HTTPException(status_code=400, detail="Aucune donnée fournie pour la mise à jour.")

        # Vérifier d'abord si la commande existe
        check_order_exists = supabase.table("orders").select("id").eq("id", order_id).maybe_single().execute()
        if not check_order_exists.data:
            raise HTTPException(status_code=404, detail=f"Commande avec ID {order_id} non trouvée.")

        # Appliquer la mise à jour
        # La colonne updated_at devrait être gérée automatiquement par le trigger `moddatetime` dans la DB
        update_response = supabase.table("orders").update(update_dict).eq("id", order_id).execute()

        if not update_response.data or not update_response.data[0]:
            logger.error(f"API Erreur - Mise à jour commande ID {order_id} n'a pas retourné de données. Supabase: {update_response}")
            # Tenter de récupérer la commande pour voir si la mise à jour a eu lieu malgré tout (RLS, etc.)
            refetched_order = supabase.table("orders").select("*").eq("id", order_id).maybe_single().execute()
            if refetched_order.data:
                # Si elle est récupérée, il faut aussi récupérer ses items pour la réponse complète
                items_response = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
                order_items_list = [schemas.OrderItem.model_validate(item) for item in items_response.data] if items_response.data else []
                full_order_data = {**refetched_order.data, "items": order_items_list}
                return schemas.Order.model_validate(full_order_data)
            raise HTTPException(status_code=500, detail="Impossible de mettre à jour la commande ou de récupérer ses données après tentative.")

        updated_order_header_db = update_response.data[0]

        # Récupérer les articles pour la réponse complète (car ils ne sont pas dans updated_order_header_db)
        items_response = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
        order_items_list_for_response = []
        if items_response.data:
            order_items_list_for_response = [schemas.OrderItem.model_validate(item) for item in items_response.data]
        
        full_updated_order_data = {**updated_order_header_db, "items": order_items_list_for_response}
        
        return schemas.Order.model_validate(full_updated_order_data)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Erreur API - Mise à jour de la commande ID {order_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur lors de la mise à jour de la commande.")

@app.delete("/api/orders/{order_id}", response_model=schemas.Order)
async def cancel_order_api(order_id: int):
    if not supabase: raise HTTPException(status_code=503, detail="Service Supabase non disponible.")
    try:
        # Vérifier d'abord si la commande existe
        check_order_response = supabase.table("orders").select("id, status").eq("id", order_id).maybe_single().execute()
        if not check_order_response.data:
            raise HTTPException(status_code=404, detail=f"Commande avec ID {order_id} non trouvée.")

        current_status = check_order_response.data["status"]
        # Idéalement, vérifier si la commande peut être annulée (par exemple, pas si elle est déjà "delivered" ou "cancelled")
        if current_status in ["delivered", "cancelled"]:
            # Retourner la commande actuelle sans la modifier si elle ne peut être annulée
            # Pour cela, il faut récupérer tous les détails, y compris les items
            items_response = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
            order_items = [schemas.OrderItem.model_validate(item) for item in items_response.data] if items_response.data else []
            full_order_data = {**check_order_response.data, "items": order_items} 
            # Il faut s'assurer que check_order_response.data contient tous les champs de OrderBase
            # Pour être sûr, on pourrait refaire un select("*") ici.
            complete_order_data_resp = supabase.table("orders").select("*").eq("id", order_id).maybe_single().execute()
            if complete_order_data_resp.data:
                 full_order_data = {**complete_order_data_resp.data, "items": order_items}
                 validated_order = schemas.Order.model_validate(full_order_data)
                 raise HTTPException(status_code=400, 
                                   detail=f"Impossible d'annuler la commande ID {order_id} car son statut est déjà '{current_status}'.",
                                   headers={"X-Current-Order-State": validated_order.model_dump_json()})
            else: # Ne devrait pas arriver si le premier check a fonctionné
                 raise HTTPException(status_code=404, detail=f"Commande ID {order_id} trouvée puis perdue.")

        # Mettre à jour le statut à "cancelled"
        update_data = {"status": "cancelled"}
        # updated_at sera géré par le trigger moddatetime
        update_response = supabase.table("orders").update(update_data).eq("id", order_id).execute()

        if not update_response.data or not update_response.data[0]:
            logger.error(f"API Erreur - Annulation commande ID {order_id} n'a pas retourné de données. Supabase: {update_response}")
            raise HTTPException(status_code=500, detail="Impossible d'annuler la commande ou de récupérer ses données après tentative.")

        cancelled_order_header_db = update_response.data[0]

        # Récupérer les articles pour la réponse complète
        items_response = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
        order_items_list_for_response = [schemas.OrderItem.model_validate(item) for item in items_response.data] if items_response.data else []
        
        full_cancelled_order_data = {**cancelled_order_header_db, "items": order_items_list_for_response}
        
        return schemas.Order.model_validate(full_cancelled_order_data)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Erreur API - Annulation de la commande ID {order_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur lors de l'annulation de la commande.")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    if supabase is None:
        logger.critical("CRITIQUE: SUPABASE_URL et SUPABASE_KEY doivent être configurés dans les variables d'environnement pour démarrer le serveur.")
        # Ne pas démarrer uvicorn si supabase n'est pas configuré
    else:
        logger.info(f"Démarrage du serveur FastAPI sur le port {port}")
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")