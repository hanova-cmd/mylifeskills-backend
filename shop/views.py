from rest_framework import generics, status, parsers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import os

from .models import ShopCategory, ShopItem, UserInventory, UserAvatar, AvatarEquipment
from .serializers import (
    ShopCategorySerializer, ShopItemSerializer, 
    UserInventorySerializer, CreateShopItemSerializer,
    UserAvatarSerializer, AvatarEquipmentSerializer,
    AvatarLayerSerializer
)


class ShopCategoriesView(generics.ListAPIView):
    queryset = ShopCategory.objects.all().order_by('order')
    serializer_class = ShopCategorySerializer
    permission_classes = [AllowAny]

class ShopItemsView(generics.ListAPIView):
    serializer_class = ShopItemSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = ShopItem.objects.filter(is_active=True)
        
        category_id = self.request.query_params.get('category')
        item_type = self.request.query_params.get('type')
        rarity = self.request.query_params.get('rarity')
        featured = self.request.query_params.get('featured')
        gender = self.request.query_params.get('gender', 'unisex')
        
        if category_id and category_id != 'all':
            queryset = queryset.filter(category_id=category_id)
        if item_type and item_type != 'all':
            queryset = queryset.filter(item_type=item_type)
        if rarity and rarity != 'all':
            queryset = queryset.filter(rarity=rarity)
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        if gender != 'all':
            queryset = queryset.filter(gender__in=[gender, 'unisex', 'any'])
        
        return queryset.order_by('layer', 'sort_order', 'price')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class PurchaseItemView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response({'error': 'Item ID is required'}, status=400)
        
        try:
            item = ShopItem.objects.get(id=item_id, is_active=True)
        except ShopItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
        
        user = request.user
        
        if UserInventory.objects.filter(user=user, item=item, is_active=True).exists():
            return Response({
                'success': False,
                'error': 'Item already purchased',
                'code': 'already_owned'
            }, status=400)
        
        if user.level < item.unlock_level:
            return Response({
                'success': False,
                'error': f'Requires level {item.unlock_level}',
                'code': 'level_required',
                'required_level': item.unlock_level,
                'current_level': user.level
            }, status=403)
        
        user_coins = user.coins
        
        if user_coins < item.price:
            return Response({
                'success': False,
                'error': 'Not enough points',
                'code': 'insufficient_points',
                'required': item.price,
                'current': user_coins,
                'missing': item.price - user_coins
            }, status=400)
        
        try:
            old_balance = user_coins
            
            if hasattr(user, 'stats'):
                user.stats.coins -= item.price
                user.stats.save(update_fields=['coins'])
                new_balance = user.stats.coins
            else:
                new_balance = user_coins - item.price
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Payment failed: {str(e)}',
                'code': 'payment_failed'
            }, status=500)
        
        try:
            inventory_item = UserInventory.objects.create(
                user=user,
                item=item,
                equipped=False
            )
            
            return Response({
                'success': True,
                'message': f'Successfully purchased {item.name}!',
                'item': ShopItemSerializer(item, context={'request': request}).data,
                'inventory_item': UserInventorySerializer(inventory_item).data,
                'balance': {
                    'before': old_balance,
                    'after': new_balance,
                    'spent': item.price,
                    'currency': 'points'
                },
                'auto_equipped': False,
                'purchase_time': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            if hasattr(user, 'stats'):
                user.stats.coins += item.price
                user.stats.save()
            
            return Response({
                'success': False,
                'error': f'Inventory creation failed: {str(e)}',
                'code': 'inventory_error',
                'refund_processed': True,
                'refund_amount': item.price
            }, status=500)

class EquipItemView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        inventory_id = request.data.get('inventory_id')
        item_id = request.data.get('item_id')
        
        if not inventory_id and not item_id:
            return Response({'error': 'Item ID or Inventory ID is required'}, status=400)
        
        try:
            if inventory_id:
                inventory_item = UserInventory.objects.get(
                    id=inventory_id,
                    user=request.user,
                    is_active=True
                )
            else:
                inventory_item = UserInventory.objects.get(
                    user=request.user,
                    item_id=item_id,
                    is_active=True
                )
        except UserInventory.DoesNotExist:
            return Response({'error': 'Item not found in inventory'}, status=404)
        
        if inventory_item.equipped:
            return Response({
                'success': True,
                'message': 'Item is already equipped',
                'inventory_item': UserInventorySerializer(inventory_item).data
            })
        
        item = inventory_item.item
        item_type = item.item_type
        
        single_item_types = ['skin', 'body', 'face', 'hair', 'background']
        if item_type in single_item_types:
            UserInventory.objects.filter(
                user=request.user,
                item__item_type=item_type,
                equipped=True,
                is_active=True
            ).update(equipped=False)
        
        inventory_item.equipped = True
        inventory_item.save()
        
        return Response({
            'success': True,
            'message': f'Equipped {item.name}',
            'inventory_item': UserInventorySerializer(inventory_item).data
        })

class UnequipItemView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        inventory_id = request.data.get('inventory_id')
        item_id = request.data.get('item_id')
        
        if not inventory_id and not item_id:
            return Response({'error': 'Item ID or Inventory ID is required'}, status=400)
        
        try:
            if inventory_id:
                inventory_item = UserInventory.objects.get(
                    id=inventory_id,
                    user=request.user,
                    is_active=True
                )
            else:
                inventory_item = UserInventory.objects.get(
                    user=request.user,
                    item_id=item_id,
                    is_active=True
                )
        except UserInventory.DoesNotExist:
            return Response({'error': 'Item not found in inventory'}, status=404)
        
        if not inventory_item.equipped:
            return Response({
                'success': True,
                'message': 'Item is not equipped',
                'inventory_item': UserInventorySerializer(inventory_item).data
            })
        
        inventory_item.equipped = False
        inventory_item.save()
        
        return Response({
            'success': True,
            'message': f'Unequipped {inventory_item.item.name}',
            'inventory_item': UserInventorySerializer(inventory_item).data
        })

class UserInventoryView(generics.ListAPIView):
    serializer_class = UserInventorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserInventory.objects.filter(
            user=self.request.user, 
            is_active=True
        ).select_related('item').order_by('-equipped', '-purchased_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        try:
            user_points = request.user.stats.points
        except:
            user_points = 0
        
        grouped_inventory = {}
        for item in serializer.data:
            item_type = item['item_details']['item_type']
            if item_type not in grouped_inventory:
                grouped_inventory[item_type] = []
            grouped_inventory[item_type].append(item)
        
        return Response({
            'success': True,
            'balance': user_points,
            'total_items': queryset.count(),
            'equipped_items': queryset.filter(equipped=True).count(),
            'grouped_inventory': grouped_inventory,
            'inventory': serializer.data
        })

class UserPointsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        return Response({
            'success': True,
            'points': user.points,
            'level': user.level,
            'daily_streak': user.daily_streak,
            'currency': 'points'
        })

class CheckPurchaseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, item_id):
        try:
            item = ShopItem.objects.get(id=item_id, is_active=True)
        except ShopItem.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Item not found'
            }, status=404)
        
        user = request.user
        
        checks = []
        
        level_ok = user.level >= item.unlock_level
        checks.append({
            'check': 'level',
            'passed': level_ok,
            'message': f'Level {user.level} >= {item.unlock_level}' if level_ok else f'Level {user.level} < {item.unlock_level}',
            'required': item.unlock_level,
            'current': user.level
        })
        
        already_owned = UserInventory.objects.filter(user=user, item=item, is_active=True).exists()
        checks.append({
            'check': 'not_owned',
            'passed': not already_owned,
            'message': 'Not owned yet' if not already_owned else 'Already owned'
        })
        
        try:
            user_points = user.stats.points
            balance_ok = user_points >= item.price
            checks.append({
                'check': 'balance',
                'passed': balance_ok,
                'message': f'Balance {user_points} >= {item.price}' if balance_ok else f'Balance {user_points} < {item.price}',
                'required': item.price,
                'current': user_points,
                'missing': item.price - user_points if not balance_ok else 0
            })
        except:
            checks.append({
                'check': 'balance',
                'passed': False,
                'message': 'No points system found'
            })
        
        can_purchase = all(check['passed'] for check in checks)
        
        return Response({
            'success': True,
            'can_purchase': can_purchase,
            'item': ShopItemSerializer(item, context={'request': request}).data,
            'checks': checks,
            'summary': 'Can purchase' if can_purchase else 'Cannot purchase'
        })

class UserAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_item_image_url(self, item, request):
        if item.external_image_url:
            return item.external_image_url
        if item.image and item.image.url:
            return request.build_absolute_uri(item.image.url)
        return None
    
    def get(self, request):
        avatar, created = UserAvatar.objects.get_or_create(user=request.user)
        
        equipped_items = UserInventory.objects.filter(
            user=request.user,
            equipped=True,
            is_active=True
        ).select_related('item')
        
        layers = []
        
        background_items = equipped_items.filter(item__item_type='background')
        if background_items.exists():
            bg_item = background_items.first().item
            layers.append({
                'type': 'background',
                'item_id': bg_item.id,
                'name': bg_item.name,
                'item_type': 'background',
                'image_url': self.get_item_image_url(bg_item, request),
                'position_x': 0,
                'position_y': 0,
                'width': 300,
                'height': 300,
                'scale': 1.0,
                'layer': 0,
                'primary_color': bg_item.primary_color,
                'secondary_color': bg_item.secondary_color,
            })
        else:
            layers.append({
                'type': 'background',
                'item_type': 'background',
                'color': avatar.background_color,
                'layer': 0,
            })
        
        skin_items = equipped_items.filter(item__item_type='skin')
        body_items = equipped_items.filter(item__item_type='body')
        
        if skin_items.exists():
            skin_item = skin_items.first().item
            layers.append({
                'type': 'skin',
                'item_id': skin_item.id,
                'name': skin_item.name,
                'item_type': 'skin',
                'image_url': self.get_item_image_url(skin_item, request),
                'position_x': 0,
                'position_y': 0,
                'width': 200,
                'height': 300,
                'scale': 1.0,
                'layer': 1,
                'primary_color': skin_item.primary_color,
                'secondary_color': skin_item.secondary_color,
                'skin_tone': skin_item.primary_color,
            })
        else:
            layers.append({
                'type': 'skin',
                'item_type': 'skin',
                'skin_tone': avatar.skin_tone,
                'layer': 1,
            })
        
        if body_items.exists():
            body_item = body_items.first().item
            layers.append({
                'type': 'body',
                'item_id': body_item.id,
                'name': body_item.name,
                'item_type': 'body',
                'image_url': self.get_item_image_url(body_item, request),
                'position_x': 0,
                'position_y': 0,
                'width': 200,
                'height': 300,
                'scale': 1.0,
                'layer': 1,
                'primary_color': body_item.primary_color,
                'secondary_color': body_item.secondary_color,
                'body_type': avatar.body_type,
            })
        
        for inv_item in equipped_items.exclude(item__item_type__in=['background', 'skin', 'body']):
            item = inv_item.item
            layer_config = item.get_layer_config()
            
            try:
                equipment = AvatarEquipment.objects.get(
                    avatar=avatar,
                    inventory_item=inv_item
                )
                position_x = equipment.custom_position_x
                position_y = equipment.custom_position_y
                scale = equipment.custom_scale
                is_visible = equipment.is_visible
            except AvatarEquipment.DoesNotExist:
                position_x = item.position_x
                position_y = item.position_y
                scale = item.scale
                is_visible = True
            
            if not is_visible:
                continue
            
            layer_data = {
                'type': 'item',
                'item_id': item.id,
                'name': item.name,
                'item_type': item.item_type,
                'image_url': self.get_item_image_url(item, request),
                'position_x': position_x,
                'position_y': position_y,
                'width': item.width,
                'height': item.height,
                'scale': scale,
                'layer': item.layer,
                'primary_color': item.primary_color,
                'secondary_color': item.secondary_color,
            }
            
            layers.append(layer_data)
        
        layers.sort(key=lambda x: x['layer'])
        
        return Response({
            'success': True,
            'avatar': UserAvatarSerializer(avatar).data,
            'layers': layers,
            'skin_tones': [
                {'name': 'Light', 'color': '#ffdbac'},
                {'name': 'Medium Light', 'color': '#f1c27d'},
                {'name': 'Medium', 'color': '#e0ac69'},
                {'name': 'Medium Dark', 'color': '#c68642'},
                {'name': 'Dark', 'color': '#8d5524'},
            ],
            'body_types': ['slim', 'average', 'athletic', 'curvy']
        })
    
    @transaction.atomic
    def post(self, request):
        avatar, created = UserAvatar.objects.get_or_create(user=request.user)
        
        skin_tone = request.data.get('skin_tone')
        body_type = request.data.get('body_type')
        face_type = request.data.get('face_type')
        background_color = request.data.get('background_color')
        show_shadow = request.data.get('show_shadow')
        avatar_size = request.data.get('avatar_size')
        
        if skin_tone:
            avatar.skin_tone = skin_tone
        if body_type:
            avatar.body_type = body_type
        if face_type:
            avatar.face_type = face_type
        if background_color:
            avatar.background_color = background_color
        if show_shadow is not None:
            avatar.show_shadow = show_shadow
        if avatar_size:
            avatar.avatar_size = avatar_size
        
        avatar.save()
        
        return Response({
            'success': True,
            'message': 'Avatar updated successfully',
            'avatar': UserAvatarSerializer(avatar).data
        })

class AvatarCustomizeView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        inventory_id = request.data.get('inventory_id')
        position_x = request.data.get('position_x')
        position_y = request.data.get('position_y')
        scale = request.data.get('scale')
        is_visible = request.data.get('is_visible')
        
        try:
            inventory_item = UserInventory.objects.get(
                id=inventory_id,
                user=request.user,
                equipped=True,
                is_active=True
            )
        except UserInventory.DoesNotExist:
            return Response({'error': 'Item not found or not equipped'}, status=404)
        
        avatar, created = UserAvatar.objects.get_or_create(user=request.user)
        
        equipment, created = AvatarEquipment.objects.get_or_create(
            avatar=avatar,
            inventory_item=inventory_item,
            defaults={
                'custom_position_x': position_x or inventory_item.item.position_x,
                'custom_position_y': position_y or inventory_item.item.position_y,
                'custom_scale': scale or inventory_item.item.scale,
                'is_visible': is_visible if is_visible is not None else True
            }
        )
        
        if not created:
            if position_x is not None:
                equipment.custom_position_x = position_x
            if position_y is not None:
                equipment.custom_position_y = position_y
            if scale is not None:
                equipment.custom_scale = scale
            if is_visible is not None:
                equipment.is_visible = is_visible
            equipment.save()
        
        return Response({
            'success': True,
            'message': 'Item customization saved',
            'equipment': AvatarEquipmentSerializer(equipment).data
        })

class AvatarPreviewView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_item_image_url(self, item, request):
        if item.external_image_url:
            return item.external_image_url
        if item.image and item.image.url:
            return request.build_absolute_uri(item.image.url)
        return None
    
    def get(self, request):
        avatar, created = UserAvatar.objects.get_or_create(user=request.user)
        
        equipped_items = UserInventory.objects.filter(
            user=request.user,
            equipped=True,
            is_active=True
        ).select_related('item')
        
        layers = []
        
        background_items = equipped_items.filter(item__item_type='background')
        if background_items.exists():
            bg_item = background_items.first().item
            layers.append({
                'type': 'background',
                'image_url': self.get_item_image_url(bg_item, request),
                'color': bg_item.primary_color,
                'layer': 0,
            })
        else:
            layers.append({
                'type': 'background',
                'color': avatar.background_color,
                'layer': 0,
            })
        
        skin_items = equipped_items.filter(item__item_type='skin')
        if skin_items.exists():
            skin_item = skin_items.first().item
            layers.append({
                'type': 'skin',
                'image_url': self.get_item_image_url(skin_item, request),
                'color': skin_item.primary_color,
                'layer': 1,
            })
        else:
            layers.append({
                'type': 'skin',
                'color': avatar.skin_tone,
                'layer': 1,
            })
        
        for inv_item in equipped_items.exclude(item__item_type__in=['background', 'skin']):
            item = inv_item.item
            
            try:
                equipment = AvatarEquipment.objects.get(
                    avatar=avatar,
                    inventory_item=inv_item
                )
                if not equipment.is_visible:
                    continue
                position_x = equipment.custom_position_x
                position_y = equipment.custom_position_y
                scale = equipment.custom_scale
            except AvatarEquipment.DoesNotExist:
                position_x = item.position_x
                position_y = item.position_y
                scale = item.scale
            
            layer_data = {
                'type': 'item',
                'item_type': item.item_type,
                'image_url': self.get_item_image_url(item, request),
                'position_x': position_x,
                'position_y': position_y,
                'scale': scale,
                'layer': item.layer,
                'color': item.primary_color,
            }
            
            layers.append(layer_data)
        
        layers.sort(key=lambda x: x['layer'])
        
        return Response({
            'success': True,
            'layers': layers,
            'avatar_size': avatar.avatar_size,
            'show_shadow': avatar.show_shadow
        })

class AdminCreateShopItemView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request):
        serializer = CreateShopItemSerializer(data=request.data, 
                                            context={'request': request})
        if serializer.is_valid():
            item = serializer.save()
            return Response({
                'success': True,
                'message': 'Item uploaded successfully',
                'item': ShopItemSerializer(item, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminShopItemsView(generics.ListCreateAPIView):
    queryset = ShopItem.objects.all().order_by('-created_at')
    serializer_class = ShopItemSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class UploadItemImageView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [parsers.MultiPartParser]
    
    def post(self, request, item_id):
        try:
            item = ShopItem.objects.get(id=item_id)
        except ShopItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
        
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': 'No image provided'}, status=400)
        
        if item.image:
            old_path = item.image.path
            if os.path.exists(old_path):
                os.remove(old_path)
        
        item.image = image_file
        item.save()
        
        return Response({
            'success': True,
            'message': 'Image uploaded successfully',
            'image_url': request.build_absolute_uri(item.image.url)
        })

class TestShopAPI(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            "success": True,
            "message": "Shop API is working!",
            "endpoints": {
                "public": {
                    "categories": "/api/shop/categories/",
                    "items": "/api/shop/items/",
                    "test": "/api/shop/test/"
                },
                "user": {
                    "purchase": "/api/shop/purchase/",
                    "equip": "/api/shop/equip/",
                    "unequip": "/api/shop/unequip/",
                    "inventory": "/api/shop/inventory/",
                    "points": "/api/shop/points/",
                    "check_purchase": "/api/shop/check/<item_id>/",
                    "avatar": "/api/shop/avatar/",
                    "avatar/customize": "/api/shop/avatar/customize/",
                    "avatar/preview": "/api/shop/avatar/preview/"
                },
                "admin": {
                    "items": "/api/shop/admin/items/",
                    "create_item": "/api/shop/admin/items/create/",
                    "upload_image": "/api/shop/admin/items/<id>/upload-image/"
                }
            },
            "status": "operational"
        })

class TestPurchaseAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response({'error': 'Item ID is required'}, status=400)
        
        try:
            item = ShopItem.objects.get(id=item_id, is_active=True)
        except ShopItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
        
        user = request.user
        
        if UserInventory.objects.filter(user=user, item=item, is_active=True).exists():
            return Response({
                'success': False,
                'error': 'Item already purchased',
                'test_mode': True
            }, status=400)
        
        inventory_item = UserInventory.objects.create(
            user=user,
            item=item,
            equipped=False
        )
        
        return Response({
            'success': True,
            'message': f'TEST: Purchased {item.name} (no points deducted)',
            'item': ShopItemSerializer(item, context={'request': request}).data,
            'inventory_item': UserInventorySerializer(inventory_item).data,
            'test_mode': True,
            'points_deducted': 0
        }, status=status.HTTP_201_CREATED)