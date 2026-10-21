from datetime import UTC, datetime

from clients.s3 import s3_urls
from schemas import SiteResponse

SITES: dict[int, SiteResponse] = {}


def get_next_id() -> int:
    return max(SITES, default=0) + 1


def build_site(
    site_id: int,
    *,
    title: str,
    prompt: str,
) -> SiteResponse:
    html_url, download_url, screenshot_url = s3_urls(site_id)
    now = datetime.now(UTC)
    return SiteResponse(
        id=site_id,
        title=title,
        html_code_url=html_url,
        html_code_download_url=download_url,
        screenshot_url=screenshot_url,
        prompt=prompt,
        created_at=now,
        updated_at=now,
    )


def create_mock_site(site_id: int = 1) -> SiteResponse:
    html_url, download_url, screenshot_url = s3_urls(site_id)
    return SiteResponse(
        id=site_id,
        title="Стегозавры",
        html_code_url=html_url,
        html_code_download_url=download_url,
        screenshot_url=screenshot_url,
        prompt="Сделай сайт про Стегозавров",
        created_at=datetime(2025, 6, 15, 18, 29, 56, tzinfo=UTC),
        updated_at=datetime(2025, 6, 15, 18, 29, 56, tzinfo=UTC),
    )


def update_site_timestamp(site_id: int) -> None:
    if site_id in SITES:
        SITES[site_id] = SITES[site_id].model_copy(
            update={"updated_at": datetime.now(UTC)},
        )
