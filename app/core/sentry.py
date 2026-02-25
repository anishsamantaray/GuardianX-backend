import os

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration

_SENTRY_INITIALIZED = False


def _get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def init_sentry(*, service_name: str, enable_fastapi: bool = False, enable_lambda: bool = False) -> bool:
    global _SENTRY_INITIALIZED

    if _SENTRY_INITIALIZED:
        return True

    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return False

    integrations = []
    if enable_fastapi:
        integrations.append(FastApiIntegration())
    if enable_lambda:
        integrations.append(AwsLambdaIntegration(timeout_warning=True))

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT") or os.getenv("ENVIRONMENT") or "development",
        release=os.getenv("SENTRY_RELEASE"),
        traces_sample_rate=_get_float_env("SENTRY_TRACES_SAMPLE_RATE", 0.0),
        profiles_sample_rate=_get_float_env("SENTRY_PROFILES_SAMPLE_RATE", 0.0),
        send_default_pii=False,
        integrations=integrations,
        server_name=service_name,
    )

    _SENTRY_INITIALIZED = True
    return True
