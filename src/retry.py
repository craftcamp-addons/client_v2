import logging

from tenacity import wait_exponential_jitter, retry, RetryCallState


def _retry_logging(retry_state: RetryCallState) -> None:
    if (not retry_state.outcome) or (not retry_state.fn):
        return
    logging.error(
        f"Function {retry_state.fn.__name__} failed, "
        f"{repr(retry_state.outcome.exception())}. "
        f"Retrying attempt: {retry_state.attempt_number}, time_spend: {retry_state.idle_for}"
    )


session_retry = retry(
    wait=wait_exponential_jitter(1, 60),
    after=_retry_logging,
)
