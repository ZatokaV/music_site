from urllib.parse import urlparse, parse_qs

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

LICENSE_CHOICES = [
    ("non_exclusive", "Non-exclusive (WAV) — від $100"),
    ("exclusive", "Exclusive — від $200"),
    ("exclusive_stems", "Exclusive+ (STEMS) — від $250"),
    ("custom", "Custom"),
]

def _youtube_embed_from_url(url: str) -> str | None:
    try:
        u = urlparse(url)
        host = u.netloc.replace('www.', '')
        if host == 'youtu.be':
            video_id = u.path.lstrip('/')
        elif host in ('youtube.com', 'm.youtube.com', 'music.youtube.com'):
            qs = parse_qs(u.query)
            video_id = qs.get('v', [None])[0]
        else:
            return None
        if not video_id:
            return None
        return f"https://www.youtube.com/embed/{video_id}"
    except Exception:
        return None


class Genre(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


from django.db import models
from django.utils.text import slugify

class Track(models.Model):
    title = models.CharField(max_length=200)
    youtube_url = models.URLField()
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # якщо вже є — не дублюй
    genres = models.ManyToManyField("Genre", blank=True, related_name="tracks")

    slug = models.SlugField(max_length=220, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "track"
            s = base
            i = 2
            while Track.objects.filter(slug=s).exclude(pk=self.pk).exists():
                s = f"{base}-{i}"
                i += 1
            self.slug = s
        super().save(*args, **kwargs)

    # ⬇️ ЦЕ ЛИШАЙ — як у тебе було
    @property
    def embed_url(self):
        from urllib.parse import urlparse, parse_qs
        try:
            u = urlparse(self.youtube_url)
            host = u.netloc.replace('www.', '')
            if host == 'youtu.be':
                vid = u.path.lstrip('/')
            elif host in ('youtube.com', 'm.youtube.com', 'music.youtube.com'):
                vid = parse_qs(u.query).get('v', [None])[0]
            else:
                return None
            return f"https://www.youtube.com/embed/{vid}" if vid else None
        except Exception:
            return None

    def __str__(self):
        return self.title

    # НОВЕ (зручно лінкуватись у шаблонах)
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("track_detail", kwargs={"slug": self.slug})



class Inquiry(models.Model):
    LICENSE_CHOICES = [
        ("nonexclusive", "Неексклюзив — мінус + права, трек лишається на моєму каналі"),
        ("exclusive", "Ексклюзив — мінус + права, я ховаю трек у себе"),
        ("exclusive_stems", "Ексклюзив+ (зі стемами) — все те ж + доріжки інструментів"),
    ]

    track = models.ForeignKey(Track, null=True, blank=True, on_delete=models.SET_NULL, related_name="inquiries")
    name = models.CharField(max_length=120)
    contact = models.CharField(max_length=180, help_text="Email або Telegram")
    license_type = models.CharField(max_length=32, choices=LICENSE_CHOICES, default="non_exclusive")
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="new")  # new / in_progress / closed

    def __str__(self):
        base = f"{self.name} → {self.get_license_type_display()}"
        return f"{base} [{self.track.title if self.track else 'без треку'}]"


def _extract_genre_names(text: str):
    if not text:
        return []
    parts = [p.strip() for p in text.split(",")]
    # фільтруємо пусті, дуже довгі, дублікати
    clean = []
    seen = set()
    for p in parts:
        if not p:
            continue
        # нормалізація: прибираємо зайве, робимо Title Case
        name = p[:60].strip()
        key = slugify(name)
        if key and key not in seen:
            clean.append((name, key))
            seen.add(key)
    return clean


@receiver(post_save, sender=Track)
def sync_genres_from_description(sender, instance: Track, **kwargs):
    names = _extract_genre_names(instance.description or "")
    if not names:
        instance.genres.clear()
        return
    genres = []
    from .models import Genre  # локальний імпорт, щоб уникнути циклу
    for display, key in names:
        g, _ = Genre.objects.get_or_create(slug=key, defaults={"name": display})
        # якщо в БД було інше написання — оновимо name на нормальне
        if g.name != display:
            g.name = display
            g.save(update_fields=["name"])
        genres.append(g)
    instance.genres.set(genres)
