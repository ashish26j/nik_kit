from django.urls import path

from . import views

urlpatterns = [
    path("cart", views.cart_view),
    path("cart/items", views.cart_add),
    path("cart/items/<int:pk>", views.cart_item),
    path("orders", views.orders_root),
    path("orders/<int:pk>", views.order_detail),
]
