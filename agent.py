from typing import Optional
from functools import cached_property

import requests
from pyquery import PyQuery as pq


class ApolloAgent:
    def __init__(self, username: str, password: str, company: str):
        self.username: str = username
        self.password: str = password
        self.company: str = company
        self.auth_d: Optional[dict] = None
        self.ticket_d: Optional[dict] = None

    @cached_property
    def session(self):
        session = requests.Session()
        session.headers[
            "User-Agent"
        ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        return session

    def login(self):
        self.get_auth_token()
        self.check_ticket()
        self.get_authorized()

    def get_auth_token(self):
        resp = self.session.get("https://asiaauth.mayohr.com/HRM/Account/Login")
        req_token = pq(resp.content)('input[name="__RequestVerificationToken"]').val()

        resp = self.session.post(
            "https://asiaauth.mayohr.com/Token",
            data={
                "__RequestVerificationToken": req_token,
                "companyCode": self.company,
                "employeeNo": self.username,
                "grant_type": "password",
                "locale": "zh-tw",
                "password": self.password,
                "red": "https://apollo.mayohr.com/tube",
                "userName": f"{self.company}-{self.username}",
            },
        )

        self.auth_d = resp.json()
        # print(dumps(self.auth_d, indent=2))
        return self.auth_d

    def check_ticket(self):
        if not self.auth_d:
            raise ValueError("call get_auth_token() first")

        code = self.auth_d["code"]
        resp = self.session.get(
            f"https://linkup-be.mayohr.com/api/auth/checkticket?code={code}"
        )
        self.ticket_d = resp.json()
        return self.ticket_d

    def get_employee_role(self):
        resp = self.session.get("https://pt-be.mayohr.com/api/ModuleRoleEmployees")
        return resp.json()

    def get_sys_date(self):
        resp = self.session.get("https://pt-be.mayohr.com/api/common/sysDate")
        return resp.json()

    def get_authorized(self):
        resp = self.session.get(
            "https://linkup-be.mayohr.com/api/Authorization/GetAuthorized"
        )
        return resp.json()

    def punch(self, attendance_type: int, override: bool = False):
        """
        attendance_type:
            1 - 上班
            2 - 下班

        override: 蓋過前一次打卡紀錄（只有下班卡可以）
        """
        if not self.auth_d:
            raise ValueError("no login data")

        resp = self.session.post(
            "https://pt-be.mayohr.com/api/checkIn/punch/web",
            headers={
                "Functioncode": "PunchCard",
                "Actioncode": "Default",
            },
            json={
                "AttendanceType": attendance_type,
                "IsOverride": override,
            },
        )

        return resp.json()

    def punch_in(self, override: bool = False):
        return self.punch(1, override)

    def punch_out(self, override: bool = False):
        return self.punch(2, override)

    def dump_cookie_keys(self):
        keys = sorted(self.session.cookies.get_dict().keys())
        print(f"total {len(keys)} keys")
        print(", ".join(keys))
