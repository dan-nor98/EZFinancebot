from typing import Annotated, Any

import httpx
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

from finance.shared.config import get_settings

app = FastAPI(title="EZFinance Telegram Gateway")
CORE_URL = "http://api:8000"


def persian_digits(value: int) -> str:
    return f"{value:,}".translate(str.maketrans("0123456789,", "۰۱۲۳۴۵۶۷۸۹٬"))


def confirmation(transaction: dict[str, Any]) -> str:
    if transaction["status"] == "INCOMPLETE":
        return "تراکنش ناقص ثبت شد؛ بعداً برای تکمیل آن از شما می‌پرسیم."
    labels = {
        "EXPENSE": "هزینه ثبت شد",
        "INCOME": "درآمد ثبت شد",
        "TRANSPORTATION": "حمل‌ونقل",
        "FOOD": "خوراک",
        "SALARY": "حقوق",
    }
    amount = int(transaction["amountIrr"]) // 10
    title = labels.get(transaction["type"], "تراکنش ثبت شد")
    category_code = transaction.get("category")
    category = labels.get(str(category_code), "بدون دسته‌بندی")
    return f"{title}\n\nمبلغ: {persian_digits(amount)} تومان\nدسته‌بندی: {category}"


async def telegram(method: str, payload: dict[str, Any]) -> None:
    token = get_settings().telegram_bot_token
    if not token:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"https://api.telegram.org/bot{token}/{method}", json=payload)


@app.get("/health/live")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def webhook(
    update: dict[str, Any], x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None
) -> JSONResponse:
    settings = get_settings()
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        return JSONResponse({"ok": False}, 403)
    message = update.get("message") or update.get("edited_message")
    if not message or "text" not in message:
        return JSONResponse({"ok": True})
    sender = message["from"]
    chat_id = message["chat"]["id"]
    text = message["text"]
    headers = {"Authorization": f"Bearer {settings.core_api_key}"}
    async with httpx.AsyncClient(base_url=CORE_URL, headers=headers, timeout=10) as client:
        if text == "/start":
            await client.post(
                "/v1/users/bootstrap",
                json={
                    "externalProvider": "telegram",
                    "externalUserId": str(sender["id"]),
                    "firstName": sender.get("first_name"),
                    "username": sender.get("username"),
                    "languageCode": sender.get("language_code"),
                },
            )
            answer = (
                "سلام! من برای ثبت و مدیریت مالی شخصی کنارتان هستم. یک هزینه یا درآمد را بنویسید."
            )
        else:
            result = await client.post(
                "/v1/capture/text",
                headers={"Idempotency-Key": f"telegram:{update['update_id']}"},
                json={
                    "externalProvider": "telegram",
                    "externalUserId": str(sender["id"]),
                    "text": text,
                    "source": "TELEGRAM",
                },
            )
            answer = (
                confirmation(result.json()["transaction"])
                if result.is_success
                else "ثبت تراکنش انجام نشد. لطفاً دوباره تلاش کنید."
            )
    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": answer,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "ویرایش", "callback_data": "edit"},
                        {"text": "لغو", "callback_data": "void"},
                    ]
                ]
            },
        },
    )
    return JSONResponse({"ok": True})
