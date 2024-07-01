import jwt
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from authentication.models import Account


@database_sync_to_async
def get_user(token_key):
    try:
        payload = jwt.decode(token_key, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
        # Retrieve user based on user_id
        user = Account.objects.get(id=user_id)
        return user
    except jwt.ExpiredSignatureError:
        # Handle token expired
        return AnonymousUser()
    except (jwt.InvalidTokenError, Account.DoesNotExist):
        # Handle invalid token or user not found
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        try:
            query_string = scope['query_string'].decode()
            query_params = dict(x.split('=') for x in query_string.split("&"))
            token_key = query_params.get('token', None)
        except ValueError:
            token_key = None

        user = await get_user(token_key)
        scope['user'] = user
        return await super().__call__(scope, receive, send)
