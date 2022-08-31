from utils.database import models


async def get_user(discord_id) -> models.Users:
    user = await models.Users.find_one(models.Users.discord_id == discord_id)
    if user is None:
        user = models.Users(discord_id=discord_id)
    return user
