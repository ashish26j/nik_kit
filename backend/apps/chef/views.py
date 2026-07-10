"""M12 — public About-Chef read."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import ChefProfile


@api_view(["GET"])
@permission_classes([AllowAny])
def chef(request):
    p = ChefProfile.get_solo()
    avatar_url = request.build_absolute_uri(p.avatar.url) if p.avatar else None
    return Response({
        "name": p.name,
        "tagline": p.tagline,
        "bio": p.bio,
        "avatar_url": avatar_url,
        "socials": [
            {"platform": s.platform, "handle": s.handle, "url": s.resolved_url}
            for s in p.socials.all()
        ],
    })
