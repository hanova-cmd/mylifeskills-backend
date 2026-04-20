from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
import os

User = get_user_model()

def shop_item_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.name.replace(' ', '_')}_{int(timezone.now().timestamp())}.{ext}"
    return f'shop_items/{instance.item_type}/{filename}'

class ShopCategory(models.Model):
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Shop Category"
        verbose_name_plural = "Shop Categories"
        ordering = ['order']
    
    def __str__(self):
        return self.display_name

class ShopItem(models.Model):
    TYPE_CHOICES = [
        ('skin', 'Skin Tone'),         
        ('body', 'Body Type'),       
        ('face', 'Face'),            
        ('hair', 'Hair'),             
        ('hair_color', 'Hair Color'), 
        ('shirt', 'Shirt/Top'),         
        ('pants', 'Pants/Bottom'),     
        ('shoes', 'Shoes'),           
        ('glasses', 'Glasses'),        
        ('hat', 'Hat'),               
        ('accessory', 'Accessory'),     
        ('facial_hair', 'Facial Hair'),  #
        
        ('avatar', 'Avatar'),
        ('background', 'Backgrounds'),
        ('frame', 'Cool frames'),
        ('badge', 'Badges'),
        ('theme', 'Themes'),
    ]
    
    LAYER_CHOICES = [
        (0, 'Background'),
        (1, 'Body/Skin'),
        (2, 'Pants/Shoes'),
        (3, 'Shirt'),
        (4, 'Facial Hair'),
        (5, 'Hair'),
        (6, 'Glasses'),
        (7, 'Hat'),
        (8, 'Accessories'),
        (9, 'Face'),
        (10, 'Frame'),
        (11, 'Badge'),
    ]
    
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    GENDER_CHOICES = [
        ('any', 'Any'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(verbose_name="Description")
    category = models.ForeignKey(ShopCategory, on_delete=models.CASCADE, 
                                related_name='items', verbose_name="Category")
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, 
                                verbose_name="Item type")
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, 
                             default='common', verbose_name="Rarity")
    price = models.IntegerField(validators=[MinValueValidator(0)], 
                               verbose_name="Price (points)")
    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    layer = models.IntegerField(choices=LAYER_CHOICES, default=3, help_text="Render layer")
    
    position_x = models.IntegerField(default=0, help_text="Horizontal offset from center")
    position_y = models.IntegerField(default=0, help_text="Vertical offset from center")
    width = models.IntegerField(default=100, help_text="Image width in pixels")
    height = models.IntegerField(default=100, help_text="Image height in pixels")
    scale = models.FloatField(default=1.0, help_text="Scale multiplier (0.5-2.0)")
    
    primary_color = models.CharField(max_length=20, default='#3498db', 
                                    verbose_name="Primary color")
    secondary_color = models.CharField(max_length=20, default='#2980b9', 
                                      verbose_name="Secondary color", blank=True)
    
    emoji = models.CharField(max_length=10, default='🎁', verbose_name="Emoji")
    preview_color = models.CharField(max_length=20, default='#ffffff', 
                                    verbose_name="Preview color")
    
    image = models.ImageField(upload_to=shop_item_image_path, 
                             blank=True, null=True, 
                             verbose_name="Item image")
    
    external_image_url = models.URLField(max_length=500, blank=True, null=True, 
                                        verbose_name="External image URL (Google Drive, etc.)",
                                        help_text="Use this instead of uploading file")
    
    compatible_with = models.ManyToManyField('self', symmetrical=False, blank=True,
                                           related_name='compatible_items',
                                           help_text="Items this can be combined with")
    exclusive_with = models.ManyToManyField('self', symmetrical=False, blank=True,
                                          related_name='exclusive_items',
                                          help_text="Items this cannot be combined with")
    
    health_bonus = models.IntegerField(default=0)
    mood_bonus = models.IntegerField(default=0)
    xp_bonus = models.IntegerField(default=0)
    charisma_bonus = models.IntegerField(default=0, help_text="Community influence")
    
    sort_order = models.IntegerField(default=0, verbose_name="Sort order")
    is_active = models.BooleanField(default=True, verbose_name="Is active")
    is_featured = models.BooleanField(default=False, verbose_name="Featured")
    unlock_level = models.IntegerField(default=1, verbose_name="Unlock Level")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Shop item"
        verbose_name_plural = "Shop items"
        ordering = ['layer', 'sort_order', 'price', 'name']
        indexes = [
            models.Index(fields=['item_type', 'is_active']),
            models.Index(fields=['layer', 'gender']),
            models.Index(fields=['category', 'rarity']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_item_type_display()})"
    
    def image_url(self):
        if self.external_image_url:
            return self.external_image_url
        
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        
        return None
    
    def get_rarity_color(self):
        colors = {
            'common': '#7f8c8d',
            'uncommon': '#2ecc71',
            'rare': '#3498db',
            'epic': '#9b59b6',
            'legendary': '#f39c12',
        }
        return colors.get(self.rarity, '#7f8c8d')
    
    def get_layer_config(self):
        layer_configs = {
            'background': {'zIndex': 0, 'defaultX': 0, 'defaultY': 0, 'defaultWidth': 300, 'defaultHeight': 300},
            'skin': {'zIndex': 1, 'defaultX': 0, 'defaultY': 0, 'defaultWidth': 200, 'defaultHeight': 300},
            'body': {'zIndex': 1, 'defaultX': 0, 'defaultY': 0, 'defaultWidth': 200, 'defaultHeight': 300},
            'pants': {'zIndex': 2, 'defaultX': 0, 'defaultY': 80, 'defaultWidth': 150, 'defaultHeight': 120},
            'shoes': {'zIndex': 3, 'defaultX': 0, 'defaultY': 180, 'defaultWidth': 100, 'defaultHeight': 50},
            'shirt': {'zIndex': 4, 'defaultX': 0, 'defaultY': 0, 'defaultWidth': 180, 'defaultHeight': 150},
            'facial_hair': {'zIndex': 5, 'defaultX': 0, 'defaultY': -10, 'defaultWidth': 120, 'defaultHeight': 60},
            'hair': {'zIndex': 6, 'defaultX': 0, 'defaultY': -80, 'defaultWidth': 180, 'defaultHeight': 120},
            'glasses': {'zIndex': 7, 'defaultX': 0, 'defaultY': -30, 'defaultWidth': 120, 'defaultHeight': 40},
            'hat': {'zIndex': 8, 'defaultX': 0, 'defaultY': -100, 'defaultWidth': 150, 'defaultHeight': 80},
            'accessory': {'zIndex': 9, 'defaultX': 40, 'defaultY': 40, 'defaultWidth': 60, 'defaultHeight': 60},
            'face': {'zIndex': 10, 'defaultX': 0, 'defaultY': -40, 'defaultWidth': 120, 'defaultHeight': 120},
            'avatar': {'zIndex': 1, 'defaultX': 0, 'defaultY': 0, 'defaultWidth': 200, 'defaultHeight': 300},
            'frame': {'zIndex': 11, 'defaultX': 0, 'defaultY': 0, 'defaultWidth': 320, 'defaultHeight': 320},
            'badge': {'zIndex': 12, 'defaultX': 100, 'defaultY': -100, 'defaultWidth': 60, 'defaultHeight': 60},
        }
        return layer_configs.get(self.item_type, {'zIndex': self.layer, 'defaultX': 0, 'defaultY': 0, 'defaultWidth': 100, 'defaultHeight': 100})

class UserAvatar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='avatar_config')
    
    skin_tone = models.CharField(max_length=20, default='#ffdbac')
    body_type = models.CharField(max_length=20, default='average')
    face_type = models.CharField(max_length=20, default='neutral', blank=True)
    
    background_color = models.CharField(max_length=20, default='#ecf0f1')
    show_shadow = models.BooleanField(default=True)
    avatar_size = models.IntegerField(default=300, help_text="Size in pixels")
    
    equipped_items = models.ManyToManyField('UserInventory', through='AvatarEquipment', 
                                          related_name='avatar_equipments')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Avatar"
        verbose_name_plural = "User Avatars"
    
    def __str__(self):
        return f"Avatar config for {self.user.username}"
    
    def get_equipped_items_by_layer(self):
        equipment = self.avatarequipment_set.select_related(
            'inventory_item__item'
        ).order_by('inventory_item__item__layer')
        
        layers = {}
        for eq in equipment:
            if eq.is_visible:
                layer = eq.inventory_item.item.layer
                if layer not in layers:
                    layers[layer] = []
                layers[layer].append(eq)
        
        return layers

class AvatarEquipment(models.Model):
    avatar = models.ForeignKey(UserAvatar, on_delete=models.CASCADE)
    inventory_item = models.ForeignKey('UserInventory', on_delete=models.CASCADE)
    
    custom_position_x = models.IntegerField(default=0)
    custom_position_y = models.IntegerField(default=0)
    custom_scale = models.FloatField(default=1.0)
    is_visible = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['avatar', 'inventory_item']
        verbose_name = "Avatar Equipment"
        verbose_name_plural = "Avatar Equipment"
    
    def __str__(self):
        return f"{self.avatar.user.username} - {self.inventory_item.item.name}"

class UserInventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_inventory')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    equipped = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    wear_level = models.IntegerField(default=100)  # 0-100%
    custom_name = models.CharField(max_length=50, blank=True)
    
    avatar_equipment = models.OneToOneField(AvatarEquipment, on_delete=models.SET_NULL, 
                                           null=True, blank=True, related_name='inventory_item_ref')
    
    class Meta:
        verbose_name = "User Inventory"
        verbose_name_plural = "User Inventory"
        unique_together = ['user', 'item']
        ordering = ['-equipped', '-purchased_at']

    def __str__(self):
        status = "✓" if self.equipped else ""
        return f"{self.user.username} - {self.item.name} {status}"
    
    def save(self, *args, **kwargs):
        if self.equipped and not self.avatar_equipment:
            avatar, created = UserAvatar.objects.get_or_create(user=self.user)
            equipment = AvatarEquipment.objects.create(
                avatar=avatar,
                inventory_item=self,
                custom_position_x=self.item.position_x,
                custom_position_y=self.item.position_y,
                custom_scale=self.item.scale
            )
            self.avatar_equipment = equipment
        
        elif not self.equipped and self.avatar_equipment:
            self.avatar_equipment.delete()
            self.avatar_equipment = None
        
        super().save(*args, **kwargs)

from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=ShopItem)
def delete_shop_item_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

@receiver(post_delete, sender=UserInventory)
def delete_inventory_avatar_equipment(sender, instance, **kwargs):
    if instance.avatar_equipment:
        instance.avatar_equipment.delete()