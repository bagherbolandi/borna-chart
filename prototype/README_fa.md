# راهنمای Prototype اکسل

## فایل اصلی
- `Borna_Process_Control_Prototype.xlsx`

## قالب‌های منبع
- پوشه `csv/` شامل قالب هر Sheet است.

## نحوه بازتولید فایل
از ریشه ریپو اجرا کنید:

```bash
python scripts/build_excel_prototype.py
```

## نکات
- این فایل در حال حاضر یک **Prototype ساختاریافته** است، نه نسخه نهایی عملیاتی.
- Sheetها، Headerها و ساختار رابطه‌ای طبق طراحی سامانه ساخته شده‌اند.
- برای نسخه بعدی می‌توان Validation، رنگ‌بندی، Pivot Dashboard و Macro/Script کنترلی اضافه کرد.
