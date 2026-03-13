"""
生成 ChatGPT 订阅支付链接

用法:
  交互模式:  cd backend && python scripts/generate_chatgpt_pay_link.py
  命令行:    cd backend && python scripts/generate_chatgpt_pay_link.py --token <JWT>
  指定计划:  cd backend && python scripts/generate_chatgpt_pay_link.py --token <JWT> --plan plus
"""
import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

AIMIZY_URL = "https://team.aimizy.com/api/public/generate-payment-link"

PLANS = {
    "team": "chatgptteamplan",
    "plus": "chatgptplusplan",
    "pro": "chatgptproplan",
}


def build_payload(token: str, plan: str = "team", seats: int = 5,
                  interval: str = "month", promo: str = "team-1-month-free") -> dict:
    return {
        "access_token": token,
        "plan_name": PLANS.get(plan, plan),
        "country": "US",
        "currency": "USD",
        "promo_campaign_id": promo,
        "is_coupon_from_query_param": True,
        "seat_quantity": seats,
        "price_interval": interval,
        "check_card_proxy": False,
        "is_short_link": True,
    }


async def generate(payload: dict) -> str | None:
    """调用 aimizy API，返回支付链接"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(AIMIZY_URL, json=payload)

    if resp.status_code != 200:
        print(f"❌ 请求失败 (HTTP {resp.status_code}): {resp.text[:500]}")
        return None

    data = resp.json()
    if not data.get("success"):
        print(f"❌ 业务失败: {data}")
        return None

    return data.get("url")


def interactive_collect() -> dict:
    """交互式收集参数"""
    print("\n===== ChatGPT 支付链接生成 =====\n")

    token = input("请粘贴 access_token: ").strip()
    if not token:
        print("❌ access_token 不能为空")
        sys.exit(1)

    print("\n选择计划:  1) Team  2) Plus  3) Pro")
    choice = input("编号 [1]: ").strip() or "1"
    plan = {"1": "team", "2": "plus", "3": "pro"}.get(choice, "team")

    seats = 5
    if plan == "team":
        s = input("席位数 [5]: ").strip()
        if s.isdigit() and int(s) > 0:
            seats = int(s)

    print("\n计费周期:  1) month  2) year")
    ic = input("编号 [1]: ").strip() or "1"
    interval = "year" if ic == "2" else "month"

    return build_payload(token, plan, seats, interval)


async def main():
    parser = argparse.ArgumentParser(description="生成 ChatGPT 支付链接")
    parser.add_argument("--token", help="OpenAI access_token")
    parser.add_argument("--plan", choices=["team", "plus", "pro"], default="team")
    parser.add_argument("--seats", type=int, default=5)
    parser.add_argument("--interval", choices=["month", "year"], default="month")
    parser.add_argument("--promo", default="team-1-month-free")
    args = parser.parse_args()

    if args.token:
        payload = build_payload(args.token, args.plan, args.seats, args.interval, args.promo)
    else:
        payload = interactive_collect()

    plan_label = args.plan if args.token else payload["plan_name"]
    print(f"\n⏳ 正在生成 {plan_label} 支付链接...")

    url = await generate(payload)
    if url:
        print(f"\n✅ 支付链接:\n   {url}")


if __name__ == "__main__":
    asyncio.run(main())
