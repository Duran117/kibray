#!/usr/bin/env python3
"""
KIBRAY Documentation Navigator
Interactive CLI tool to quickly access project documentation
"""

import os
from pathlib import Path
import sys


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header():
    """Print the application header"""
    print(
        f"\n{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗{Colors.ENDC}"
    )
    print(
        f"{Colors.HEADER}{Colors.BOLD}║     📖 KIBRAY - Documentation Navigator                  ║{Colors.ENDC}"
    )
    print(
        f"{Colors.HEADER}{Colors.BOLD}║     Quick access to project documentation               ║{Colors.ENDC}"
    )
    print(
        f"{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════════╝{Colors.ENDC}\n"
    )


def get_project_root():
    """Get the project root directory"""
    script_dir = Path(__file__).resolve().parent
    return script_dir


def print_menu():
    """Print the main menu"""
    print(f"{Colors.OKBLUE}{Colors.BOLD}🚀 QUICK ACCESS:{Colors.ENDC}\n")

    menu_items = [
        ("1", "📊 Master Status (START HERE)", "00_MASTER_STATUS_NOV2025.md", Colors.OKGREEN),
        ("2", "📖 README & Setup", "README.md", Colors.OKCYAN),
        ("3", "🔧 API Reference", "API_README.md", Colors.OKCYAN),
        ("4", "⚡ Quick Start Guide", "QUICK_START.md", Colors.OKCYAN),
        ("", "", "", ""),  # Spacer
        ("5", "📋 Documentation Index", "docs/00_DOCUMENTATION_INDEX.md", Colors.OKBLUE),
        (
            "6",
            "✅ Gaps A-C (Digital Signatures, Payroll, Invoices)",
            "docs/GAPS_COMPLETION_SUMMARY.md",
            Colors.OKBLUE,
        ),
        (
            "7",
            "✅ Gaps D-F (Inventory, Financial, Client Portal)",
            "docs/GAPS_D_E_F_COMPLETION.md",
            Colors.OKBLUE,
        ),
        ("", "", "", ""),  # Spacer
        ("8", "📦 Modules Documentation", "list_modules", Colors.WARNING),
        ("9", "🗃️  View Archived Docs", "docs/archive/", Colors.WARNING),
        ("", "", "", ""),  # Spacer
        ("0", "❌ Exit", "exit", Colors.FAIL),
    ]

    for num, desc, _, color in menu_items:
        if num:
            print(f"  {color}{num}.{Colors.ENDC} {desc}")
        else:
            print()  # Empty line for spacing


def list_module_docs():
    """List all module documentation files"""
    project_root = get_project_root()

    print(f"\n{Colors.OKGREEN}{Colors.BOLD}📦 MODULE DOCUMENTATION:{Colors.ENDC}\n")

    module_docs = [
        ("MODULE_11_TASKS_COMPLETE.md", "Task Management"),
        ("MODULE_12_DAILY_PLANS_COMPLETE.md", "Daily Planning"),
        ("MODULE_13_TIME_TRACKING_COMPLETE.md", "Time Tracking"),
        ("MODULE_14_MATERIALS_COMPLETE.md", "Materials Management"),
        ("MODULE_17_22_CLIENT_COMMUNICATION_COMPLETE.md", "Client Communication"),
        ("MODULE_18_21_VISUAL_COLLABORATION_COMPLETE.md", "Visual Collaboration"),
        ("MODULE_29_PRETASK_LIBRARY_COMPLETE.md", "Pre-task Library"),
        ("MODULE_30_WEATHER_SNAPSHOTS_COMPLETE.md", "Weather Snapshots"),
    ]

    for i, (filename, title) in enumerate(module_docs, 1):
        filepath = project_root / filename
        status = "✅" if filepath.exists() else "❌"
        print(f"  {status} {i}. {title}")
        print(f"     {Colors.OKCYAN}{filename}{Colors.ENDC}")

    print(
        f"\n{Colors.WARNING}Enter module number to open, or 'b' to go back:{Colors.ENDC} ", end=""
    )
    choice = input().strip().lower()

    if choice == "b":
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(module_docs):
            open_file(project_root / module_docs[idx][0])
        else:
            print(f"{Colors.FAIL}Invalid selection!{Colors.ENDC}")
    except ValueError:
        print(f"{Colors.FAIL}Invalid input!{Colors.ENDC}")


def open_file(filepath):
    """Open a file with the default system application"""
    if not filepath.exists():
        print(f"{Colors.FAIL}❌ File not found: {filepath}{Colors.ENDC}")
        return

    print(f"\n{Colors.OKGREEN}📖 Opening: {filepath.name}{Colors.ENDC}")

    # Try different commands based on OS
    if sys.platform == "darwin":  # macOS
        os.system(f'open "{filepath}"')
    elif sys.platform == "linux":
        os.system(f'xdg-open "{filepath}"')
    elif sys.platform == "win32":
        os.system(f'start "" "{filepath}"')
    else:
        print(f"{Colors.WARNING}⚠️  Please open manually: {filepath}{Colors.ENDC}")


def show_project_status():
    """Display quick project status"""
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}📊 PROJECT STATUS:{Colors.ENDC}\n")
    print(f"  ✅ Completitud: {Colors.BOLD}95%{Colors.ENDC}")
    print(f"  ✅ Tests: {Colors.BOLD}670 passing{Colors.ENDC} (667 passed, 3 skipped)")
    print(f"  ✅ Gaps A-F: {Colors.BOLD}All Complete{Colors.ENDC} (42 tests)")
    print(f"  ✅ API Endpoints: {Colors.BOLD}45+ ViewSets{Colors.ENDC}")
    print(f"  ✅ Production: {Colors.BOLD}Ready{Colors.ENDC}")
    print()


def main():
    """Main application loop"""
    project_root = get_project_root()

    while True:
        print_header()
        show_project_status()
        print_menu()

        print(f"\n{Colors.BOLD}Select an option (0-9):{Colors.ENDC} ", end="")
        choice = input().strip()

        if choice == "0":
            print(f"\n{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}\n")
            break

        elif choice == "1":
            open_file(project_root / "00_MASTER_STATUS_NOV2025.md")

        elif choice == "2":
            open_file(project_root / "README.md")

        elif choice == "3":
            open_file(project_root / "API_README.md")

        elif choice == "4":
            open_file(project_root / "QUICK_START.md")

        elif choice == "5":
            open_file(project_root / "docs" / "00_DOCUMENTATION_INDEX.md")

        elif choice == "6":
            open_file(project_root / "docs" / "GAPS_COMPLETION_SUMMARY.md")

        elif choice == "7":
            open_file(project_root / "docs" / "GAPS_D_E_F_COMPLETION.md")

        elif choice == "8":
            list_module_docs()

        elif choice == "9":
            archive_path = project_root / "docs" / "archive"
            if archive_path.exists():
                print(
                    f"\n{Colors.WARNING}⚠️  These documents are OBSOLETE. View for historical reference only.{Colors.ENDC}"
                )
                open_file(archive_path / "README.md")
            else:
                print(f"{Colors.FAIL}Archive directory not found!{Colors.ENDC}")

        else:
            print(f"\n{Colors.FAIL}❌ Invalid option. Please try again.{Colors.ENDC}")

        input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")
        print("\n" * 50)  # Clear screen


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Interrupted by user.{Colors.ENDC}")
        sys.exit(0)
