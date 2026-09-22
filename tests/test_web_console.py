def test_web_console_page_is_served(client) -> None:
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    assert "سامانه عملیاتی و کنترلی بورنا" in resp.text
    assert "خانه نقش" in resp.text
    assert "کارتابل و اقدام‌ها" in resp.text
    assert "مدیریت امنیت، کاربران و نشست‌ها" in resp.text

    console_resp = client.get("/console")
    assert console_resp.status_code == 200, console_resp.text
    assert "میزکار عملیات" in console_resp.text
    assert "رهگیری ارتباط فرایندها" in console_resp.text
    assert "مدیریت کاربران" in console_resp.text

    review_console_resp = client.get("/review-console")
    assert review_console_resp.status_code == 200, review_console_resp.text
    assert "کنسول کنترل فرایند بورنا" in review_console_resp.text
