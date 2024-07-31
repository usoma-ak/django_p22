from django.contrib.admin import register, ModelAdmin, action, StackedInline

from apps.models import Product, ProductImage, Category, Review, Tags, Favorite


class ProductImageStackInline(StackedInline):
    model = ProductImage
    extra = 2
    min_num = 1


@register(Product)
class ProductModelAdmin(ModelAdmin):
    list_display = 'name', 'get_in_stock', 'category', 'id'
    inlines = [ProductImageStackInline]

    @action(description='Sotuvda bormi?')
    def get_in_stock(self, obj):
        return obj.in_stock

    get_in_stock.boolean = True


@register(Category)
class CategoryModelAdmin(ModelAdmin):
    pass


@register(Review)
class ReviewModelAdmin(ModelAdmin):
    pass


@register(Tags)
class ReviewModelAdmin(ModelAdmin):
    pass


@register(Favorite)
class ReviewModelAdmin(ModelAdmin):
    pass
