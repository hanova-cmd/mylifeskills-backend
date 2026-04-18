from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ShopCategory, ShopItem, UserInventory, UserAvatar, AvatarEquipment

User = get_user_model()

class ShopCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = ShopCategory
        fields = ('id', 'name', 'display_name', 'icon', 'order', 'description', 'item_count')

class ShopItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    image_url = serializers.SerializerMethodField()
    can_purchase = serializers.SerializerMethodField()
    purchase_error = serializers.SerializerMethodField()
    owned = serializers.SerializerMethodField()
    equipped = serializers.SerializerMethodField()
    layer_config = serializers.SerializerMethodField()
    
    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'description', 'category', 'category_name',
            'item_type', 'rarity', 'price', 'gender', 'layer',
            'primary_color', 'secondary_color', 'emoji', 'preview_color',
            'position_x', 'position_y', 'width', 'height', 'scale',
            'image_url', 'compatible_with', 'exclusive_with',
            'health_bonus', 'mood_bonus', 'xp_bonus', 'charisma_bonus',
            'unlock_level', 'is_featured', 'sort_order', 'is_active',
            'created_at', 'can_purchase', 'purchase_error', 'owned', 
            'equipped', 'layer_config'
        )
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_can_purchase(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            
            if UserInventory.objects.filter(user=user, item=obj, is_active=True).exists():
                return False
            
            if user.level < obj.unlock_level:
                return False
            
            try:
                user_points = user.points
                return user_points >= obj.price
            except:
                return False
        
        return False
    
    def get_purchase_error(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            
            if UserInventory.objects.filter(user=user, item=obj, is_active=True).exists():
                return 'Already purchased'
            
            if user.level < obj.unlock_level:
                return f'Requires level {obj.unlock_level}'
            
            try:
                user_points = user.points
                if user_points < obj.price:
                    return f'Not enough points ({user_points}/{obj.price})'
            except:
                return 'No points available'
        
        return 'Not authenticated'
    
    def get_owned(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserInventory.objects.filter(
                user=request.user, 
                item=obj, 
                is_active=True
            ).exists()
        return False
    
    def get_equipped(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserInventory.objects.filter(
                user=request.user, 
                item=obj, 
                equipped=True,
                is_active=True
            ).exists()
        return False
    
    def get_layer_config(self, obj):
        return obj.get_layer_config()

class UserInventorySerializer(serializers.ModelSerializer):
    item_details = ShopItemSerializer(source='item', read_only=True)
    
    class Meta:
        model = UserInventory
        fields = (
            'id', 'user', 'item', 'item_details', 'purchased_at',
            'equipped', 'is_active', 'wear_level', 'custom_name'
        )

class AvatarEquipmentSerializer(serializers.ModelSerializer):
    inventory_item = UserInventorySerializer(read_only=True)
    item_details = ShopItemSerializer(source='inventory_item.item', read_only=True)
    
    class Meta:
        model = AvatarEquipment
        fields = (
            'id', 'inventory_item', 'item_details',
            'custom_position_x', 'custom_position_y', 'custom_scale',
            'is_visible', 'created_at', 'updated_at'
        )

class UserAvatarSerializer(serializers.ModelSerializer):
    equipped_items = AvatarEquipmentSerializer(source='avatarequipment_set', many=True, read_only=True)
    
    class Meta:
        model = UserAvatar
        fields = (
            'id', 'user', 'skin_tone', 'body_type', 'face_type',
            'background_color', 'show_shadow', 'avatar_size',
            'equipped_items', 'updated_at'
        )

class AvatarLayerSerializer(serializers.Serializer):
    type = serializers.CharField()
    item_id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    item_type = serializers.CharField(required=False)
    image_url = serializers.CharField(required=False, allow_null=True)
    position_x = serializers.IntegerField(default=0)
    position_y = serializers.IntegerField(default=0)
    width = serializers.IntegerField(default=100)
    height = serializers.IntegerField(default=100)
    scale = serializers.FloatField(default=1.0)
    layer = serializers.IntegerField(default=0)
    primary_color = serializers.CharField(required=False, allow_null=True)
    secondary_color = serializers.CharField(required=False, allow_null=True)
    skin_tone = serializers.CharField(required=False, allow_null=True)
    body_type = serializers.CharField(required=False, allow_null=True)

class CreateShopItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'name', 'description', 'category', 'item_type', 'rarity',
            'price', 'gender', 'layer', 'primary_color', 'secondary_color',
            'emoji', 'position_x', 'position_y', 'width', 'height', 'scale',
            'image', 'compatible_with', 'exclusive_with',
            'health_bonus', 'mood_bonus', 'xp_bonus', 'charisma_bonus',
            'unlock_level', 'is_featured', 'sort_order'
        )