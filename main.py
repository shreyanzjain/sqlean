from src.cli_engine import CLIEngine

def main():
    """
    Main entry point for the SQLean application.
    """
    engine = CLIEngine()
    engine.run()

if __name__ == "__main__":
    main()