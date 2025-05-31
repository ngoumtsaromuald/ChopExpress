from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") # Utiliser la clé anon pour la connexion directe à la DB si nécessaire ou gérer via API Supabase

# Construction de l'URL de connexion pour SQLAlchemy (format PostgreSQL)
# Exemple: postgresql://user:password@host:port/database
# Supabase fournit une chaîne de connexion directe à PostgreSQL dans les paramètres du projet.
# Il est IMPORTANT de stocker ces identifiants de manière sécurisée.
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "") # À remplir avec le vrai mot de passe de la DB
DB_HOST = os.getenv("DB_HOST", "") # À remplir avec l'hôte de la DB Supabase (ex: db.xxxx.supabase.co)
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # role = Column(String, default="client") # client, restaurant_owner, admin

    # Relationships
    orders = relationship("Order", back_populates="customer")

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    whatsapp_number = Column(String, unique=True, nullable=True) # Pour les notifications directes
    description = Column(Text, nullable=True)
    cuisine_type = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Si un utilisateur peut posséder un restaurant
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    menu_items = relationship("MenuItem", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=True) # e.g., Entrée, Plat principal, Dessert, Boisson
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    status = Column(String, default="pending") # pending, confirmed, preparing, ready_for_pickup, out_for_delivery, delivered, cancelled, refunded
    total_amount = Column(Float, nullable=False)
    delivery_address = Column(String, nullable=True)
    delivery_latitude = Column(Float, nullable=True)
    delivery_longitude = Column(Float, nullable=True)
    payment_method = Column(String, nullable=True) # e.g., CinetPay, Cash
    payment_status = Column(String, default="pending") # pending, paid, failed
    transaction_id = Column(String, nullable=True) # Pour CinetPay
    notes = Column(Text, nullable=True)
    estimated_delivery_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_order = Column(Float, nullable=False) # Prix au moment de la commande
    notes = Column(Text, nullable=True) # Notes spécifiques pour cet article

    # Relationships
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    lang_code = Column(String(5), nullable=False, index=True) # e.g., fr_CM, en_CM
    key = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Fonction pour créer les tables dans la base de données
def create_db_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Ceci est pour la création initiale des tables.
    # En production, vous utiliseriez Alembic pour les migrations.
    print("Création des tables de la base de données...")
    # create_db_tables() # Décommentez pour créer les tables si elles n'existent pas.
    # print("Tables créées (si elles n'existaient pas).")
    print("DATABASE_URL utilisée:", DATABASE_URL)
    print("Assurez-vous que les variables d'environnement DB_USER, DB_PASSWORD, DB_HOST sont correctement configurées.")
    print("Vous devrez exécuter ce script ou utiliser Alembic pour appliquer ce schéma à votre base de données Supabase.") 