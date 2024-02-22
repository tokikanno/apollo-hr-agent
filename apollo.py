#!/bin/env python
from typing import Optional
from json import dumps, loads
from random import randint
from datetime import datetime, timedelta, timezone
from time import sleep

import typer

from agent import ApolloAgent

LOCAL_TZ: timezone = datetime.now().astimezone().tzinfo

app = typer.Typer(no_args_is_help=True)

agent: ApolloAgent = None
auth_d: dict = None

AUTO_WAIT_INTERVAL_ENTRIES = (
    (7200, 3600),
    (3600, 1800),
    (600, 300),
    (60, 30),
    (0, 1),
)


def _get_auto_wait_interval(target: datetime):
    time_delta_to_target = target - datetime.now()
    total_secs = time_delta_to_target.total_seconds()
    for d, s in AUTO_WAIT_INTERVAL_ENTRIES:
        if total_secs >= d:
            return s

    return 0


def _wait_for_datetime_passed(target: datetime):
    print(f"[{datetime.now()}] waiting for {target}...")
    while True:
        if datetime.now() >= target:
            break

        sleep_sec = _get_auto_wait_interval(target=target)
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
    jitter: int = typer.Option(60, help="random jitter seconds"), force: bool = False
):
    while True:
        now = datetime.now()

        if now.hour >= 7 and not force:
            print(f"if passed 7AM, auto punch will only be effective from next morning")
        else:
            check_is_workay_and_auto_punch(jitter=jitter, force=force)

        _wait_for_datetime_passed(
            datetime(now.year, now.month, now.day, 6, 59) + timedelta(days=1)
        )


@app.command()
def test():
    print(agent.get_sys_date())
    print(agent.get_employee_role())
    print_json(get_workday_calendars())
    # print_json(get_today_worday_calendar())


def prepare_login_agent():
    global agent
    agent = ApolloAgent(**auth_d)
    agent.login()


def get_workday_calendars() -> dict[str, dict]:
    calendars = agent.get_employee_calendar()["Data"]["Calendars"]
    result_map: dict[str, dict] = {}

    def _parse_as_gmt_8_dt(dt_str: Optional[str]):
        if not dt_str:
            return None

        return datetime.fromisoformat(dt_str).astimezone(LOCAL_TZ).replace(tzinfo=None)

    for c in calendars:
        cal = {
            "date": c["Date"].split("T")[0],
            "work_on_time": _parse_as_gmt_8_dt(c["ShiftSchedule"]["WorkOnTime"]),
            "work_off_time": _parse_as_gmt_8_dt(c["ShiftSchedule"]["WorkOffTime"]),
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
