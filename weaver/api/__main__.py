import uvicorn

from weaver.config import settings


def main() -> None:
    uvicorn.run(
        "weaver.api.main:app",
        host="0.0.0.0",
        port=8787,
        reload=False,
    )


if __name__ == "__main__":
    main()
