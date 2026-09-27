"""
CLI нейро-бухгалтера.

Примеры:
    python -m src.cli
    python -m src.cli -q "Какая ставка НДС в 2025 году?"
    python -m src.cli -q "..." -v
"""
from __future__ import annotations

import argparse
import sys
import time

from src.rag.query import ask


def _print_banner() -> None:
    print("=" * 70)
    print("  🤖 Нейро-бухгалтер")
    print("  Введите вопрос или 'exit' / 'quit' для выхода.")
    print("  Спецкоманды: :help, :verbose, :clear")
    print("=" * 70)


def _print_help() -> None:
    print("""
Доступные команды:
  :help       — эта справка
  :verbose    — переключить подробный режим (показывает ответ роутера)
  :clear      — очистить экран
  exit, quit  — выйти
""")


def _interactive(verbose: bool) -> int:
    _print_banner()
    print(f"Verbose: {'ON' if verbose else 'OFF'}\n")

    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not q:
            continue

        if q.lower() in {"exit", "quit"}:
            break

        if q == ":help":
            _print_help()
            continue

        if q == ":verbose":
            verbose = not verbose
            print(f"Verbose: {'ON' if verbose else 'OFF'}")
            continue

        if q == ":clear":
            print("\033[2J\033[H", end="")
            continue

        t0 = time.time()
        try:
            answer = ask(q, verbose=verbose)
        except Exception as e:
            print(f"[!] Ошибка: {e}")
            continue
        dt = time.time() - t0

        print()
        print(answer)
        print(f"\n[{dt:.2f} сек]")
        print("-" * 70)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="src.cli",
        description="CLI нейро-бухгалтера",
    )
    parser.add_argument("-q", "--query", default=None,
                        help="Один вопрос — и выход")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Показывать отладку")
    args = parser.parse_args()

    if args.query:
        t0 = time.time()
        answer = ask(args.query, verbose=args.verbose)
        dt = time.time() - t0
        print(answer)
        if args.verbose:
            print(f"\n[{dt:.2f} сек]")
        return 0

    return _interactive(args.verbose)


if __name__ == "__main__":
    sys.exit(main())