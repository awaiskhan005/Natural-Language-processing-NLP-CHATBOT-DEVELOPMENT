# House Plan Generator

Generate architectural house plans in DXF format and 3D renderings using Blender.

## Features

- **3-Bedroom House Plan** (2000 sqft)
  - Master suite with walk-in closet and ensuite bathroom
  - Two additional bedrooms with closets
  - Open kitchen with island
  - Living room
  - Hall bathroom
  - Laundry/utility area

## Generated Files

### DXF Floor Plan
- `house_plan_3bed_2000sqft.dxf` - CAD-compatible floor plan

### 3D Blender Files
- `house_3d_model.blend` - Blender project file
- `house_3d_render.png` - Rendered 3D view

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# For 3D rendering, install Blender from:
# https://www.blender.org/download/
```

## Usage

### Generate DXF Floor Plan

```bash
python house_plan_dxf.py
```

### Generate 3D Render with Blender

```bash
# Run in Blender's Python environment
blender --background --python blender_3d_render.py

# Or open in Blender GUI
blender -P blender_3d_render.py
```

## House Specifications

| Area | Dimensions | Square Footage |
|------|------------|----------------|
| Living Room | 16' x 15' | 240 sqft |
| Kitchen/Dining | 18' x 15' | 270 sqft |
| Master Bedroom | 16' x 14' | 224 sqft |
| Bedroom 2 | 12' x 12' | 144 sqft |
| Bedroom 3 | 12' x 12' | 144 sqft |
| Master Bath | 10' x 6' | 60 sqft |
| Hall Bath | 10' x 8' | 80 sqft |
| **Total** | 50' x 40' | **~2000 sqft** |

## Floor Plan Layout

```
+------------------+----------------------------------+
|                  |                                  |
|  MASTER BEDROOM  |    BEDROOM 2    |   BEDROOM 3   |
|    16' x 14'     |    12' x 12'    |   12' x 12'   |
|                  |                 |               |
+--------+---------+-----------------+-------+-------+
| W.I.C. | MASTER  |                 |       |       |
|        | BATH    |                 | BATH  |LAUNDRY|
+--------+---------+-----------------+-------+-------+
|                  |                                  |
|   LIVING ROOM    |     OPEN KITCHEN / DINING       |
|    16' x 15'     |          18' x 15'              |
|                  |                                  |
+--------+---------+----------------------------------+
         ^
       ENTRY
```

## DXF Layers

| Layer | Color | Description |
|-------|-------|-------------|
| WALLS | White | Wall outlines |
| DOORS | Cyan | Door symbols |
| WINDOWS | Blue | Window symbols |
| DIMENSIONS | Green | Measurement annotations |
| TEXT | Yellow | Room labels |
| FURNITURE | Magenta | Furniture placement |
| FIXTURES | Red | Kitchen/bath fixtures |

## License

MIT License
