# from django.contrib.auth.views import LoginView
from django.urls import path

from apps.views import (ProductListView, ProductDetailView, SettingsUpdateView, LogoutView, RegisterCreateView,
                        CustomLoginView, CartListView, CartItemDeleteView, AddressCreateView, AddressUpdateView,
                        AddToCartView, update_quantity, CheckoutListView, OrderListView, OrderDeleteView,
                        OrderCreateView, OrderDetailView)

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list_page'),
    path('product/<int:pk>', ProductDetailView.as_view(), name='product_detail_page'),
    #
    #
    #
    path('logout', LogoutView.as_view(), name='logout_page'),
    path('settings', SettingsUpdateView.as_view(), name='settings_page'),
    path('register', RegisterCreateView.as_view(), name='register_page'),
    path('login', CustomLoginView.as_view(), name='login_page'),
    #
    #
    #
    path('shopping-cart', CartListView.as_view(), name='cart_page'),
    path('add-shopping-cart/<int:pk>/', AddToCartView.as_view(), name='add_cart_page'),
    path('remove-cart/delete/<int:pk>/', CartItemDeleteView.as_view(), name='cart_delete_page'),
    #
    #
    # path('favorites', FavouriteView.as_view(), name='favorites_page'),
    # path('add-to-favourite/<int:pk>/', AddToFavouriteView.as_view(), name='add_favourites_page'),
    # path('remove-favorite/<int:pk>/', RemoveFromFavoritesView.as_view(), name='remove_from_favorites'),
    #
    path('update-quantity/<int:pk>/', update_quantity, name='update_quantity'),
    path('chekout', CheckoutListView.as_view(), name='checkout_page'),
    #
    #
    path('address-create', AddressCreateView.as_view(), name='create_address_page'),
    path('address-update/<int:pk>', AddressUpdateView.as_view(), name='update_address_page'),
    #
    #
    path('orders', OrderListView.as_view(), name='order_list_page'),
    path('order-detail/<int:pk>', OrderDetailView.as_view(), name='order_detail_page'),
    path('order-create', OrderCreateView.as_view(), name='order_create_page'),
    path('order-delete/<int:pk>', OrderDeleteView.as_view(), name='order_delete_page')
]
