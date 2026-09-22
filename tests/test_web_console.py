def test_web_console_page_is_served(client) -> None:
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    assert "Borna Process Control Console" in resp.text
    assert "/api/v1/auth/login" in resp.text
    assert "Access control review" in resp.text
    assert "Procurement workflow runner" in resp.text
    assert "Downstream procurement runner" in resp.text

    console_resp = client.get("/console")
    assert console_resp.status_code == 200, console_resp.text
    assert "Session & role shortcuts" in console_resp.text
    assert "Security incident workflow lab" in console_resp.text
    assert "Guided tools & request composer" in console_resp.text
    assert "Trace Latest Payment" in console_resp.text
