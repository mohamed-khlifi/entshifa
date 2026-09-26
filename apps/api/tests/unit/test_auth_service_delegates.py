"""AuthService read helpers (repository delegation)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ent.features.auth.service import AuthService
from ent.settings import get_settings


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_get_active_session_returns_row(mock_repo_cls: MagicMock) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    session_row = MagicMock(
        revoked_at=None,
        expires_at=now + timedelta(hours=1),
    )
    repo = AsyncMock()
    repo.get_session_by_public_id.return_value = session_row
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    assert await service.get_active_session("sess") is session_row


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_user_belongs_to_clinic_true(mock_repo_cls: MagicMock) -> None:
    repo = AsyncMock()
    repo.get_clinic_by_public_id.return_value = MagicMock(id=5)
    repo.user_belongs_to_clinic.return_value = True
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    assert await service.user_belongs_to_clinic(1, "01ARZ3NDEKTSV4RRFFQ69G5FB1")


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_user_belongs_to_clinic_missing_clinic(mock_repo_cls: MagicMock) -> None:
    repo = AsyncMock()
    repo.get_clinic_by_public_id.return_value = None
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    assert await service.user_belongs_to_clinic(1, "missing") is False


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_load_permissions(mock_repo_cls: MagicMock) -> None:
    repo = AsyncMock()
    repo.load_permission_codes.return_value = frozenset({"patient.read"})
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    perms = await service.load_permissions(user_id=1, clinic_id=2)
    assert perms == frozenset({"patient.read"})


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_get_user_and_clinic_by_public_id(mock_repo_cls: MagicMock) -> None:
    user = MagicMock()
    clinic = MagicMock()
    repo = AsyncMock()
    repo.get_user_by_public_id.return_value = user
    repo.get_clinic_by_public_id.return_value = clinic
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    assert await service.get_user_by_public_id("u") is user
    assert await service.get_clinic_by_public_id("c") is clinic


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_assert_clinic_membership_success(mock_repo_cls: MagicMock) -> None:
    clinic = MagicMock()
    repo = AsyncMock()
    repo.get_clinic_by_public_id.return_value = clinic
    repo.user_belongs_to_clinic.return_value = True
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    result = await service.assert_clinic_membership_or_not_found(
        user_id=1,
        clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB1",
    )
    assert result is clinic


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_assert_clinic_membership_denied(mock_repo_cls: MagicMock) -> None:
    from ent.core.errors.exceptions import NotFoundError

    clinic = MagicMock()
    repo = AsyncMock()
    repo.get_clinic_by_public_id.return_value = clinic
    repo.user_belongs_to_clinic.return_value = False
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    with pytest.raises(NotFoundError):
        await service.assert_clinic_membership_or_not_found(
            user_id=1,
            clinic_public_id="01ARZ3NDEKTSV4RRFFQ69G5FB1",
        )


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_update_session_active_clinic(mock_repo_cls: MagicMock) -> None:
    repo = AsyncMock()
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    await service.update_session_active_clinic(session_id=9, clinic_id=3)
    repo.update_session_active_clinic.assert_awaited_once_with(9, 3)
