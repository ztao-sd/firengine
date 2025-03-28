import typer

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}!")


@app.command()
def goodbye(name: str):
    print(f"Goodbye {name}")


def exchange():
    pass


def fetch():
    pass


def watch():
    pass


def main():
    app()


if __name__ == "__main__":
    main()
