from apps.telegram_gateway.main import confirmation


def test_gateway_confirmation_is_persian_presentation_only() -> None:
    value = confirmation(
        {
            "type": "EXPENSE",
            "amountIrr": 3_500_000,
            "category": "TRANSPORTATION",
            "status": "COMPLETE",
        }
    )
    assert value == "هزینه ثبت شد\n\nمبلغ: ۳۵۰٬۰۰۰ تومان\nدسته‌بندی: حمل‌ونقل"
