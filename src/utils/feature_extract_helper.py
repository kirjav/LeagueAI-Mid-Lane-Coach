def is_boots(item_id):
    return item_id in {
        1001, 3006, 3009, 3020, 3047, 3111, 3117, 3158
    }
    
def calculate_kda(kills, assists, deaths):
    return round((int(kills) + int(assists)) / max(1, int(deaths)), 2)