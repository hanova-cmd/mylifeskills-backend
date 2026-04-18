from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('categories/', views.ShopCategoriesView.as_view(), name='shop_categories'),
    path('items/', views.ShopItemsView.as_view(), name='shop_items'),
    path('test/', views.TestShopAPI.as_view(), name='shop_test'),
    
    path('purchase/', views.PurchaseItemView.as_view(), name='purchase_item'),
    path('equip/', views.EquipItemView.as_view(), name='equip_item'),
    path('unequip/', views.UnequipItemView.as_view(), name='unequip_item'),
    path('inventory/', views.UserInventoryView.as_view(), name='user_inventory'),
    path('points/', views.UserPointsView.as_view(), name='user_points'),
    path('check/<int:item_id>/', views.CheckPurchaseView.as_view(), name='check_purchase'),
    
    path('avatar/', views.UserAvatarView.as_view(), name='user_avatar'),
    path('avatar/customize/', views.AvatarCustomizeView.as_view(), name='avatar_customize'),
    path('avatar/preview/', views.AvatarPreviewView.as_view(), name='avatar_preview'),
    
    path('admin/items/', views.AdminShopItemsView.as_view(), name='admin_shop_items'),
    path('admin/items/create/', views.AdminCreateShopItemView.as_view(), name='admin_create_item'),
    path('admin/items/<int:item_id>/upload-image/', 
         views.UploadItemImageView.as_view(), name='upload_item_image'),
    
    path('test-purchase/', views.TestPurchaseAPI.as_view(), name='test_purchase'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)