from unittest.mock import patch, Mock, MagicMock
from langflow.services.database.models.user.user import User
from langflow.services.settings.constants import (
    DEFAULT_SUPERUSER,
    DEFAULT_SUPERUSER_PASSWORD,
)
from langflow.services.utils import setup_superuser, teardown_superuser


@patch("langflow.services.utils.get_settings_manager")
@patch("langflow.services.utils.create_super_user")
@patch("langflow.services.utils.get_session")
def test_setup_superuser(
    mock_get_session, mock_create_super_user, mock_get_settings_manager
):
    # Test when AUTO_LOGIN is True
    mock_settings_manager = Mock()
    mock_settings_manager.auth_settings.AUTO_LOGIN = True
    mock_get_settings_manager.return_value = mock_settings_manager
    setup_superuser()
    mock_get_session.assert_not_called()
    mock_create_super_user.assert_not_called()

    def reset_mock_credentials():
        mock_settings_manager.auth_settings.SUPERUSER = DEFAULT_SUPERUSER
        mock_settings_manager.auth_settings.SUPERUSER_PASSWORD = (
            DEFAULT_SUPERUSER_PASSWORD
        )

    # Test when username and password are default
    mock_settings_manager.auth_settings = Mock()
    mock_settings_manager.auth_settings.AUTO_LOGIN = False
    mock_settings_manager.auth_settings.SUPERUSER = "admin"
    mock_settings_manager.auth_settings.SUPERUSER_PASSWORD = "password"
    mock_settings_manager.auth_settings.reset_credentials = Mock(
        side_effect=reset_mock_credentials
    )

    mock_get_settings_manager.return_value = mock_settings_manager
    mock_session = Mock()
    mock_session.query.return_value.filter.return_value.first.return_value = (
        mock_session
    )
    # return value of get_session is a generator
    mock_get_session.return_value = iter([mock_session, mock_session])
    setup_superuser()
    mock_session.query.assert_called_once_with(User)
    actual_expr = mock_session.query.return_value.filter.call_args[0][0]
    expected_expr = User.username == "admin"

    assert str(actual_expr) == str(expected_expr)
    mock_create_super_user.assert_called_once_with(
        db=mock_session, username="admin", password="password"
    )
    # Test that superuser credentials are reset
    mock_settings_manager.auth_settings.reset_credentials.assert_called_once()
    assert mock_settings_manager.auth_settings.SUPERUSER != "admin"
    assert mock_settings_manager.auth_settings.SUPERUSER_PASSWORD != "password"

    # Test when superuser already exists
    mock_settings_manager.auth_settings.AUTO_LOGIN = False
    mock_settings_manager.auth_settings.SUPERUSER = "admin"
    mock_settings_manager.auth_settings.SUPERUSER_PASSWORD = "password"
    mock_user = Mock()
    mock_user.is_superuser = True
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user
    setup_superuser()
    mock_session.query.assert_called_with(User)
    actual_expr = mock_session.query.return_value.filter.call_args[0][0]
    expected_expr = User.username == "admin"

    assert str(actual_expr) == str(expected_expr)

    # Called once in the previous test
    mock_create_super_user.assert_called_once()


@patch("langflow.services.utils.get_settings_manager")
@patch("langflow.services.utils.get_session")
def test_teardown_superuser_default_superuser(
    mock_get_session, mock_get_settings_manager
):
    mock_settings_manager = MagicMock()
    mock_settings_manager.auth_settings.AUTO_LOGIN = True
    mock_settings_manager.auth_settings.SUPERUSER = DEFAULT_SUPERUSER
    mock_settings_manager.auth_settings.SUPERUSER_PASSWORD = DEFAULT_SUPERUSER_PASSWORD
    mock_get_settings_manager.return_value = mock_settings_manager

    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_user.is_superuser = True
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user
    mock_get_session.return_value = iter([mock_session])

    teardown_superuser()

    mock_session.query.assert_called_once_with(User)
    actual_expr = mock_session.query.return_value.filter.call_args[0][0]
    expected_expr = User.username == DEFAULT_SUPERUSER

    assert str(actual_expr) == str(expected_expr)
    mock_session.delete.assert_called_once_with(mock_user)
    mock_session.commit.assert_called_once()


@patch("langflow.services.utils.get_settings_manager")
@patch("langflow.services.utils.get_session")
def test_teardown_superuser_no_default_superuser(
    mock_get_session, mock_get_settings_manager
):
    mock_settings_manager = MagicMock()
    mock_settings_manager.auth_settings.AUTO_LOGIN = False
    mock_settings_manager.auth_settings.SUPERUSER = "admin"
    mock_settings_manager.auth_settings.SUPERUSER_PASSWORD = "password"
    mock_get_settings_manager.return_value = mock_settings_manager

    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_user.is_superuser = False
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user
    mock_get_session.return_value = [mock_session]

    teardown_superuser()

    mock_session.query.assert_not_called()
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()