"""Real-browser checks. Assemble _site first; a local server starts automatically.

Requires Playwright for Python and Edge (or set BROWSER_CHANNEL to chromium).
Does not replace Python unit tests; exercises the actual CDN/Pyodide bridge.
"""

import json
import os
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright


@contextmanager
def site_url():
    if os.getenv("SITE_URL"):
        yield os.environ["SITE_URL"].rstrip("/")
        return

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(Path("_site").resolve())))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def main():
    output = Path("_site/qa")
    output.mkdir(parents=True, exist_ok=True)
    errors = []
    with site_url() as url, sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=os.getenv("BROWSER_CHANNEL", "msedge"))
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url + "/")
        page.locator("#new").wait_for(state="visible")
        page.wait_for_function("!document.querySelector('#new').disabled", timeout=120000)
        assert page.locator("#phase-title").inner_text() == "Prepare seu esquadrão."
        page.get_by_role("button", name="Recrutar Guardião, 4 suprimentos", exact=True).click()
        page.get_by_role("button", name="Mover para retaguarda · grátis", exact=True).click()
        assert page.locator("#ally-back .piece").count() == 1
        assert page.locator("#resources").inner_text() == "6"
        assert page.evaluate("state.acted.length") == 0
        page.get_by_role("button", name="Devolver recruta · +4 suprimentos", exact=True).click()
        assert page.locator("#resources").inner_text() == "10"
        assert page.locator(".ally-lane .piece").count() == 0
        page.get_by_role("button", name="Recrutar Guardião, 4 suprimentos", exact=True).click()
        page.get_by_role("button", name="Recrutar Arqueiro, 3 suprimentos", exact=True).click()
        page.get_by_role("button", name="Recrutar Soldado, 2 suprimentos", exact=True).click()
        assert page.locator("#resources").inner_text() == "1"
        assert page.locator("#shop button:enabled").count() == 0
        page.screenshot(path=str(output / "desktop-recruit.png"), full_page=True)
        page.locator("#advance").click()
        assert page.evaluate("state.phase") == "combat"
        page.locator("#actions button", has_text="Atacar").click()
        assert "dano" in page.locator("#targets button").first.inner_text()
        assert page.locator(".target-preview").count() > 0
        page.screenshot(path=str(output / "desktop-combat.png"), full_page=True)
        before = page.evaluate("JSON.stringify(state)")
        page.wait_for_timeout(1100)
        assert (
            page.evaluate("JSON.stringify(state)") == before
        ), "Battle advanced without player command"
        page.locator("#targets button").first.click()
        # Complete a match through visible controls, including review and recruitment.
        for _ in range(400):
            phase = page.evaluate("state.phase")
            if phase == "finished":
                break
            if phase == "recruit":
                shop = page.get_by_role(
                    "button", name="Recrutar Arqueiro, 3 suprimentos", exact=True
                )
                if shop.is_enabled():
                    shop.click()
                else:
                    page.locator("#advance").click()
            elif phase == "review":
                page.locator("#advance").click()
            else:
                if not page.locator("#actions button").count():
                    page.locator(".ally-lane .piece:enabled").first.click()
                page.locator("#actions button:enabled").first.click()
                page.locator("#targets button").first.click()
        else:
            raise AssertionError("Match did not finish")
        page.screenshot(path=str(output / "desktop-result.png"), full_page=True)
        with page.expect_download() as downloaded:
            page.locator("#export").click()
        downloaded.value.save_as(str(output / "report.json"))
        report = json.loads((output / "report.json").read_text())
        assert report["state"]["phase"] == "finished"
        assert report["commands"] and report["ruleset"] == "tactical-v3"
        page.locator("#new").click()
        page.locator("#seed").fill("0")
        page.locator("#rounds").fill("3")
        page.get_by_role("button", name="Começar partida", exact=True).click()
        assert page.locator("#resources").inner_text() == "10"
        page.get_by_role("button", name="Recrutar Guardião, 4 suprimentos", exact=True).click()
        page.get_by_role("button", name="Recrutar Arqueiro, 3 suprimentos", exact=True).click()
        page.locator("#advance").click()
        for width in (320, 375, 390, 768, 1024, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            ), f"Horizontal overflow at {width}"
            page.screenshot(path=str(output / f"combat-{width}.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.locator(".ally-lane .piece:enabled").first.click()
        page.locator("#actions button", has_text="Reposicionar").click()
        page.locator("#targets button").first.click()
        page.get_by_role("button", name="Como jogar", exact=True).click()
        assert page.locator("#help-dialog").is_visible()
        page.keyboard.press("Escape")
        assert not page.locator("#help-dialog").is_visible()
        # Heavy weapons remain selectable while reloading, with defensive orders.
        page.locator("#new").click()
        page.locator("#opponent").select_option("economy")
        page.locator("#seed").fill("0")
        page.get_by_role("button", name="Começar partida", exact=True).click()
        page.get_by_role("button", name="Recrutar Tanque, 5 suprimentos", exact=True).click()
        page.get_by_role("button", name="Recrutar Guardião, 4 suprimentos", exact=True).click()
        page.locator("#advance").click()
        page.locator('.piece[data-kind="tank"]').click()
        page.locator("#actions button", has_text="Atacar").click()
        page.locator("#targets button").first.click()
        assert "Arma: R3" in page.locator('.piece[data-kind="tank"] .weapon-state').inner_text()
        page.locator("#actions button", has_text="Esperar").click()
        page.locator("#targets button").first.click()
        page.locator("#advance").click()
        page.locator("#advance").click()
        page.locator('.ally-lane .piece[data-kind="tank"]').click()
        assert page.locator("#actions button", has_text="Atacar").is_disabled()
        assert page.locator("#actions button", has_text="Proteger").is_enabled()
        assert "rodada 3" in page.locator(".reload-hint").inner_text()
        page.screenshot(path=str(output / "reload-mobile.png"), full_page=True)
        page.emulate_media(reduced_motion="reduce")
        page.reload()
        page.wait_for_function("!document.querySelector('#new').disabled", timeout=120000)
        assert page.evaluate("state.phase") == "recruit"
        # Legacy lab still imports the bridge, runs battle and tournament.
        page.goto(url + "/simulator.html")
        page.wait_for_function("!document.querySelector('#b-run').disabled", timeout=120000)
        page.locator("#b-rounds").fill("3")
        page.locator("#b-run").click()
        page.locator("#t-end").click()
        page.locator("#tab-tournament").click()
        page.locator("#t-sims").fill("2")
        page.locator("#t-seeds").fill("11")
        page.locator("#t-rounds").fill("3")
        page.locator("#t-run").click()
        page.wait_for_function("!document.querySelector('#t-run').disabled")
        assert page.locator("#t-out table").count() > 0
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        ), "Laboratory overflow"
        page.screenshot(path=str(output / "lab-mobile.png"), full_page=True)
        assert not errors, errors
        # An unavailable CDN must leave help usable and expose an explicit retry.
        offline = browser.new_page(viewport={"width": 390, "height": 844})
        offline.route("https://cdn.jsdelivr.net/**", lambda route: route.abort())
        offline.goto(url + "/")
        offline.locator("#retry").wait_for(state="visible")
        assert offline.locator("#advance").is_disabled()
        offline.get_by_role("button", name="Como jogar", exact=True).click()
        assert offline.locator("#help-dialog").is_visible()
        offline.close()
        browser.close()
    print(
        "Browser OK: complete game, download, restart, mobile actions, six widths, help, reload, battle, tournament and CDN failure."
    )


if __name__ == "__main__":
    main()
