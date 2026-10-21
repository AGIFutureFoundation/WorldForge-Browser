# WorldForge Earth

**41 agentic training worlds on real Earth maps.** Walkable 3-D worlds with satellite imagery, elevation data, OpenStreetMap buildings, robot digital twins, and union trade certification courses.

*Agents operate; people govern. Powered by AGI Corp. Owned by AGI Future Foundation PBC.*

## Live Site

🌍 **https://agifuturefoundation.github.io/WorldForge-Browser/earth/**

## Features

- **41 Worlds** on real Earth locations (London, New Orleans, Detroit, San Francisco, Boston, Houston, Austin, Seattle, Kennedy Space Center, etc.)
- **Real Maps**: Satellite imagery (Esri), elevation (AWS Terrain Tiles), OSM buildings, rivers, parks
- **Robot Training**: ROS 2-style tasks for 10 robot types (Boston Dynamics Spot, Unitree Go2, PAL TALOS, UR10e, Franka FR3, etc.)
- **Union Certifications**: 8 industry programs (UAW, Teamsters, IBEW, 1199SEIU, UFCW, Laborers) with 70-140 hour courses
- **AGI Robotics Language**: JSONL training schemas for robot simulation feedback
- **Quest System**: XP-based learning with checkpoints at each zone
- **Avatar Interactions**: Omega Stewards, Hermes messengers, Hive swarms, Coaches

## Industry Training Hubs

| City | Industry | Union | Hours | Robots |
|------|----------|-------|-------|--------|
| Detroit | Automotive Manufacturing | UAW/IAM | 120h | UR10e, Franka, Fetch |
| Memphis | Logistics & Warehousing | Teamsters/ILWU | 80h | Husky, Fetch, Spot |
| Miami | Construction & Infrastructure | Laborers/Ironworkers | 100h | Spot, Go2, Crazyflie |
| Boston | Healthcare & Biotech | 1199SEIU | 90h | Franka, Kinova, NAO |
| Central Valley | Agriculture & Food | UFCW | 70h | Husky, Go2, Crazyflie |
| Houston | Clean Energy | IBEW | 110h | Spot, Crazyflie, Husky |
| Austin | Electronics & Semiconductors | IBEW/IUE-CWA | 130h | Franka, Kinova, Fetch |
| Seattle | Aerospace & Defense | IAM/UAW Aerospace | 140h | UR10e, Franka, Spot |

## Run Locally

```bash
# Serve the site
python3 -m http.server 8094 --directory site

# Open in browser
open http://127.0.0.1:8094/earth/

# Visit a specific world
open http://127.0.0.1:8094/earth/world.html?world=climate-dao
```

## Build Industry Training

```bash
# Generate robot tasks, union certifications, and world designs for 8 industry cities
python3 /path/to/build_industry.py
```

## Pages Deployment

Automatic deployment via GitHub Actions:
- Push to `main` triggers `.github/workflows/pages.yml`
- Site deploys to https://agifuturefoundation.github.io/WorldForge-Browser/
- Earth worlds at https://agifuturefoundation.github.io/WorldForge-Browser/earth/

## Related Repositories

- **SmartCiti.X**: Trade Craft Academy — https://github.com/AGIFutureFoundation/SmartCiti.X
- **Metropolis-SmartCiti**: Onchain agent layer on Monad — https://github.com/AGIFutureFoundation/Metropolis-SmartCiti