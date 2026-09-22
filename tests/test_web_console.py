def test_web_console_page_is_served(client) -> None:
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    assert "سامانه عملیات فرایندی بورنا" in resp.text
    assert "ورود به سامانه" in resp.text
    assert "کارتابل من" in resp.text
    assert "رهگیری ارتباط فرایندها" in resp.text

    console_resp = client.get("/console")
    assert console_resp.status_code == 200, console_resp.text
    assert "عملیات نقش من" in console_resp.text
    assert "ثبت درخواست خرید" in console_resp.text
    assert "مدیریت پایه و دسترسی" in console_resp.text

    review_console_resp = client.get("/review-console")
    assert review_console_resp.status_code == 200, review_console_resp.text
    assert "کنسول کنترل فرایند بورنا" in review_console_resp.text
