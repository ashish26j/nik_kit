from django.urls import path

from . import views

urlpatterns = [
    # cart
    path("cart", views.cart_view),
    path("cart/items", views.cart_add),
    path("cart/items/<int:pk>", views.cart_item),
    # orders (client)
    path("orders", views.orders_root),
    path("orders/<int:pk>", views.order_detail),
    # payment + tracking (client)
    path("orders/<int:pk>/payment", views.payment_info),
    path("orders/<int:pk>/payment/proof", views.upload_proof),
    path("orders/<int:pk>/tracking", views.order_tracking),
    # admin (confirm gate + advance)
    path("admin/payments", views.admin_payments_queue),
    path("admin/orders/<int:pk>/payment/confirm", views.admin_confirm_payment),
    path("admin/orders/<int:pk>/payment/reject", views.admin_reject_payment),
    path("admin/orders/<int:pk>/advance", views.admin_advance),
    path("admin/orders/<int:pk>/cancel", views.admin_cancel),
]
