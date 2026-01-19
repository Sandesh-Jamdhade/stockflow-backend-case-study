from django.db import models
from decimal import Decimal


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="warehouses")
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("company", "name")

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=255)
    contact_email = models.EmailField(blank=True, null=True)

    class Meta:
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


class Product(models.Model):
    PRODUCT_TYPES = (
        ("normal", "Normal"),
        ("bundle", "Bundle"),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)  # platform-wide unique
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="normal")

    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    # low stock threshold varies by product
    low_stock_threshold = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class BundleItem(models.Model):
    bundle = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bundle_items")
    item = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="included_in_bundles")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("bundle", "item")


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventories")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventories")
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ("product", "warehouse")
        indexes = [
            models.Index(fields=["warehouse", "product"]),
        ]


class InventoryLog(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name="logs")
    change = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SalesActivity(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    sold_at = models.DateTimeField(auto_now_add=True)
