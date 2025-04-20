from seleniumbase import SB

with SB(uc=True, test=True, locale="en") as sb:
    url = "https://www.backmarket.de/de-de/l/samsung-galaxy-s8/0c94cba0-ea6a-4a84-be84-09b4df8f6b9b"
    sb.activate_cdp_mode(url)
    sb.uc_gui_click_captcha()
    sb.sleep(2)