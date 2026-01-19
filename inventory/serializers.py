from rest_framework import serializers
from decimal import Decimal
from .models import Product, Company, Warehouse, Inventory, InventoryLog


class ProductCreateSerializer(serializers.Serializer):
    company_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    sku = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    warehouse_id = serializers.IntegerField()
    initial_quantity = serializers.IntegerField(required=False, default=0)

    def validate_price(self, value):
        if value < Decimal("0.00"):
            raise serializers.ValidationError("Price cannot be negative")
        return value

    def validate_initial_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Initial quantity cannot be negative")
        return value
