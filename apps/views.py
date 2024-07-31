from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Sum, F
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, UpdateView, CreateView, DetailView, DeleteView, TemplateView

from apps.forms import UserRegisterModelForm, OrderCreateModelForm
from apps.models import Product, Category, CartItem, User, Address, Order, OrderItem, SiteSettings


class CategoryMixin:
    def get_context_data(self, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductListView(CategoryMixin, ListView):
    queryset = Product.objects.order_by('-created_at')
    template_name = 'apps/product/product-list.html'
    context_object_name = 'products'
    paginate_by = 2

    def get_queryset(self):
        qs = super().get_queryset()
        if category_slug := self.request.GET.get('category'):
            return qs.filter(category__slug=category_slug).all()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_len'] = CartItem.objects.count()

        return context


class ProductDetailView(CategoryMixin, DetailView):
    model = Product
    template_name = 'apps/product/product-details.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_len'] = CartItem.objects.count()

        return context


class RegisterCreateView(CategoryMixin, CreateView):
    template_name = 'apps/auth/register.html'
    form_class = UserRegisterModelForm
    success_url = reverse_lazy('product_list_page')

    def form_valid(self, form):
        form.save()
        # send_to_email('Your account has been created!', form.data['email'])
        # send_to_email.delay('Your account has been created!', form.data['email'])
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class SettingsUpdateView(CategoryMixin, LoginRequiredMixin, UpdateView):
    queryset = User.objects.all()
    fields = 'first_name', 'last_name', 'email'
    template_name = 'apps/auth/settings.html'
    success_url = reverse_lazy('settings_page')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['cart_len'] = CartItem.objects.count()
        return context


class CustomLoginView(CategoryMixin, LoginView):
    template_name = 'apps/auth/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('product_list_page')


class LogoutView(CategoryMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('product_list_page')


class AddToCartView(CategoryMixin, View):
    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, id=pk)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return redirect('cart_page')


class CartListView(CategoryMixin, ListView):
    queryset = CartItem.objects.all()
    template_name = 'apps/product/shopping-cart.html'
    context_object_name = 'shopping_cart'
    success_url = reverse_lazy('cart_page')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['categories'] = Category.objects.all()
        context['cart_len'] = CartItem.objects.count()
        context['total_sum'] = sum(map(lambda i: i.quantity, CartItem.objects.all()))

        qs = self.get_queryset()

        context.update(
            **qs.aggregate(
                total_sum=Sum(F('quantity') * F('product__price') * (100 - F('product__discount')) / 100),
                total_count=Sum(F('quantity'))
            )
        )
        return context


def update_quantity(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(CartItem, pk=pk)
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity > 0:
            product.quantity = new_quantity
            product.save()

            total_sum = CartItem.objects.aggregate(
                total_sum=Sum(F('quantity') * F('product__price') * (100 - F('product__discount')) / 100)
            )['total_sum'] or 0

            total_count = CartItem.objects.aggregate(
                total_count=Sum('quantity')
            )['total_count'] or 0

            return JsonResponse({'new_quantity': new_quantity, 'total_sum': total_sum, 'total_count': total_count})
    return JsonResponse({'error': 'Invalid request'}, status=400)


class CartItemDeleteView(CategoryMixin, DeleteView):
    model = CartItem
    success_url = reverse_lazy('cart_page')


class AddressCreateView(CategoryMixin, CreateView):
    model = Address
    template_name = 'apps/address/create-address.html'
    fields = 'city', 'street', 'zip_code', 'phone', 'full_name'
    context_object_name = 'create_address'
    success_url = reverse_lazy("checkout_page")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_len'] = CartItem.objects.count()

        return context


class AddressUpdateView(CategoryMixin, UpdateView):
    model = Address
    template_name = 'apps/address/update-address.html'
    fields = ('city', 'street', 'phone', 'zip_code')
    success_url = reverse_lazy('checkout_page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart_len'] = CartItem.objects.count()
        return context


class CheckoutListView(LoginRequiredMixin, CategoryMixin, ListView):
    queryset = CartItem.objects.all()
    template_name = 'apps/product/checkout.html'
    context_object_name = 'cart_items'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        qs = self.get_queryset()

        context.update(
            **qs.aggregate(
                subtotal=Sum(F('quantity') * F('product__price') * (100 - F('product__discount')) / 100),
                shipping_cost=Sum(F('product__shipping_cost')),
                total=Sum(F('product__shipping_cost')) + Sum(
                    F('quantity') * F('product__price') * (100 - F('product__discount')) / 100)
            )
        )
        context['addresses'] = Address.objects.filter(user=self.request.user)
        context['cart_len'] = CartItem.objects.count()
        return context


class OrderListView(CategoryMixin, ListView):
    queryset = Order.objects.order_by('-created_at')
    template_name = 'apps/orders/order-list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(owner=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['tax'] = SiteSettings.objects.first().tax
        context['cart_len'] = CartItem.objects.count()
        return context


class OrderDetailView(LoginRequiredMixin, CategoryMixin, DetailView):
    model = Order
    template_name = 'apps/orders/order-details.html'
    context_object_name = 'order'

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(owner=self.request.user)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        qs = OrderItem.objects.filter(order_id=context['order'].id)

        context.update(
            **qs.aggregate(
                subtotal=Sum(F('quantity') * (F('product__price') * (
                        100 - F('product__discount')) / 100)),
                shipping_cost=Sum(F('product__shipping_cost'))
            )
        )
        context['tax'] = SiteSettings.objects.first().tax
        return context


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy('order_list_page')


class OrderCreateView(LoginRequiredMixin, CategoryMixin, CreateView):
    model = Order
    template_name = 'apps/product/checkout.html'
    form_class = OrderCreateModelForm
    success_url = reverse_lazy('order_list_page')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

# class FavouriteView(View):
#     template_name = 'apps/product/favourite.html'
#
#     def get(self, request, *args, **kwargs):
#         favourite_items = Favorite.objects.filter(user=request.user)
#         for item in favourite_items:
#             item.total_price = item.product.current_price
#
#         context = {
#             'favourite_items': favourite_items,
#         }
#         return render(request, self.template_name, context)
#
#
# class AddToFavouriteView(View):
#     def get(self, request, pk):
#         product = get_object_or_404(Product, id=pk)
#         favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
#
#         if not created:
#             product.is_favorited_by_user = True
#             product.save()
#         return redirect('favorites_page')
#
#
# # class RemoveFromFavoritesView(LoginRequiredMixin, View):
# #
# #     def get(self, request, *args, **kwargs):
# #         item_id = self.request.GET.get('item_id')
# #         if item_id:
# #             try:
# #                 cart_item = Favorite.objects.get(id=item_id, user=request.user)
# #                 cart_item.delete()
# #             except Favorite.DoesNotExist:
# #                 pass
# #         return redirect('favorites_page')
#
# class RemoveFromFavoritesView(LoginRequiredMixin, DeleteView):
#     queryset = Favorite.objects.all()
#     success_url = reverse_lazy('favorites_page')
#
#     def get_queryset(self):
#         return super().get_queryset().filter(user=self.request.user)
