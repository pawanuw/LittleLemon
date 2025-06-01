from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, UserSerializer, OrderSerializer
from rest_framework import viewsets
from .models import Category, MenuItem, Cart, User, Order, OrderItem
from rest_framework.decorators import action
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.core.paginator import Paginator, EmptyPage

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method=='GET':
            return []
        user = self.request.user
        if user and user.is_authenticated and (user.groups.filter(name='Manager').exists() or user.is_superuser):
            return []
        self.permission_denied(self.request, message="Only Admin or Managers are allowed to perform this action.")

    @action(detail=True, methods=['get'], url_path='menu-items')
    def menu_items(self, request, pk=None):
        items = MenuItem.objects.filter(category_id=pk)
        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data)

class MenuItemsViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['price', 'title']  # Allow ordering by price or title
    ordering = ['price'] 
    lookup_field = 'slug'

    def list(self, request, pk=None):
        if pk is not None:
            # Filter by category name
            queryset = MenuItem.objects.filter(category__title=pk)
        else:
            # Return all menu items
            queryset = MenuItem.objects.all()
        perpage = request.query_params.get('perpage', default=2)
        page = request.query_params.get('page', default=1)
        paginator = Paginator(queryset, per_page=perpage)
        try:
            queryset = paginator.page(number=page)
        except EmptyPage:
            queryset = []
        serializer = MenuItemSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        queryset = MenuItem.objects.all()
        category_id = self.kwargs.get('pk')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def get_permissions(self):
        if self.request.method=='GET':
            return []
        user = self.request.user
        if user and user.is_authenticated and (user.groups.filter(name='Manager').exists() or user.is_superuser):
            return []
        self.permission_denied(self.request, message="Only Admin or Managers are allowed to perform this action.")

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only the carts of the authenticated user
        return Cart.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        # If 'pk' is in kwargs, delete a single item
        if 'pk' in kwargs:
            return super().destroy(request, *args, **kwargs)
        
        # If no pk: treat as bulk delete (delete all user's cart items)
        self.get_queryset().delete()
        return Response({"detail": "All cart items deleted."})
    
from django.contrib.auth.models import Group

class ManagersViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(groups__name='Manager')

    def get_permissions(self):
        user = self.request.user
        if user and user.is_authenticated and (user.groups.filter(name='Manager').exists() or user.is_superuser):
            return []
        self.permission_denied(self.request, message="Only Admin or Managers are allowed to perform this action.")

    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        if not username:
            return Response({"error": "username is required"}, status=400)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        manager_group, created = Group.objects.get_or_create(name='Manager')
        user.groups.add(manager_group)
        return Response({"detail": f"User {user.username} added to Manager group"}, status=201)
    
    def destroy(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        manager_group = Group.objects.get(name='Manager')
        user.groups.remove(manager_group)
        return Response({"detail": f"User {user.username} removed from Manager group"}, status=204)
    
class DeliveryCrewViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(groups__name='Delivery crew')

    def get_permissions(self):
        user = self.request.user
        if user and user.is_authenticated and user.groups.filter(name='Manager').exists():
            return []
        self.permission_denied(self.request, message="Only Managers are allowed to perform this action.")

    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        if not username:
            return Response({"error": "username is required"}, status=400)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        delivery_crew_group, created = Group.objects.get_or_create(name='Delivery crew')
        user.groups.add(delivery_crew_group)
        return Response({"detail": f"User {user.username} added to Delivery crew group"}, status=201)
    
    def destroy(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        delivery_crew_group = Group.objects.get(name='Delivery crew')
        user.groups.remove(delivery_crew_group)
        return Response({"detail": f"User {user.username} removed from Delivery crew group"}, status=204)
    
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            if user.groups.filter(name='Manager').exists():
                return Order.objects.all()
            elif user.groups.filter(name='Delivery crew').exists():
                return Order.objects.filter(delivery_crew=user)
            else:
                return Order.objects.filter(user=user)
        self.permission_denied(self.request, message="Authentication is required to access this resource.")


    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=401)

        if not request.user.groups.filter(name='Manager').exists():
            data = request.data.copy()
            data.pop('delivery_crew', None)
        else:
            data = request.data

        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.create(serializer.validated_data)
        output_serializer = self.get_serializer(order)
        return Response(output_serializer.data, status=201)

    def destroy(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Manager').exists():
            return Response({"detail": "Only Managers can delete orders."}, status=403)
        return super().destroy(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        user = request.user

        if user.groups.filter(name='Delivery crew').exists():
            if set(request.data.keys()) != {'status'}:
                return Response({"detail": "Delivery crew can only update the status field."}, status=403)
            return super().partial_update(request, *args, **kwargs)

        if user.groups.filter(name='Manager').exists():
            if set(request.data.keys()) != {'delivery_crew'}:
                return Response({"detail": "Managers can only update the delivery_crew field."}, status=403)
            return super().partial_update(request, *args, **kwargs)

        return Response({"detail": "Only Managers or Delivery crew can update orders."}, status=403)