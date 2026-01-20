from django.db import transaction
from django.utils.timezone import now
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Company, Warehouse, Product,
    Inventory, InventoryLog, SalesActivity
)
from .serializers import ProductCreateSerializer

class HomeAPI(APIView):
    def get(self, request):
        return Response({"message": "StockFlow Backend Running "})



class CreateProductAPI(APIView):
    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            company = Company.objects.get(id=data["company_id"])
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=404)

        try:
            warehouse = Warehouse.objects.get(id=data["warehouse_id"], company=company)
        except Warehouse.DoesNotExist:
            return Response({"error": "Warehouse not found for this company"}, status=404)

        with transaction.atomic():
        
            if Product.objects.filter(sku=data["sku"]).exists():
                return Response({"error": "SKU already exists"}, status=400)

            product = Product.objects.create(
                company=company,
                name=data["name"],
                sku=data["sku"],
                price=data["price"]
            )

            inventory = Inventory.objects.create(
                product=product,
                warehouse=warehouse,
                quantity=data["initial_quantity"]
            )

            InventoryLog.objects.create(
                inventory=inventory,
                change=data["initial_quantity"],
                reason="Initial stock"
            )

        return Response(
            {"message": "Product created", "product_id": product.id},
            status=status.HTTP_201_CREATED
        )


class LowStockAlertsAPI(APIView):

    def get(self, request, company_id):
        recent_days = 30
        cutoff = now() - timedelta(days=recent_days)

        warehouses = Warehouse.objects.filter(company_id=company_id)
        if not warehouses.exists():
            return Response({"alerts": [], "total_alerts": 0})

        alerts = []

        for wh in warehouses:
            inventories = Inventory.objects.filter(
                warehouse=wh
            ).select_related("product", "product__supplier")

            for inv in inventories:
                product = inv.product

                has_recent_sales = SalesActivity.objects.filter(
                    product=product,
                    warehouse=wh,
                    sold_at__gte=cutoff
                ).exists()

                if not has_recent_sales:
                    continue

                threshold = product.low_stock_threshold

                if inv.quantity < threshold:
                    sales_qs = SalesActivity.objects.filter(
                        product=product,
                        warehouse=wh,
                        sold_at__gte=cutoff
                    ).values_list("quantity_sold", flat=True)

                    total_sold = sum(sales_qs) if sales_qs else 0
                    avg_daily_sales = (total_sold / recent_days) if total_sold else 0

                    if avg_daily_sales > 0:
                        days_until_stockout = int(inv.quantity / avg_daily_sales)
                    else:
                        days_until_stockout = None

                    supplier_data = None
                    if product.supplier:
                        supplier_data = {
                            "id": product.supplier.id,
                            "name": product.supplier.name,
                            "contact_email": product.supplier.contact_email
                        }

                    alerts.append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "sku": product.sku,
                        "warehouse_id": wh.id,
                        "warehouse_name": wh.name,
                        "current_stock": inv.quantity,
                        "threshold": threshold,
                        "days_until_stockout": days_until_stockout,
                        "supplier": supplier_data
                    })

        return Response({"alerts": alerts, "total_alerts": len(alerts)})
