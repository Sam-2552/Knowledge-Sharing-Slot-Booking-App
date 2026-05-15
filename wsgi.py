from app import create_app

application = create_app()

if __name__ == "__main__":
    import os

    host = os.environ.get("APP_HOST", "0.0.0.0")
    port = int(os.environ.get("APP_PORT", "5000"))
    application.run(host=host, port=port, debug=application.config.get("DEBUG", False))
