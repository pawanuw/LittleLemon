from rest_framework import serializers 
from .models import Category, MenuItem, Cart, Order, OrderItem
from rest_framework.validators import UniqueTogetherValidator 
from django.contrib.auth.models import User
from decimal import Decimal

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']
        read_only_fields = ['id', 'slug']

class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    featured = serializers.BooleanField(required=True)
    class Meta:
        model = MenuItem
        fields = ['title', 'slug', 'price', 'featured', 'category']
        read_only_fields = ['slug']

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'PUT' and 'featured' not in data:
            raise serializers.ValidationError({
                'featured': 'This field is required.'
            })
        return data

class CartSerializer(serializers.ModelSerializer):
    menuitem = serializers.SlugRelatedField(
        slug_field='title',
        queryset=MenuItem.objects.all()
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'quantity', 'unit_price', 'price']
        read_only_fields = ['price', 'unit_price']
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=['user', 'menuitem']
            )
        ]
    def create(self, validated_data):
        request = self.context['request']
        validated_data['user'] = request.user  # Set user from token
        return super().create(validated_data)

class OrderItemNestedSerializer(serializers.ModelSerializer):
    menuitem = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())

    class Meta:
        model = OrderItem
        fields = ['menuitem', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemNestedSerializer(many=True, write_only=True)
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = ['user', 'delivery_crew', 'status', 'total', 'date', 'order_items']
        read_only_fields = ['user', 'date', 'delivery_crew', 'total']

    def validate_delivery_crew(self, value):
        if value and not value.groups.filter(name="Delivery crew").exists():
            raise serializers.ValidationError("Selected user is not in the Delivery crew.")
        return value

    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        request = self.context['request']
        validated_data['user'] = request.user
        validated_data['status'] = False

        total = Decimal('0.00')
        print("Order creation: validated_data before total calculation:", validated_data)
        print("Order items data:", order_items_data)

        for item_data in order_items_data:
            menuitem = item_data['menuitem']
            quantity = Decimal(str(item_data['quantity']))
            unit_price = menuitem.price
            price = unit_price * quantity
            print(f"Item: {menuitem}, quantity: {quantity}, unit_price: {unit_price}, price: {price}")
            total += price

        validated_data['total'] = total
        print("Final validated_data with total:", validated_data)

        order = Order.objects.create(**validated_data)

        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                menuitem=item_data['menuitem'],
                quantity=item_data['quantity'],
                unit_price=item_data['menuitem'].price,
                price=item_data['menuitem'].price * Decimal(str(item_data['quantity']))
            )
        return order
    
    def update(self, instance, validated_data):
        if 'status' not in validated_data:
            validated_data['status'] = instance.status or False
        return super().update(instance, validated_data)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            user = request.user
            if user and user.is_authenticated and (
                user.groups.filter(name='Manager').exists() or
                user.groups.filter(name='Delivery crew').exists()
            ):
                self.fields['order_items'].required = False

class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all()
    )
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all()
    )

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'quantity', 'unit_price', 'price']
        validators = [
            UniqueTogetherValidator(
                queryset=OrderItem.objects.all(),
                fields=['order', 'menuitem']
            )
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user