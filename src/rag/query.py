from src.rag.engines import build_router
from src.guardrails.fast_filter import check_input, check_output


_BLOCKED_INPUT = "Извините, я не могу ответить на этот вопрос. Он нарушает политику безопасности."
_BLOCKED_OUTPUT = "Ответ не прошёл проверку безопасности. Попробуйте переформулировать запрос."

_router = None


def _lazy_init():
    global _router
    if _router is None:
        _router = build_router()


def ask(question: str, verbose: bool = False) -> str:
    _lazy_init()

    if check_input(question):
        return _BLOCKED_INPUT

    response = _router.query(question)
    answer = str(response)

    if verbose:
        print(f"[debug] {answer[:200]}...")

    if check_output(answer):
        return _BLOCKED_OUTPUT

    return answer