
from app.utils.logs import logger
import fire
import uvicorn


class Cli:
    @staticmethod
    def run(
        port=8000,
        workers=1,
    ):
        """
        Run forwarding serve.
        """

        uvicorn.run(
            app="app.main:app",
            host="0.0.0.0",
            port=port,
            workers=workers,
            app_dir=".",
        )


def main():
    fire.Fire(Cli)


if __name__ == "__main__":
    main()
