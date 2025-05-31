from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RestaurantBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True

class RestaurantCreate(RestaurantBase):
    pass

class Restaurant(RestaurantBase):
    id: int
    owner_id: Optional[int] = None # Si vous décidez de lier à un utilisateur propriétaire
    created_at: datetime
    updated_at: datetime

    class Config:
        # orm_mode = True # Renommé en from_attributes = True dans Pydantic V2
        # Pour Pydantic V2, utilisez:
        from_attributes = True

class RestaurantListResponse(BaseModel):
    restaurants: List[Restaurant]

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    owner_id: Optional[int] = None

# Schemas pour MenuItem
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True

class MenuItemCreate(MenuItemBase):
    # restaurant_id sera fourni par le path parameter
    pass

class MenuItem(MenuItemBase):
    id: int
    restaurant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MenuItemListResponse(BaseModel):
    menu_items: List[MenuItem]

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None

# Schemas pour User
class UserBase(BaseModel):
    phone_number: str # Supposant que le format est validé ailleurs ou est flexible
    name: Optional[str] = None
    # role: Optional[str] = "client" # Pourrait être géré séparément

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    # Si nous voulons exposer les commandes de l'utilisateur directement:
    # orders: List[Order] = [] # Nécessiterait un schéma Order défini et une jointure

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[User]

class UserUpdate(BaseModel):
    name: Optional[str] = None
    # role: Optional[str] = None # Attention à la gestion des rôles

# Schemas pour OrderItem
class OrderItemBase(BaseModel):
    menu_item_id: int
    quantity: int
    notes: Optional[str] = None

class OrderItemCreate(OrderItemBase):
    # price_at_order sera calculé au moment de la création de la commande
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    price_at_order: float # Prix au moment de la commande

    class Config:
        from_attributes = True

# Schemas pour Order
class OrderBase(BaseModel):
    restaurant_id: int
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    notes: Optional[str] = None
    # customer_id sera déduit de l'utilisateur authentifié (via le bot WhatsApp)
    # total_amount, status, payment_method, payment_status, transaction_id seront gérés par la logique de création

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] # Liste des articles de la commande

class Order(OrderBase):
    id: int
    customer_id: int
    status: str
    total_amount: float
    payment_method: Optional[str] = None
    payment_status: str
    transaction_id: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItem] # Liste des articles de la commande avec tous les détails

    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    orders: List[Order]

class OrderUpdate(BaseModel):
    status: Optional[str] = None # Principalement pour l'admin ou le restaurant
    estimated_delivery_time: Optional[datetime] = None
    # D'autres champs pourraient être ajoutés si nécessaire pour la mise à jour 