from django.urls import path
from .views import CreateProductAPI, LowStockAlertsAPI, HomeAPI

urlpatterns = [
    path("products/", CreateProductAPI.as_view(), name="create-product"),
    path("companies/<int:company_id>/alerts/low-stock/", LowStockAlertsAPI.as_view(), name="low-stock-alerts"),
    path("", HomeAPI.as_view()),

]
