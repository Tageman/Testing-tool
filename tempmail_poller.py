import re
import time
import urllib.parse
import requests


def extract_code(text):
    """从邮件文本中提取 6 位数字验证码，支持中英文格式"""
    patterns = [
        r"验证码[：:]\s*(\d{6})",
        r"验证码[是為]\s*(\d{6})",
        r"code[：: ]*(\d{6})",
        r"(\d{6})\s*is your code",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    # 兜底：找第一个连续 6 位数字
    m = re.search(r"\b(\d{6})\b", text)
    return m.group(1) if m else None


def main():
    email = input("请输入邮箱地址: ").strip()
    if not email:
        print("邮箱地址不能为空")
        return

    encoded_email = urllib.parse.quote(email, safe="")
    url = f"https://tempmail.cn/api/mails/{encoded_email}"
    print(f"开始轮询: {url}")
    print("每3秒请求一次，按 Ctrl+C 停止\n")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    })

    seen_codes = set()
    new_found = False

    try:
        while True:
            try:
                resp = session.get(url, timeout=10)
                print(f"[{time.strftime('%H:%M:%S')}] HTTP {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    mails = data.get("mails", []) if isinstance(data, dict) else data
                    if isinstance(mails, list) and mails:
                        for mail in mails:
                            text = mail.get("text", "")
                            code = extract_code(text)
                            if code:
                                if code not in seen_codes:
                                    seen_codes.add(code)
                                    new_found = True
                                    print(f"  >>> 新验证码: {code} <<<")
                            else:
                                subject = mail.get("subject", "(无主题)")
                                from_addr = mail.get("from", "(未知发件人)")
                                print(f"  {from_addr} → {subject}")
                                if text:
                                    print(f"  邮件原文片段: {text[:150]}")
                    elif isinstance(mails, list):
                        print("  暂无邮件")
                    else:
                        print(f"  响应: {resp.text[:200]}")
                else:
                    print(f"  响应: {resp.text[:200]}")

                if new_found:
                    choice = input("是否停止轮询? (y/n, 默认停止): ").strip().lower()
                    new_found = False
                    if choice != "n":
                        print("已停止轮询")
                        break
                    print("继续轮询...\n")

            except requests.RequestException as e:
                print(f"[{time.strftime('%H:%M:%S')}] 请求失败: {e}")

            time.sleep(3)
    except KeyboardInterrupt:
        print("\n已停止轮询")


if __name__ == "__main__":
    main()
