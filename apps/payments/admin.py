from django.contrib import admin
from .models import Product, Price, CheckoutPayment


class PriceInlineAdmin(admin.TabularInline):
    model = Price
    extra = 0
    fields = ('stripe_price_id', 'price', 'display_price')
    readonly_fields = ('display_price',)

    def display_price(self, obj):
        return obj.get_display_price() if obj.pk else '-'


class ProductAdmin(admin.ModelAdmin):
    inlines = [PriceInlineAdmin]
    list_display = ('name', 'stripe_product_id', 'has_file', 'url')
    search_fields = ('name', 'stripe_product_id')

    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'stripe_price_id', 'price', 'display_price')
    list_filter = ('product',)
    search_fields = ('product__name', 'stripe_price_id')

    def display_price(self, obj):
        return obj.get_display_price()


@admin.register(CheckoutPayment)
class CheckoutPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'payment_status', 'payment_intent', 'dt_created')
    list_filter = ('payment_status', 'product', 'dt_created')
    search_fields = ('user__username', 'user__email', 'product__name', 'payment_intent')
    readonly_fields = ('user', 'product', 'payment_intent', 'payment_status', 'dt_created')


admin.site.register(Product, ProductAdmin)
