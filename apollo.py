#!/bin/env python
from typing import Optional
from json import dumps, loads
from random import randint
from datetime import datetime, timedelta, timezone
from time import sleep

import typer

from agent import ApolloAgent

GMT_8_TZ: timezone = timezone(timedelta(hours=8))

app = typer.Typer()

agent: ApolloAgent = None
auth_d: dict = None


def _wait_for_datetime_passed(target: datetime, sleep_sec: int = 1):
    print(f"waiting for {target} with sleep interval {sleep_sec}s ...")
    while True:
        if datetime.now() >= target:
            break

        sleep(sleep_sec)


def print_json(data: dict, indent=2):
    def _default(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        raise TypeError(f"can not handle {obj} (type=type(obj))")

    print(
        dumps(data, indent=indent, ensure_ascii=False, sort_keys=True, default=_default)
    )


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


def _do_auto_punch_loop(
    in_dt: datetime,
    out_dt: datetime,
    jitter: int = 60,
):
    in_time_dt: datetime = in_dt - timedelta(seconds=randint(0, jitter))
    out_time_dt: datetime = out_dt + timedelta(seconds=randint(0, jitter))

    print(f"auto punch in @ {in_time_dt}")
    print(f"auto punch out @ {out_time_dt}")

    print()

    _wait_for_datetime_passed(in_time_dt)
    print(f"auto punching in @ {datetime.now()}")
    print_json(agent.punch_in())

    _wait_for_datetime_passed(out_time_dt)
    print(f"auto punching out @ {datetime.now()}")
    print_json(agent.punch_out())


def check_is_workay_and_auto_punch(jitter: int = 60, force: bool = False):
    prepare_login_agent()

    cal = get_today_worday_calendar()
    print(f'now date = {cal["date"]}')
    if not cal["is_work_day"]:
        print("not work day")
        if not force:
            return

        print("force bypass work day check")

    _do_auto_punch_loop(cal["work_on_time"], cal["work_off_time"], jitter=jitter)


@app.command()
def auto_punch(
    auto_work_day_check: bool = True,
    jitter: int = typer.Option(60, help="random jitter seconds"),
):
    while True:
        now = datetime.now()

        if now.hour >= 8:
            print(f"if passed 8AM, auto punch will only be effective from next morning")
            now += timedelta(days=1)

        _wait_for_datetime_passed(
            datetime(now.year, now.month, now.day, 7), sleep_sec=60
        )
        check_is_workay_and_auto_punch(jitter=jitter, force=not auto_work_day_check)


@app.command()
def test():
    print(agent.get_sys_date())
    print(agent.get_employee_role())
    # print(get_workday_calendars())
    print_json(get_today_worday_calendar())


def prepare_login_agent():
    global agent
    agent = ApolloAgent(**auth_d)
    agent.login()


def get_workday_calendars() -> dict[str, dict]:
    calendars = agent.get_employee_calendar()["Data"]["Calendars"]
    result_map: dict[str, dict] = {}

    for c in calendars:
        cal = {
            "date": c["Date"].split("T")[0],
            "work_on_time": datetime.fromisoformat(c["ShiftSchedule"]["WorkOnTime"])
            .astimezone(GMT_8_TZ)
            .replace(tzinfo=None)
            if c["ShiftSchedule"]["WorkOnTime"]
            else None,
            "work_off_time": datetime.fromisoformat(c["ShiftSchedule"]["WorkOffTime"])
            .astimezone(GMT_8_TZ)
            .replace(tzinfo=None)
            if c["ShiftSchedule"]["WorkOffTime"]
            else None,
        }

        cal["is_work_day"] = bool(cal["work_on_time"] and cal["work_off_time"])
        cal["memo"] = (
            c["CalendarEvent"]["EventMemo"]
            if c["CalendarEvent"]
            else ("工作日" if cal["is_work_day"] else "休假日")
        )

        # print(cal)
        result_map[cal["date"]] = cal

    return result_map


def get_today_worday_calendar():
    dt_to_cal_map = get_workday_calendars()
    return dt_to_cal_map[datetime.now().strftime("%Y-%m-%d")]


@app.callback()
def main(ctx: typer.Context, config: str = typer.Option(None, help="config username")):
    global auth_d

    if ctx.invoked_subcommand == "init":
        return

    if not config:
        print("please provide a user config name via --config option")
        print("or create via init sub command if you don't have one")
        raise typer.Exit(code=-1)

    try:
        auth_d = loads(open(f"{config}.json").read())
    except IOError as e:
        print(e)
        raise typer.Exit(code=-1)

    if ctx.invoked_subcommand != "auto-punch":
        prepare_login_agent()


if __name__ == "__main__":
    app()
