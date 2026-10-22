#!/usr/bin/env python3
"""WorldForge ROS 2 Training Dataset Generator. Generates deterministic, reproducible datasets."""
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import pyarrow as pa; import pyarrow.parquet as pq; HAS_PQ = True
except ImportError:
    HAS_PQ = False

REPO = Path(__file__).resolve().parents[2]
DD = REPO/"datasets"/"worldforge-ros-training"; SAMPLES=DD/"samples"; PACKS=DD/"packs"; MANIFEST=DD/"manifest.json"
SAMPLES.mkdir(parents=True,exist_ok=True); PACKS.mkdir(parents=True,exist_ok=True)

REGIONS = {
    "bay-area": {"worlds": [
        {"slug":"sf-downtown","name":"San Francisco Downtown","lat":37.7749,"lon":-122.4194},
        {"slug":"oakland-uptown","name":"Oakland Uptown","lat":37.8044,"lon":-122.2712},
        {"slug":"san-jose-santana-row","name":"San Jose Santana Row","lat":37.3230,"lon":-121.9470}],
        "robots":["spot","stretch","r1"]},
    "nola": {"worlds": [
        {"slug":"nola-french-quarter","name":"New Orleans French Quarter","lat":29.9584,"lon":-90.0644},
        {"slug":"nola-garden-district","name":"New Orleans Garden District","lat":29.9287,"lon":-90.0878}],
        "robots":["spot","r1"]},
    "dental": {"worlds": [
        {"slug":"unspoken-smiles","name":"Unspoken Smiles Dental Clinic","lat":37.7800,"lon":-122.4100}],
        "robots":["dental-arm"]},
}
TOPICS = {
    "spot":[("/spot/camera/front","sensor_msgs/msg/Image",15),("/spot/odometry","nav_msgs/msg/Odometry",50),("/spot/imu","sensor_msgs/msg/Imu",200),("/spot/joint_states","sensor_msgs/msg/JointState",100)],
    "stretch":[("/stretch/camera/head","sensor_msgs/msg/Image",15),("/stretch/odometry","nav_msgs/msg/Odometry",50),("/stretch/arm/joint_states","sensor_msgs/msg/JointState",100),("/stretch/gripper/force","geometry_msgs/msg/WrenchStamped",100)],
    "r1":[("/r1/camera/front","sensor_msgs/msg/Image",15),("/r1/lidar/scan","sensor_msgs/msg/LaserScan",10),("/r1/odometry","nav_msgs/msg/Odometry",50),("/r1/gps","sensor_msgs/msg/NavSatFix",5)],
    "dental-arm":[("/dental/camera/intraoral","sensor_msgs/msg/Image",30),("/dental/arm/joint_states","sensor_msgs/msg/JointState",200),("/dental/scaler/force","geometry_msgs/msg/WrenchStamped",500),("/dental/probe/depth","sensor_msgs/msg/FluidPressure",100),("/dental/tool/position","geometry_msgs/msg/PoseStamped",200)],
}
TYPES={"spot":"quadruped","stretch":"mobile-manipulator","r1":"delivery-robot","dental-arm":"dental-manipulator"}

class R:
    def __init__(s,seed): s.s=seed&0xFFFFFFFFFFFFFFFF or 1
    def n(s):
        x=s.s; x^=(x<<13)&0xFFFFFFFFFFFFFFFF; x^=(x>>7)&0xFFFFFFFFFFFFFFFF; x^=(x<<17)&0xFFFFFFFFFFFFFFFF; s.s=x; return x
    def f(s,lo,hi): return lo+(s.n()/0xFFFFFFFFFFFFFFFF)*(hi-lo)

def gen_msgs(rid,robot,world,dur=60):
    seed=int(hashlib.sha256(rid.encode()).hexdigest()[:16],16); rng=R(seed); msgs=[]; bt=1700000000.0
    for ti in range(dur*10):
        ts=bt+ti*0.1
        for topic,mt,rate in TOPICS[robot]:
            if ti%max(1,10//(rate//10))!=0: continue
            msgs.append(_m(mt,topic,ts,rng,world,robot))
    msgs.sort(key=lambda m:m.get("_t",0)); return msgs

def _m(mt,topic,ts,rng,w,rob):
    h={"header":{"stamp":{"sec":int(ts),"nanosec":int((ts%1)*1e9)},"frame_id":f"{rob}_base"}}
    if "Image" in mt: return {**h,"_t":ts,"_tp":topic,"height":480,"width":640,"encoding":"rgb8","data":"binary_truncated"}
    if "Odometry" in mt: return {**h,"_t":ts,"_tp":topic,"px":rng.f(-100,100),"py":rng.f(-100,100),"pz":rng.f(-1,3),"vx":rng.f(-1,1)}
    if "Imu" in mt: return {**h,"_t":ts,"_tp":topic,"ax":rng.f(-2,2),"ay":rng.f(-2,2),"az":rng.f(-2,2),"lx":rng.f(-10,10),"ly":rng.f(-10,10),"lz":rng.f(0,20)}
    if "JointState" in mt:
        nj=4 if "arm" in topic else 12
        return {**h,"_t":ts,"_tp":topic,"joints":[rng.f(-3.14,3.14) for _ in range(nj)]}
    if "Wrench" in mt: return {**h,"_t":ts,"_tp":topic,"fx":rng.f(-20,20),"fy":rng.f(-20,20),"fz":rng.f(-30,5),"tx":rng.f(-2,2),"ty":rng.f(-2,2),"tz":rng.f(-2,2)}
    if "LaserScan" in mt: return {**h,"_t":ts,"_tp":topic,"ranges_count":360,"range_min":0.1,"range_max":30.0}
    if "NavSat" in mt: return {**h,"_t":ts,"_tp":topic,"lat":w["lat"]+rng.f(-0.001,0.001),"lon":w["lon"]+rng.f(-0.001,0.001),"alt":rng.f(-5,50)}
    if "FluidPressure" in mt: return {**h,"_t":ts,"_tp":topic,"pressure":rng.f(50000,120000),"variance":100.0}
    if "PoseStamped" in mt: return {**h,"_t":ts,"_tp":topic,"px":rng.f(-0.5,0.5),"py":rng.f(-0.5,0.5),"pz":rng.f(0,0.3)}

def write_jsonl(msgs,path):
    with open(path,"w") as f:
        for m in msgs: f.write(json.dumps({k:v for k,v in m.items() if k!="_t"},default=str)+"\n")
    return path.stat().st_size

def write_pq(msgs,path):
    if not HAS_PQ or not msgs: return 0
    rows=[{"t":m.get("_t",0),"tp":m.get("_tp",""),"px":m.get("px",0.0),"py":m.get("py",0.0),"pz":m.get("pz",0.0)} for m in msgs]
    t=pa.table({"t":[r["t"] for r in rows],"tp":[r["tp"] for r in rows],"px":[r["px"] for r in rows],"py":[r["py"] for r in rows],"pz":[r["pz"] for r in rows]})
    pq.write_table(t,path); return path.stat().st_size

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(8192),b""): h.update(c)
    return h.hexdigest()

def _reg(slug):
    for r,d in REGIONS.items():
        for ww in d["worlds"]:
            if ww["slug"]==slug: return r
    return "unknown"

def gen_run(rid,robot,world,od,dur=60):
    od.mkdir(parents=True,exist_ok=True)
    print(f"  {rid} ({robot} @ {world['name']}, {dur}s)")
    msgs=gen_msgs(rid,robot,world,dur)
    jp=od/f"{rid}.jsonl"; js=write_jsonl(msgs,jp)
    pp=od/f"{rid}.parquet"; ps=write_pq(msgs,pp)
    meta={"run_id":rid,"robot":robot,"robot_type":TYPES.get(robot,""),"world":world["slug"],"world_name":world["name"],"lat":world["lat"],"lon":world["lon"],"duration_sec":dur,"message_count":len(msgs),"topics":[t[0] for t in TOPICS[robot]],"generated_at":datetime.now(timezone.utc).isoformat()}
    (od/f"{rid}.meta.json").write_text(json.dumps(meta,indent=2))
    return {"run_id":rid,"robot":robot,"world":world["slug"],"region":_reg(world["slug"]),"duration_sec":dur,"message_count":len(msgs),"jsonl_size":js,"parquet_size":ps,"sha256":sha(jp),"files":{"jsonl":f"{rid}.jsonl","parquet":f"{rid}.parquet","meta":f"{rid}.meta.json"}}

def gen_sample():
    print("=== FREE SAMPLE ==="); w=REGIONS["bay-area"]["worlds"][0]
    e=gen_run("sample-sf-downtown-spot-60s","spot",w,SAMPLES,60)
    e.update({"price_usd":0.0,"tier":"free","description":"Free sample: Spot, 60s SF Downtown"}); return e

def gen_dental():
    print("=== DENTAL PACK ==="); dd=PACKS/"dental"; dd.mkdir(parents=True,exist_ok=True)
    w=REGIONS["dental"]["worlds"][0]
    e=gen_run("dental-unspoken-smiles-cleaning-5min","dental-arm",w,dd,300)
    e.update({"price_usd":10.0,"tier":"premium","description":"Unspoken Smiles: scaler force, probe depth, tool position","tags":["dental","unspoken-smiles","force-feedback"]}); return e

def gen_region(region):
    print(f"=== REGION: {region} ==="); rd=REGIONS[region]; rdir=PACKS/region; rdir.mkdir(parents=True,exist_ok=True); entries=[]
    for w in rd["worlds"]:
        for rob in rd["robots"]:
            rid=f"{region}-{w['slug']}-{rob}-60s"
            e=gen_run(rid,rob,w,rdir,60); e.update({"price_usd":0.01,"tier":"standard","description":f"{rob} in {w['name']} (60s)"}); entries.append(e)
    return entries

def write_manifest(entries):
    m={"version":"1.0.0","generated_at":datetime.now(timezone.utc).isoformat(),"total_runs":len(entries),"total_size_bytes":sum(e.get("jsonl_size",0)+e.get("parquet_size",0) for e in entries),"pricing":{"free":{"price_usd":0.0},"standard":{"price_usd":0.01},"premium":{"price_usd":10.0}},"runs":entries}
    MANIFEST.write_text(json.dumps(m,indent=2))
    print(f"\nManifest: {MANIFEST} | {len(entries)} runs, {m['total_size_bytes']:,} bytes")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--region"); p.add_argument("--sample",action="store_true"); p.add_argument("--dental",action="store_true"); p.add_argument("--all",action="store_true")
    a=p.parse_args(); entries=[]
    if a.sample or a.all: entries.append(gen_sample())
    if a.dental or a.all: entries.append(gen_dental())
    if a.region: entries.extend(gen_region(a.region))
    elif a.all:
        for r in REGIONS:
            if r!="dental": entries.extend(gen_region(r))
    if not entries: print("Use --sample, --dental, --region <name>, or --all"); sys.exit(1)
    write_manifest(entries); print("Done.")

if __name__=="__main__": main()