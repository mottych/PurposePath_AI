try:
    from coaching.src.core.config import Settings

    print("Imported Settings")
    s = Settings()
    print("Instantiated Settings")
    print(s.model_dump())
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
