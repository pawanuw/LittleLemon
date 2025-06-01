from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework.authtoken.views import obtain_auth_token


router = DefaultRouter()

urlpatterns = [
    path('api-token-auth/', obtain_auth_token),
    path('categories',views.CategoryViewSet.as_view(actions={'get':'list', 'post':'create'})),
    path('categories/<int:pk>',views.MenuItemsViewSet.as_view(actions={'get':'list'})),
    path('categories/<int:pk>/menu-items', views.CategoryViewSet.as_view({'get': 'menu_items'})),
    path('menu-items',views.MenuItemsViewSet.as_view(actions={'get':'list', 'post':'create'})),
    path('menu-items/<slug:slug>',views.MenuItemsViewSet.as_view(actions={'get':'retrieve', 'put':'update', 'delete':'destroy', 'patch':'update'})),
    path('cart/menu-items',views.CartViewSet.as_view(actions={'get':'list', 'post':'create', 'delete':'destroy'})),
    path('groups/manager/users',views.ManagersViewSet.as_view(actions={'get':'list', 'post':'create'})),
    path('groups/manager/users/<int:pk>', views.ManagersViewSet.as_view(actions={'delete':'destroy'})),
    path('groups/delivery-crew/users', views.DeliveryCrewViewSet.as_view(actions={'get':'list', 'post':'create'})),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryCrewViewSet.as_view(actions={'delete':'destroy'})),
    path('orders', views.OrderViewSet.as_view(actions={'get':'list', 'post':'create'})),
    path('orders/<int:pk>', views.OrderViewSet.as_view(actions={'get':'retrieve', 'delete':'destroy', 'patch':'partial_update'})),
]