from django.contrib import admin
from payments import models

# Register your models here.
from django.contrib import admin
from .models import Product, Price, CheckoutPayment


class PriceInlineAdmin(admin.TabularInline):
    model = Price
    extra = 0


class ProductAdmin(admin.ModelAdmin):
    inlines = [PriceInlineAdmin]


admin.site.register(Product, ProductAdmin)

admin.site.register(CheckoutPayment)