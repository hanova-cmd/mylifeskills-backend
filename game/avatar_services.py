class AvatarCustomizationService:
    
    @staticmethod
    def get_available_options(user):
        avatar = Avatar.objects.get(user=user)
        inventory = PlayerInventory.objects.get(user=user)
        
        return {
            'skin_tones': ['light', 'medium', 'dark', 'olive'],
            'hair_styles': ['short', 'medium', 'long', 'curly', 'afro'],
            'hair_colors': ['black', 'brown', 'blonde', 'red', 'gray', 'blue', 'pink'],
            'eye_colors': ['blue', 'green', 'brown', 'hazel', 'gray'],
            'equipped_items': avatar.equipped_items,
            'available_clothing': InventoryClothing.objects.filter(inventory=inventory)
        }
    
    @staticmethod
    def update_appearance(user, updates):
        avatar = Avatar.objects.get(user=user)
        
        if 'skin_tone' in updates:
            avatar.skin_tone = updates['skin_tone']
        if 'hair_style' in updates:
            avatar.hair_style = updates['hair_style']
        if 'hair_color' in updates:
            avatar.hair_color = updates['hair_color']
        if 'eye_color' in updates:
            avatar.eye_color = updates['eye_color']
            
        avatar.save()
        return avatar
    
    @staticmethod
    def equip_item(user, clothing_id):
        avatar = Avatar.objects.get(user=user)
        inventory = PlayerInventory.objects.get(user=user)
        
        try:
            inventory_item = InventoryClothing.objects.get(
                inventory=inventory,
                clothing_id=clothing_id,
                quantity__gte=1
            )
            
            clothing = inventory_item.clothing
            
            equipped_items = avatar.equipped_items.copy()
            
            equipped_items = [item for item in equipped_items 
                            if item.get('type') != clothing.clothing_type]
            
            equipped_items.append({
                'id': clothing.id,
                'type': clothing.clothing_type,
                'sprite_name': clothing.sprite_name,
                'name': clothing.name
            })
            
            avatar.equipped_items = equipped_items
            avatar.save()
            
            AvatarCustomizationService.calculate_style_points(avatar)
            
            return True
            
        except InventoryClothing.DoesNotExist:
            return False
    
    @staticmethod
    def calculate_style_points(avatar):
        total_style = 0
        equipped_items = avatar.equipped_items
        
        for item_data in equipped_items:
            try:
                clothing = ClothingItem.objects.get(id=item_data['id'])
                total_style += clothing.style_points
            except ClothingItem.DoesNotExist:
                continue
        
        avatar.total_style_points = total_style
        avatar.avatar_level = max(1, total_style // 100 + 1)
        avatar.save()