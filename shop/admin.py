from django.contrib import admin
from django.utils.html import format_html
from .models import ShopCategory, ShopItem, UserInventory, UserAvatar, AvatarEquipment
from django.db import models

@admin.register(ShopCategory)
class ShopCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'icon', 'order', 'item_count')
    list_editable = ('order', 'icon')
    search_fields = ('name', 'display_name')
    ordering = ('order',)
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Товаров'

@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'item_type', 'gender', 'rarity_badge', 
                   'price', 'layer', 'is_active', 'is_featured', 'image_preview')
    list_filter = ('item_type', 'rarity', 'category', 'gender', 'layer', 'is_active', 'is_featured')
    list_editable = ('price', 'is_active', 'is_featured', 'layer')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'image_preview', 'get_layer_config_display')
    filter_horizontal = ('compatible_with', 'exclusive_with')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'category', 'item_type', 
                      'rarity', 'price', 'gender', 'layer', 'unlock_level')
        }),
        
        ('Изображение и внешний вид', {
            'fields': ('image', 'external_image_url', 'emoji', 'primary_color', 
                      'secondary_color', 'preview_color', 'position_x', 'position_y', 
                      'width', 'height', 'scale')
        }),              
        
        ('Совместимость', {
            'fields': ('compatible_with', 'exclusive_with')
        }),
        
        ('Бонусы и статистика', {
            'fields': ('health_bonus', 'mood_bonus', 'xp_bonus', 'charisma_bonus')
        }),
        
        ('Настройки отображения', {
            'fields': ('is_featured', 'sort_order', 'is_active', 'get_layer_config_display')
        }),
        
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rarity_badge(self, obj):
        color = obj.get_rarity_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_rarity_display().upper()
        )
    rarity_badge.short_description = 'Редкость'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<div style="border: 2px solid #ddd; padding: 5px; border-radius: 8px; background: #f9f9f9;">'
                '<img src="{}" style="max-height: 150px; max-width: 150px; display: block; margin: 0 auto;" />'
                '<p style="text-align: center; margin-top: 5px; font-size: 12px; color: #666;">{}x{}</p>'
                '</div>',
                obj.image.url, obj.width, obj.height
            )
        return format_html(
            '<div style="width: 150px; height: 150px; background-color: {}; '
            'display: flex; align-items: center; justify-content: center; '
            'font-size: 48px; border-radius: 8px; border: 2px solid #ddd;">'
            '{}</div>',
            obj.preview_color, obj.emoji
        )
    image_preview.short_description = 'Предпросмотр изображения'
    
    def get_layer_config_display(self, obj):
        config = obj.get_layer_config()
        return format_html(
            '<div style="padding: 8px; background: #f0f8ff; border-radius: 6px; font-size: 12px;">'
            '<strong>Слой:</strong> {}<br>'
            '<strong>Позиция:</strong> X={}, Y={}<br>'
            '<strong>Размер:</strong> {}x{}<br>'
            '</div>',
            config.get('zIndex', 0),
            obj.position_x, obj.position_y,
            obj.width, obj.height
        )
    get_layer_config_display.short_description = 'Конфигурация слоя'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if not obj.layer:
                layer_map = {
                    'background': 0,
                    'skin': 1,
                    'body': 1,
                    'pants': 2,
                    'shoes': 2,
                    'shirt': 3,
                    'facial_hair': 4,
                    'hair': 5,
                    'glasses': 6,
                    'hat': 7,
                    'accessory': 8,
                    'face': 9,
                    'avatar': 1,
                    'frame': 10,
                    'badge': 11,
                    'theme': 0,
                }
                obj.layer = layer_map.get(obj.item_type, 3)
            
            if not obj.width or not obj.height:
                size_map = {
                    'background': (300, 300),
                    'skin': (200, 300),
                    'body': (200, 300),
                    'shirt': (180, 150),
                    'pants': (150, 120),
                    'shoes': (100, 50),
                    'hair': (180, 120),
                    'glasses': (120, 40),
                    'hat': (150, 80),
                    'accessory': (60, 60),
                    'face': (120, 120),
                    'badge': (60, 60),
                    'frame': (320, 320),
                }
                default_size = size_map.get(obj.item_type, (200, 200))
                obj.width = default_size[0]
                obj.height = default_size[1]
        
        super().save_model(request, obj, form, change)

@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'item_name', 'item_type', 'purchased_at', 'equipped_badge', 'wear_level_bar')
    list_filter = ('equipped', 'is_active', 'item__item_type', 'item__rarity')
    search_fields = ('user__username', 'item__name', 'custom_name')
    readonly_fields = ('purchased_at', 'wear_level_bar', 'user_display', 'item_display')
    list_select_related = ('item', 'user')
    
    actions = []
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user_display', 'item_display', 'custom_name', 'equipped', 'is_active')
        }),
        ('Состояние предмета', {
            'fields': ('wear_level', 'wear_level_bar')
        }),
        ('Системная информация', {
            'fields': ('purchased_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_action_choices(self, request, default_choices=models.BLANK_CHOICE_DASH):
        choices = [] + default_choices
        return choices
    
    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<strong>{}</strong> (ID: {})<br>'
                '<small>Email: {}</small>',
                obj.user.username, obj.user.id, obj.user.email
            )
        return "-"
    user_display.short_description = 'Пользователь'
    
    def item_display(self, obj):
        if obj.item:
            color = obj.item.get_rarity_color()
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 5px; '
                'display: flex; align-items: center; justify-content: center; font-size: 16px;">{}</div>'
                '<div>'
                '<strong>{}</strong><br>'
                '<small>Тип: {} | Цена: {} | Редкость: <span style="color: {}">{}</span></small>'
                '</div>'
                '</div>',
                obj.item.preview_color or '#ffffff',
                obj.item.emoji or '🎁',
                obj.item.name,
                obj.item.get_item_type_display(),
                obj.item.price,
                color, obj.item.get_rarity_display()
            )
        return "-"
    item_display.short_description = 'Товар'
    
    def item_name(self, obj):
        return f"{obj.item.name} ({obj.item.get_item_type_display()})"
    item_name.short_description = 'Товар и тип'
    
    def item_type(self, obj):
        return obj.item.get_item_type_display()
    item_type.short_description = 'Тип'
    
    def equipped_badge(self, obj):
        if obj.equipped:
            return format_html(
                '<span style="background: #27ae60; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 12px; font-weight: bold;">✓</span>'
            )
        return ""
    equipped_badge.short_description = 'Надето'
    
    def wear_level_bar(self, obj):
        color = '#27ae60' if obj.wear_level > 70 else '#f39c12' if obj.wear_level > 30 else '#e74c3c'
        return format_html(
            '<div style="background: #f0f0f0; border-radius: 10px; height: 20px; width: 100px; position: relative;">'
            '<div style="background: {}; height: 100%; width: {}%; border-radius: 10px;"></div>'
            '<span style="position: absolute; left: 50%; top: 0; transform: translateX(-50%); '
            'font-size: 12px; font-weight: bold; color: #333;">{}%</span>'
            '</div>',
            color, obj.wear_level, obj.wear_level
        )
    wear_level_bar.short_description = 'Износ'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

@admin.register(UserAvatar)
class UserAvatarAdmin(admin.ModelAdmin):
    list_display = ('user', 'skin_tone_preview', 'body_type', 'equipped_items_count', 'updated_at')
    list_filter = ('body_type',)
    search_fields = ('user__username',)
    readonly_fields = ('updated_at', 'skin_tone_preview', 'equipped_items_list', 'user_display')
    
    fieldsets = (
        ('Основные настройки', {
            'fields': ('user_display', 'skin_tone', 'skin_tone_preview', 'body_type', 'face_type')
        }),
        ('Настройки отображения', {
            'fields': ('background_color', 'show_shadow', 'avatar_size')
        }),
        ('Надетые предметы', {
            'fields': ('equipped_items_list',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        return format_html(
            '<strong>{}</strong> (ID: {})<br>'
            '<small>Email: {}</small>',
            obj.user.username, obj.user.id, obj.user.email
        )
    user_display.short_description = 'Пользователь'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk: 
            pass
        super().save_model(request, obj, form, change)
    
    def skin_tone_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; '
            'border-radius: 50%; border: 2px solid #ddd; display: inline-block; '
            'vertical-align: middle; margin-right: 10px;"></div>'
            '<span style="vertical-align: middle;">{}</span>',
            obj.skin_tone, obj.skin_tone
        )
    skin_tone_preview.short_description = 'Цвет кожи'
    
    def equipped_items_count(self, obj):
        count = obj.equipped_items.count()
        return format_html(
            '<span style="background: #3498db; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-weight: bold;">{}</span>',
            count
        )
    equipped_items_count.short_description = 'Надето предметов'
    
    def equipped_items_list(self, obj):
        items = obj.equipped_items.all()
        if not items:
            return "Нет надетых предметов"
        
        html = '<div style="max-height: 300px; overflow-y: auto;">'
        for item in items:
            html += format_html(
                '<div style="padding: 8px; margin-bottom: 5px; background: #f9f9f9; '
                'border-radius: 6px; border-left: 4px solid #3498db;">'
                '<strong>{}</strong> ({})<br>'
                '<small>Тип: {} | Куплено: {}</small>'
                '</div>',
                item.item.name,
                item.item.get_item_type_display(),
                item.item.rarity,
                item.purchased_at.strftime('%d.%m.%Y %H:%M')
            )
        html += '</div>'
        return format_html(html)
    equipped_items_list.short_description = 'Список надетых предметов'

@admin.register(AvatarEquipment)
class AvatarEquipmentAdmin(admin.ModelAdmin):
    list_display = ('avatar_user', 'item_name', 'custom_position', 'custom_scale', 'is_visible', 'updated_at')
    list_filter = ('is_visible',)
    search_fields = ('avatar__user__username', 'inventory_item__item__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('avatar', 'inventory_item')
        }),
        ('Кастомизация позиции', {
            'fields': ('custom_position_x', 'custom_position_y', 'custom_scale', 'is_visible')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def avatar_user(self, obj):
        return obj.avatar.user.username
    avatar_user.short_description = 'Пользователь'
    
    def item_name(self, obj):
        return obj.inventory_item.item.name
    item_name.short_description = 'Предмет'
    
    def custom_position(self, obj):
        return f"X: {obj.custom_position_x}, Y: {obj.custom_position_y}"
    custom_position.short_description = 'Позиция'

    def save_model(self, request, obj, form, change):
        if obj.inventory_item:
            obj.inventory_item.equipped = True
            obj.inventory_item.save()
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        if obj.inventory_item:
            obj.inventory_item.equipped = False
            obj.inventory_item.save()
        
        super().delete_model(request, obj)