import time

from django.core.cache import cache
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import InquiryForm
from .models import Track, Genre
from .notify import notify_telegram


GENDER_SLUGS = {"female", "male"}

LICENSE_MAP = {
    "nonex": "non_exclusive",     # ?license=nonex → Non-exclusive
    "excl":  "exclusive",         # ?license=excl  → Exclusive
    "stems": "exclusive_stems",   # ?license=stems → Exclusive+ (STEMS)
}


PAGE_SIZE_DEFAULT = 21

def catalog(request):
    # Базовий queryset
    qs = (
        Track.objects.all()
        .order_by("-is_featured", "-created_at")  # або як тобі треба
        .prefetch_related("genres")
    )

    # Фільтр за жанром (опційно)
    genre_slug = request.GET.get("genre")
    active_genre = None
    if genre_slug:
        active_genre = Genre.objects.filter(slug=genre_slug).first()
        if active_genre:
            qs = qs.filter(genres=active_genre)

    # Пагінація: 20 на сторінку
    paginator = Paginator(qs, 21)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)  # зручно: сам ловить помилки і дає валідну сторінку

    context = {
        "page_obj": page_obj,
        "tracks": page_obj.object_list,                  # ← ВАЖЛИВО: у шаблон йдуть лише елементи поточної сторінки
        "paginator": paginator,
        "genres": Genre.objects.all().order_by("name"),  # чіпси зверху
        "active_genre": active_genre,
    }
    return render(request, "tracks/track_list.html", context)

def home(request):
    featured = Track.objects.filter(is_featured=True).order_by("-created_at")[:6]
    latest = Track.objects.order_by("-created_at")[:6]
    top_genres = Genre.objects.annotate(n=Count("tracks")).order_by("-n", "name")[:12]
    return render(request, "tracks/home.html", {
        "featured": featured,
        "latest": latest,
        "top_genres": top_genres,
    })


def track_list(request):
    genre_slug = request.GET.get("genre")
    tracks_qs = Track.objects.all().prefetch_related("genres").order_by("-created_at")

    active_genre = None
    if genre_slug:
        active_genre = Genre.objects.filter(slug=genre_slug).first()
        if active_genre:
            tracks_qs = tracks_qs.filter(genres=active_genre).distinct()

    genres = Genre.objects.annotate(n=Count("tracks")).order_by("-n", "name")

    return render(request, "tracks/track_list.html", {
        "tracks": tracks_qs,
        "genres": genres,
        "active_genre": active_genre,
    })


def order_page(request):
    """Форма замовлення з anti-bot, rate-limit, та префілом треку/ліцензії з query."""
    # ---- Rate limit: не більше 5 POST за 10 хв з IP
    if request.method == "POST":
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0] or request.META.get("REMOTE_ADDR")
        key = f"order_rate:{ip}"
        hits = cache.get(key, 0) + 1
        cache.set(key, hits, timeout=60 * 10)  # 10 хв
        if hits > 5:
            return HttpResponseBadRequest("Забагато спроб. Спробуй пізніше, братан.")

    # ---- GET: ставимо мітку часу (anti-bot)
    if request.method == "GET":
        request.session["order_started_at"] = int(time.time())

    # ---- Витягуємо трек (із GET або POST)
    track_id = request.GET.get("track") if request.method == "GET" else request.POST.get("track")
    track = get_object_or_404(Track, id=track_id) if track_id else None

    if request.method == "POST":
        # Anti-bot: занадто швидкий сабміт
        started = int(request.session.get("order_started_at", 0))
        if started and time.time() - started < 3:
            return HttpResponseBadRequest("Здається, бот. Заповнюй форму не так блискавично :)")

        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save()

            # Телега — як у тебе було
            msg = (
                "🚨 <b>Нова заявка</b>\n"
                f"🎵 Трек: {inquiry.track.title if inquiry.track else '—'}\n"
                f"👤 Ім’я: {inquiry.name}\n"
                f"📬 Контакт: {inquiry.contact}\n"
                f"🧾 Ліцензія: {inquiry.get_license_type_display()}\n"
                f"💬 Повідомлення: {inquiry.message[:500] or '—'}"
            )
            notify_telegram(msg)

            return redirect(reverse("order_thanks") + f"?id={inquiry.id}")
        else:
            # впав валідатор — відмалюємо з помилками
            return render(request, "tracks/order_page.html", {"form": form, "track": track})

    # ---- GET: готуємо початкові значення форми
    initial = {}
    if track:
        initial["track"] = track

    # Префіл ліцензії з ?license=
    lic_qs = request.GET.get("license")
    if lic_qs in LICENSE_MAP:
        initial["license_type"] = LICENSE_MAP[lic_qs]

    form = InquiryForm(initial=initial)
    return render(request, "tracks/order_page.html", {"form": form, "track": track})


def order_thanks(request):
    return render(request, "tracks/order_thanks.html")


def track_detail(request, slug):
    track = get_object_or_404(Track.objects.prefetch_related("genres"), slug=slug)
    gender_tags = [g for g in track.genres.all() if g.slug in GENDER_SLUGS]
    other_tags = [g for g in track.genres.all() if g.slug not in GENDER_SLUGS]

    related = (Track.objects
    .filter(~Q(id=track.id), genres__in=track.genres.all())
    .distinct()
    .order_by("-is_featured", "-created_at")[:6])

    return render(request, "tracks/track_detail.html", {
        "track": track,
        "gender_tags": gender_tags,
        "other_tags": other_tags,
        "related": related,
    })
