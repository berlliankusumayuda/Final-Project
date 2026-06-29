from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import time
from django.conf import settings
import redis

class RedisRateLimitMiddleware(MiddlewareMixin):
    """Simple fixed-window rate limiting for certain endpoints.
    Uses Redis key: ratelimit:{ip}:{path}
    """
    redis_client = None
    def _get_redis(self):
        if not self.redis_client:
            self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=6379, db=2)
        return self.redis_client

    def process_request(self, request):
        # Apply only to course list
        if request.path.startswith('/courses/') and request.method == 'GET':
            ip = request.META.get('REMOTE_ADDR','anon')
            key = f"rl:{ip}:{request.path}"
            r = self._get_redis()
            limit = 60
            current = r.get(key)
            if current and int(current) >= limit:
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'data': None, 'error': {'code': 'rate_limited', 'message': 'Too many requests'}}, status=429)
            else:
                pipe = r.pipeline()
                pipe.incr(key,1)
                pipe.expire(key,60)
                pipe.execute()
        return None
