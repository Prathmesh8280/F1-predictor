import os
import urllib.request

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ml.config import LOGOS_DIR

from backend.app.constants import LOGO_SLUGS

router = APIRouter()


@router.get("/logo/{slug}")
def get_logo(slug: str):
    entry = LOGO_SLUGS.get(slug.lower())
    if not entry:
        raise HTTPException(status_code=404, detail="Unknown team slug")

    year, f1slug = entry
    cached_path = os.path.join(LOGOS_DIR, f"{f1slug}.webp")

    if os.path.exists(cached_path) and os.path.getsize(cached_path) > 100:
        with open(cached_path, "rb") as f:
            return Response(
                content=f.read(),
                media_type="image/webp",
                headers={"Cache-Control": "public, max-age=86400"},
            )

    url = (
        f"https://media.formula1.com/image/upload/f_auto/q_auto/v1"
        f"/common/f1/{year}/{f1slug}/{year}{f1slug}logo.webp"
    )
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "image/webp,image/*,*/*",
            "Referer": "https://www.formula1.com/",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        if len(data) > 100:
            with open(cached_path, "wb") as f:
                f.write(data)
            return Response(
                content=data,
                media_type="image/webp",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch logo: {e}")

    raise HTTPException(status_code=404, detail="Logo unavailable")
