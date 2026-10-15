"""MongoDB aggregation pipelines for per-employee monthly summaries."""

from ..config import PRESENCE
from .common import month_bounds


def employee_month_pipeline(emp_code: str, month: str):
    start, end, last = month_bounds(month)
    return [
        {"$match": {"emp_code": emp_code, "date": {"$gte": start, "$lte": end}}},
        {
            "$addFields": {
                "_weekday": {"$dayOfWeek": {"$dateFromString": {"dateString": "$date"}}}
            }
        },
        {
            "$group": {
                "_id": None,
                "present_days": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$in": ["$status", list(PRESENCE)]},
                                    {"$in": ["$_weekday", [2, 3, 4, 5, 6]]},
                                ]
                            },
                            {
                                "$cond": [
                                    {"$eq": [{"$ifNull": ["$half_day", False]}, True]},
                                    0.5,
                                    1,
                                ]
                            },
                            0,
                        ]
                    }
                },
                "leave_days": {
                    "$sum": {"$cond": [{"$eq": ["$status", "LEAVE"]}, 1, 0]}
                },
                "late_count": {
                    "$sum": {
                        "$cond": [{"$gt": [{"$ifNull": ["$late_minutes", 0]}, 0]}, 1, 0]
                    }
                },
                "total_late_minutes": {"$sum": {"$ifNull": ["$late_minutes", 0]}},
                "total_overtime_minutes": {
                    "$sum": {"$ifNull": ["$overtime_minutes", 0]}
                },
            }
        },
    ]


def employee_working_days_pipeline(emp_code: str, month: str):
    start, end, _ = month_bounds(month)
    start_date = {"$dateFromString": {"dateString": "$effective_start"}}
    end_date = {"$dateFromString": {"dateString": end}}
    count = {
        "$cond": [
            {"$lte": [start_date, end_date]},
            {
                "$add": [
                    {
                        "$dateDiff": {
                            "startDate": start_date,
                            "endDate": end_date,
                            "unit": "day",
                        }
                    },
                    1,
                ]
            },
            0,
        ]
    }
    return [
        {"$match": {"emp_code": emp_code}},
        {
            "$project": {
                "effective_start": {
                    "$cond": [{"$gt": ["$joined_on", start]}, "$joined_on", start]
                }
            }
        },
        {
            "$project": {
                "days": {
                    "$map": {
                        "input": {"$range": [0, count]},
                        "as": "offset",
                        "in": {
                            "$dateAdd": {
                                "startDate": start_date,
                                "unit": "day",
                                "amount": "$$offset",
                            }
                        },
                    }
                }
            }
        },
        {
            "$project": {
                "working_days": {
                    "$size": {
                        "$filter": {
                            "input": "$days",
                            "as": "day",
                            "cond": {"$in": [{"$dayOfWeek": "$$day"}, [2, 3, 4, 5, 6]]},
                        }
                    }
                }
            }
        },
    ]
