from magicgui.application import use_app


def test_mock_app(mock_app):
    app = use_app()
    backend = mock_app._backend

    assert app is mock_app

    app.backend_name
    backend._mgui_get_backend_name.assert_called_once()

    app.get_obj("some name")
    mock_app._prop.assert_called_once()

    with app:
        backend._mgui_get_native_app.assert_called_once()
    backend._mgui_start_timer.assert_called_once()
    backend._mgui_run.assert_called_once()
    backend._mgui_stop_timer.assert_called_once()

    app.process_events()
    backend._mgui_process_events.assert_called_once()

    app.quit()
    backend._mgui_quit.assert_called_once()
