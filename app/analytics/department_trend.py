"""MongoDB aggregation pipeline for daily department trends."""

from datetime import datetime, timedelta

from ..config import PRESENCE


def trend_pipeline(department: str, start: str, end: str):
    # Seed the date series from a department employee, so even a department with
    # no logs on any requested date still gets one row per day after densifying.
    return [
        {"$match": {"department": department}},
        {"$limit": 1},
        {"$project": {"_id": {"$dateFromString": {"dateString": start}}}},
        {
            "$densify": {
                "field": "_id",
                "range": {
                    "step": 1,
                    "unit": "day",
                    "bounds": [
                        datetime.fromisoformat(start),
                        datetime.fromisoformat(end) + timedelta(days=1),
                    ],
                },
            }
        },
        {
            "$set": {
                "date": {"$dateToString": {"date": "$_id", "format": "%Y-%m-%d"}},
                "is_working_day": {"$in": [{"$dayOfWeek": "$_id"}, [2, 3, 4, 5, 6]]},
            }
        },
        {
            "$lookup": {
                "from": "attendance_logs",
                "let": {"d": "$date"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$date", "$$d"]}}},
                    {
                        "$lookup": {
                            "from": "employees",
                            "localField": "emp_code",
                            "foreignField": "emp_code",
                            "as": "employee",
                        }
                    },
                    {"$unwind": "$employee"},
                    {"$match": {"employee.department": department}},
                    {
                        "$group": {
                            "_id": None,
                            "present_count": {
                                "$sum": {
                                    "$cond": [
                                        {"$in": ["$status", list(PRESENCE)]},
                                        {
                                            "$cond": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$ifNull": [
                                                                "$half_day",
                                                                False,
                                                            ]
                                                        },
                                                        True,
                                                    ]
                                                },
                                                0.5,
                                                1,
                                            ]
                                        },
                                        0,
                                    ]
                                }
                            },
                            "late_count": {
                                "$sum": {
                                    "$cond": [
                                        {"$gt": [{"$ifNull": ["$late_minutes", 0]}, 0]},
                                        1,
                                        0,
                                    ]
                                }
                            },
                        }
                    },
                ],
                "as": "daily",
            }
        },
        {
            "$set": {
                "present_count": {
                    "$ifNull": [{"$arrayElemAt": ["$daily.present_count", 0]}, 0]
                },
                "late_count": {
                    "$ifNull": [{"$arrayElemAt": ["$daily.late_count", 0]}, 0]
                },
            }
        },
        {
            "$lookup": {
                "from": "employees",
                "let": {"d": "$date"},
                "pipeline": [
                    {
                        "$match": {
                            "department": department,
                            "$expr": {"$lte": ["$joined_on", "$$d"]},
                        }
                    },
                    {"$count": "n"},
                ],
                "as": "hc",
            }
        },
        {"$set": {"headcount": {"$ifNull": [{"$arrayElemAt": ["$hc.n", 0]}, 0]}}},
        {
            "$set": {
                "attendance_rate": {
                    "$cond": [
                        {"$and": ["$is_working_day", {"$gt": ["$headcount", 0]}]},
                        {"$divide": ["$present_count", "$headcount"]},
                        None,
                    ]
                }
            }
        },
        {
            "$setWindowFields": {
                "sortBy": {"_id": 1},
                "output": {
                    "moving_avg_7d": {
                        "$avg": "$attendance_rate",
                        "window": {"documents": [-6, 0]},
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "date": 1,
                "is_working_day": 1,
                "headcount": 1,
                "present_count": 1,
                "late_count": 1,
                "attendance_rate": 1,
                "moving_avg_7d": 1,
            }
        },
        {"$sort": {"date": 1}},
    ]
