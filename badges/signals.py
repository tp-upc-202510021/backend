from .models import Badge


def create_default_badges(sender, **kwargs):
    """
    Crea la colección inicial de logros si no existen.
    Se ejecuta tras aplicar las migraciones.
    """
    default_badges = [
        {
            "name": "El primer paso",
            "description": "El usuario completó su primer módulo de manera exitosa!",
            "unlock_condition": "complete_first_module",
        },
        {
            "name": "Empiezo lo que termino",
            "description": "El usuario completó todos sus módulos asignados.",
            "unlock_condition": "complete_all_modules",
        },
        {
            "name": "Primera de muchas (o eso creemos)",
            "description": "Ganar el primer juego contra un amigo.",
            "unlock_condition": "win_first_friend_game",
        },
        {
            "name": "Trilogía Victoriosa",
            "description": "Tres victorias y tu leyenda financiera ya es tema de conversación!",
            "unlock_condition": "win_three_games",  
        },
        {
            "name":"Alguien deténgalo",
            "description": "El usuario ganó 5 juegos contra amigos.",
            "unlock_condition": "win_five_games",
        },
        {
            "name": "Premio o castigo?",
            "description": "El usuario se vio afectado por un evento aleatorio.",
            "unlock_condition": "random_event_triggered",
        },
    ]

    for data in default_badges:
        Badge.objects.get_or_create(
            name=data["name"],
            defaults={
                "description": data["description"],
                "unlock_condition": data["unlock_condition"],
            },
        )
