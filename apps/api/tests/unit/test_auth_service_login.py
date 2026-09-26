"""AuthService login edge cases (mocked repository)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ent.core.errors.exceptions import AuthenticationError, AuthInvalidCredentialsError
from ent.features.auth.service import AuthService
from ent.settings import get_settings


@pytest.mark.asyncio
@patch("ent.features.auth.service.clear_login_attempts", new_callable=AsyncMock)
@patch("ent.features.auth.service.record_failed_login", new_callable=AsyncMock)
@patch("ent.features.auth.service.assert_login_allowed", new_callable=AsyncMock)
@patch("ent.features.auth.service.AuthRepository")
async def test_login_unknown_email(
    mock_repo_cls: MagicMock,
    *_mocks: object,
) -> None:
    repo = AsyncMock()
    repo.get_user_by_email.return_value = None
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    with pytest.raises(AuthInvalidCredentialsError):
        await service.login(
            email="unknown@test.entshifa.local",
            password="secret",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )


@pytest.mark.asyncio
@patch("ent.features.auth.service.clear_login_attempts", new_callable=AsyncMock)
@patch("ent.features.auth.service.record_failed_login", new_callable=AsyncMock)
@patch("ent.features.auth.service.assert_login_allowed", new_callable=AsyncMock)
@patch("ent.features.auth.service.verify_password", return_value=False)
@patch("ent.features.auth.service.AuthRepository")
async def test_login_wrong_password(
    mock_repo_cls: MagicMock,
    *_mocks: object,
) -> None:
    user = MagicMock(id=1)
    repo = AsyncMock()
    repo.get_user_by_email.return_value = user
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    with pytest.raises(AuthInvalidCredentialsError):
        await service.login(
            email="doctor@test.entshifa.local",
            password="wrong",
            ip_address=None,
            user_agent=None,
        )
    repo.record_failed_login.assert_awaited_once_with(1)


@pytest.mark.asyncio
@patch("ent.features.auth.service.clear_login_attempts", new_callable=AsyncMock)
@patch("ent.features.auth.service.record_failed_login", new_callable=AsyncMock)
@patch("ent.features.auth.service.assert_login_allowed", new_callable=AsyncMock)
@patch("ent.features.auth.service.verify_password", return_value=True)
@patch("ent.features.auth.service.AuthRepository")
async def test_login_without_clinic(
    mock_repo_cls: MagicMock,
    *_mocks: object,
) -> None:
    user = MagicMock(id=1, password_hash="hash")
    repo = AsyncMock()
    repo.get_user_by_email.return_value = user
    repo.default_clinic_for_user.return_value = None
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    with pytest.raises(AuthInvalidCredentialsError):
        await service.login(
            email="doctor@test.entshifa.local",
            password="secret",
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_refresh_expired_session(mock_repo_cls: MagicMock) -> None:
    from datetime import UTC, datetime, timedelta

    repo = AsyncMock()
    session_row = MagicMock(
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
        revoked_at=None,
        user_id=1,
    )
    repo.get_session_by_refresh_hash.return_value = session_row
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    with pytest.raises(AuthenticationError):
        await service.refresh(raw_refresh_token="refresh-token-value")


@pytest.mark.asyncio
@patch("ent.features.auth.service.AuthRepository")
async def test_logout_revokes_session(mock_repo_cls: MagicMock) -> None:
    repo = AsyncMock()
    session_row = MagicMock(id=99)
    repo.get_session_by_refresh_hash.return_value = session_row
    mock_repo_cls.return_value = repo

    service = AuthService(session=AsyncMock(), settings=get_settings())
    await service.logout(raw_refresh_token="refresh-token-value")
    repo.revoke_session.assert_awaited_once()
