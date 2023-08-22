
from fastapi import FastAPI
from app.routers.relay import router as relay_router
from app.utils.conf import OPEN_SENTRY, SENTRY_NSD

if OPEN_SENTRY:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_NSD,
        traces_sample_rate=1.0,
    )

app = FastAPI()


@app.get('/ping')
def ping():
    return "PONG"


app.include_router(relay_router)



