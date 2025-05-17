#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os

# 原始大 JSON 路径
INPUT_FILE = "SpatioScene/builder/data/MotionSample.json"
# 拆分后子文件存放目录
OUT_DIR = "SpatioScene/builder/data/sub_data"
os.makedirs(OUT_DIR, exist_ok=True)

with open(INPUT_FILE, encoding="utf-8") as f:
    records = json.load(f)

# 各实体列表
feature_values      = []
visual_features     = []
imu_features        = []
time_points         = []
relations           = []
spatio_temporals    = []
motion_samples      = []

for rec in records:
    sid = str(rec["id"])

    # —— 1) TimePoint ——
    raw_ts = rec.get("ts", "")
    ts_arr = (
        [s.strip() for s in raw_ts.split(",") if s.strip()]
        if isinstance(raw_ts, str)
        else raw_ts
    )
    if len(ts_arr) >= 14:
        tp_id = f"{sid}:ts"
        tp = {
            "id":        tp_id,
            "timestamp": float(ts_arr[0]),
            "dx":        float(ts_arr[1]),
            "dy":        float(ts_arr[2]),
            "h":         float(ts_arr[3]),
            "dh":        float(ts_arr[4]),
            "x":         float(ts_arr[5]),
            "dd":        float(ts_arr[6]),
            "dz":        float(ts_arr[7]),
            "dw":        float(ts_arr[8]),
            "d":         float(ts_arr[9]),
            "w":         float(ts_arr[10]),
            "z":         float(ts_arr[11]),
            "y":         float(ts_arr[12]),
            "dt":        float(ts_arr[13]),
        }
        time_points.append(tp)

    # —— 2) Relation ——
    raw_rel = rec.get("relationIds", "")
    rels = (
        [s.strip() for s in raw_rel.split(",") if s.strip()]
        if isinstance(raw_rel, str)
        else raw_rel
    )
    if len(rels) >= 5:
        rel_id = f"{sid}:rel"
        rel = {
            "id":          rel_id,
            "relationE":   int(rels[0]),
            "relationD":   int(rels[1]),
            "relationC":   int(rels[2]),
            "relationA":   int(rels[3]),
            "relationB":   int(rels[4]),
        }
        relations.append(rel)

    # —— 3) SpatioTemporalRelation ——
    raw_spa = rec.get("spatialIds", "")
    spas = (
        [s.strip() for s in raw_spa.split(",") if s.strip()]
        if isinstance(raw_spa, str)
        else raw_spa
    )
    if len(spas) >= 4:
        spa_id = f"{sid}:spa"
        spa = {
            "id":    spa_id,
            "tRel":  int(spas[0]),
            "zRel":  int(spas[1]),
            "yRel":  int(spas[2]),
            "xRel":  int(spas[3]),
        }
        spatio_temporals.append(spa)

    # —— 4) VisualFeature + FeatureValue ——
    raw_vis = rec.get("visualVec")
    if raw_vis:
        vals = (
            [s.strip() for s in raw_vis.split(",") if s.strip()]
            if isinstance(raw_vis, str)
            else raw_vis
        )
        fv_ids = []
        for idx, v in enumerate(vals):
            fv_id = f"{sid}:vis:fv:{idx}"
            feature_values.append({
                "id":            fv_id,
                "dimensionIdx":  idx,
                "featureValue":  float(v),
            })
            fv_ids.append(fv_id)
        visual_features.append({
            "id":      f"{sid}:vis",
            "feature": ",".join(fv_ids),
        })

    # —— 5) IMUFeature + FeatureValue ——
    raw_imu = rec.get("imuVec")
    if raw_imu:
        vals = (
            [s.strip() for s in raw_imu.split(",") if s.strip()]
            if isinstance(raw_imu, str)
            else raw_imu
        )
        fv_ids = []
        for idx, v in enumerate(vals):
            fv_id = f"{sid}:imu:fv:{idx}"
            feature_values.append({
                "id":            fv_id,
                "dimensionIdx":  idx,
                "featureValue":  float(v),
            })
            fv_ids.append(fv_id)
        imu_features.append({
            "id":      f"{sid}:imu",
            "feature": ",".join(fv_ids),
        })

    # —— 6) MotionSample ——
    ms = {
        "id":          sid,
        "classId":     rec.get("classId"),
        "ts":          f"{sid}:ts",
        "relationIds": f"{sid}:rel",
        "spatialIds":  f"{sid}:spa",
        "visualVec":   f"{sid}:vis",
        "imuVec":      f"{sid}:imu" if raw_imu else None,
    }
    motion_samples.append(ms)

# 写入 JSON
def dump(name, arr):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(arr)} items to {path}")

dump("FeatureValue.json",           feature_values)
dump("VisualFeature.json",          visual_features)
dump("IMUFeature.json",             imu_features)
dump("TimePoint.json",              time_points)
dump("Relation.json",               relations)
dump("SpatioTemporalRelation.json", spatio_temporals)
dump("MotionSample.json",           motion_samples)