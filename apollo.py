from typing import Optional
from json import dumps, loads

import typer

from agent import ApolloAgent

app = typer.Typer()
agent: ApolloAgent = None


@app.command()
def init(
    username: str = typer.Option(...),
    password: str = typer.Option(...),
    company: str = typer.Option(...),
):
    """
    init config file
    """
    payload = {"username": username, "password": password, "company": company}

    print(f"writing ur config into {username}.json")
    with open(f"{username}.json", "w") as f:
        f.write(dumps(payload, indent=2))
    print("done")


@app.command()
def punch_in():
    print(agent.punch_in())


@app.command()
def punch_out():
    print(agent.punch_out())


@app.command()
def test():
    print(agent.get_sys_date())
    print(agent.get_employee_role())


def prepare_login_agent(username: str, password: str, company: str):
    global agent
    agent = ApolloAgent(username=username, password=password, company=company)
    agent.login()


@app.callback()
def main(ctx: typer.Context, config: str = typer.Option(None, help="config username")):
    if ctx.invoked_subcommand == "init":
        return

    if not config:
        print("please provide a user config name via --config option")
        print("or create via init sub command if you don't have one")
        raise typer.Exit(code=-1)

    try:
        config = loads(open(f"{config}.json").read())
        prepare_login_agent(**config)
    except IOError as e:
        print(e)
        raise typer.Exit(code=-1)


if __name__ == "__main__":
    app()
