import bisect
import numpy as np
from ..analysis.generate_report import RequestLevelReport

if __name__ == "__main__":
    import pickle
    import json

    ids = [
        ("32a4dfc8-f930-42ee-bd47-2548f7854418", 10, 40, None),
        ("4bb45905-bcd6-4c26-b76d-eef7fc399252", None, None, None),
        ("424d1e15-73ec-48bc-9baf-2a34f3d49904", None, None, None),
        ("36d0f992-210d-4d01-8f08-e086ab79a6ee", None, None, None),
        ("78977d32-3719-4a29-9aab-45c03c867842", 8, 20, None),
        ("a44f266f-1bd6-46b8-81ef-8debb3d73a51", None, None, None),
        ("3c26d44c-5773-4dbe-aabb-a497c02652ee", None, None, None),
        ("ae5ea044-3a02-4bf1-ae73-870cc8c57ec9", None, None, None),
        ("dc979ea3-6c3d-499c-8c92-f19f85ec3652", None, None, None),
        ("e1d9c841-bd89-4283-9c5f-722be5a6b5b2", 3, 10, None),
        ("6b488517-970a-4786-88f6-21dbe32c12e4", None, None, None),
        ("ee4b8dad-143f-4832-9452-a438ba50ff05", None, None, None),
        ("f9619a54-cddb-42a1-879d-978ffa63c7ef", None, None, None),
        ("c120dce0-daba-4955-a8a3-c12f79395770", None, None, None),
        ("dbe2a8f3-4f86-43d2-9f1c-6058f273f275", None, None, (0.3, 0.8)),
        ("3ed00ae1-a545-4f3d-ae2e-9f2e6a17b410", None, None, (0.3, 0.8)),
        ("51727804-8838-456e-8264-cdb4be8e1e12", None, None, (0.3, 0.8)),
        ("30e5efbe-7fe2-4a21-82e6-b1e73c5a8492", None, None, (0.3, 0.8)),
        ("45f977fa-ba07-4e95-ac66-cc231a86fcfc", None, None, (0.3, 0.8)),
    ]
    export_data = []
    for id, sample_start, offset, percent_range in ids:
        path = f"tmp/raw_report_{id}.pkl"
        raw_data: RequestLevelReport = pickle.load(open(path, "rb"))
        tracking = [(p[0]-raw_data.token_timestamp[0][0],p[1])for p in raw_data.token_timestamp]
        start = tracking[0][0]
        end = tracking[-1][0]
        time_step = 1
        window_size = 5
        x = np.arange(0, end - start, time_step)
        y = np.zeros(len(x))
        for i in range(len(y)):
            ty = start + i * time_step
            y[i] = bisect.bisect_right(
                tracking, ty + window_size / 2, key=lambda x: x[0]
            ) - bisect.bisect_left(tracking, ty - window_size / 2, key=lambda x: x[0])
        y = y / window_size
        max_time, max_tps = x[np.argmax(y)], np.max(y)
        if sample_start is None:
            sample_start = max_time
        if offset is None:
            offset = 60
        sample_end = sample_start + offset
        if percent_range is not None:
            sample_start = start + (end - start) * percent_range[0]
            sample_end = start + (end - start) * percent_range[1]
        avg_token = sum([p[1] for p in tracking if p[0]>= sample_start and p[0] < sample_end])/(sample_end-sample_start)
        export_data.append({
            "id": id,
            "max_time": max_time,
            "max_tps": max_tps,
            "avg_token": avg_token
        })
    json.dump(export_data, open(f"export/tps_tracking.json", "w"))
