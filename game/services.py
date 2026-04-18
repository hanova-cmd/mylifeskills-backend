class ProgressService:
    @staticmethod
    def calculate_level(experience):
        level = 1
        exp_required = 1000
        
        while experience >= exp_required:
            level += 1
            experience -= exp_required
            exp_required = int(exp_required * 1.2)
        
        return level, experience, exp_required

    @staticmethod
    def update_player_progress(user, points_earned):
        stats, created = UserStats.objects.get_or_create(user=user)
        
        stats.total_points += points_earned
        stats.experience += points_earned
        stats.tasks_completed += 1
        
        new_level, remaining_exp, next_level_exp = ProgressService.calculate_level(stats.experience)
        if new_level > stats.level:
            stats.level = new_level
            RewardService.give_level_up_rewards(user, new_level)
        
        stats.save()
        return stats

class RewardService:
    @staticmethod
    def give_level_up_rewards(user, new_level):
        inventory, created = PlayerInventory.objects.get_or_create(user=user)
        
        rewards = {
            2: {'coins': 100, 'message': 'Congratulatins with 2 level!'},
            3: {'coins': 150, 'furniture': 'basic_chair', 'message': 'New Furniture!'},
            5: {'coins': 300, 'clothing': 'cool_hat', 'message': 'New Accessory!'},
            10: {'coins': 1000, 'furniture': 'special_lamp', 'clothing': 'epic_outfit', 'message': 'Happy!'}
        }
        
        if new_level in rewards:
            reward = rewards[new_level]
            
            inventory.coins += reward.get('coins', 0)
            
            if 'furniture' in reward:
                furniture = FurnitureItem.objects.get(sprite_name=reward['furniture'])
                InventoryFurniture.objects.create(
                    inventory=inventory,
                    furniture=furniture,
                    quantity=1
                )
            
            if 'clothing' in reward:
                clothing = ClothingItem.objects.get(sprite_name=reward['clothing'])
                InventoryClothing.objects.create(
                    inventory=inventory,
                    clothing=clothing,
                    quantity=1
                )
            
            inventory.save()
            return reward
        
        return None