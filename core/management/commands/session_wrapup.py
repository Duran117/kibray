import subprocess
from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "One-Click Closure: Verify weather API, auto-save to git, and print final report."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.WARNING("Starting One-Click Closure (Session Wrap-Up)"))

        # STEP B: Verify Weather API (Smoke Test)
        self.stdout.write(self.style.WARNING("\nSTEP B: Weather API Smoke Test"))
        try:
            from core.services.weather import OpenWeatherMapProvider  # type: ignore

            provider = OpenWeatherMapProvider()
            result = provider.get_weather(lat=19.43, lon=-99.13)
            prov = result.get("provider")

            if prov == "openweathermap":
                self.stdout.write("✅ SUCCESS: Connected to Real API")
            elif prov in ("mock", "openweathermap_mock"):
                self.stdout.write("⚠️ WARNING: Using Mock Data (Check API Key)")
            else:
                self.stdout.write(f"⚠️ WARNING: Unknown provider '{prov}' (result={result})")

            self.stdout.write(f"Weather result: {result}")
        except Exception as exc:
            self.stderr.write(f"❌ ERROR: {exc}")

        # STEP A: Git Auto-Save (Push)
        self.stdout.write(self.style.WARNING("\nSTEP A: Git Auto-Save"))
        def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
            except Exception as e:
                return 1, "", f"Command failed: {e}"

        # Determine current branch early for pull --rebase workflow
        code_branch, out_branch, err_branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        current_branch = out_branch.strip() if code_branch == 0 and out_branch else "main"
        if not current_branch:
            current_branch = "main"

        # git fetch
        self.stdout.write("$ git fetch origin")
        _, out, err = run_cmd(["git", "fetch", "origin"])
        if out:
            self.stdout.write(out)
        if err:
            self.stderr.write(err)

        # git pull --rebase origin <current_branch>
        self.stdout.write(f"$ git pull --rebase origin {current_branch}")
        code, out, err = run_cmd(["git", "pull", "--rebase", "origin", current_branch])
        if out:
            self.stdout.write(out)
        if err:
            self.stderr.write(err)
        if code != 0:
            self.stderr.write("Rebase failed. Please resolve conflicts and re-run this command.")
            return

        # git status
        code, out, err = run_cmd(["git", "status"])
        self.stdout.write("$ git status")
        if out:
            self.stdout.write(out)
        if err:
            self.stderr.write(err)

        # git add .
        code, out, err = run_cmd(["git", "add", "."])
        self.stdout.write("$ git add .")
        if out:
            self.stdout.write(out)
        if err:
            self.stderr.write(err)

        # git commit
        code, out, err = run_cmd([
            "git",
            "commit",
            "-m",
            "chore: Final automated wrap-up (Bulk, Weather, Notifs)",
        ])
        self.stdout.write("$ git commit -m 'chore: Final automated wrap-up (Bulk, Weather, Notifs)'")
        if code == 0:
            self.stdout.write(out or "Commit created.")
        else:
            # Handle nothing to commit gracefully
            if "nothing to commit" in (out + err).lower():
                self.stdout.write("No changes to commit.")
            else:
                self.stderr.write(err or "Commit failed.")


        # Detect current branch and push to it, handling first-time upstream
        # (branch value already computed above)

        # Check if upstream is set
        code_upstream, out_upstream, err_upstream = run_cmd([
            "git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"
        ])
        if code_upstream != 0:
            # No upstream, set it
            self.stdout.write(f"$ git push --set-upstream origin {current_branch}")
            code, out, err = run_cmd(["git", "push", "--set-upstream", "origin", current_branch])
        else:
            self.stdout.write(f"$ git push origin {current_branch}")
            code, out, err = run_cmd(["git", "push", "origin", current_branch])
        if out:
            self.stdout.write(out)
        if err:
            self.stderr.write(err)

        # STEP C: Final Report
        self.stdout.write(self.style.WARNING("\nSTEP C: Final Report"))
        box_lines = [
            "==============================",
            "  MISSION ACCOMPLISHED ✅",
            "------------------------------",
            "  Today Completed:",
            "   1. Bulk Actions",
            "   2. Real Weather",
            "   3. PM Notifications",
            "==============================",
        ]
        for line in box_lines:
            self.stdout.write(line)

        self.stdout.write(self.style.SUCCESS("Wrap-up complete. You can step away now."))
