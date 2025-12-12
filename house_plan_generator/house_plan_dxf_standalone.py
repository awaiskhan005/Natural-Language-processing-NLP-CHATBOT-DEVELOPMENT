#!/usr/bin/env python3
"""
Standalone House Plan DXF Generator
Creates a 3-bedroom, 2000 sqft house plan with open kitchen and master suite
No external dependencies required - writes DXF format directly
"""

import math
import os


class DXFWriter:
    """Simple DXF file writer - no external dependencies"""

    def __init__(self):
        self.entities = []
        self.handle_counter = 100

    def _next_handle(self):
        """Generate next entity handle"""
        self.handle_counter += 1
        return hex(self.handle_counter)[2:].upper()

    def add_line(self, x1, y1, x2, y2, layer='0', color=256):
        """Add a line entity"""
        self.entities.append(f"""  0
LINE
  5
{self._next_handle()}
  8
{layer}
 62
{color}
 10
{x1}
 20
{y1}
 30
0.0
 11
{x2}
 21
{y2}
 31
0.0""")

    def add_circle(self, cx, cy, radius, layer='0', color=256):
        """Add a circle entity"""
        self.entities.append(f"""  0
CIRCLE
  5
{self._next_handle()}
  8
{layer}
 62
{color}
 10
{cx}
 20
{cy}
 30
0.0
 40
{radius}""")

    def add_arc(self, cx, cy, radius, start_angle, end_angle, layer='0', color=256):
        """Add an arc entity"""
        self.entities.append(f"""  0
ARC
  5
{self._next_handle()}
  8
{layer}
 62
{color}
 10
{cx}
 20
{cy}
 30
0.0
 40
{radius}
 50
{start_angle}
 51
{end_angle}""")

    def add_text(self, x, y, text, height=0.5, layer='0', color=256):
        """Add a text entity"""
        self.entities.append(f"""  0
TEXT
  5
{self._next_handle()}
  8
{layer}
 62
{color}
 10
{x}
 20
{y}
 30
0.0
 40
{height}
  1
{text}
 72
1
 11
{x}
 21
{y}
 31
0.0""")

    def add_rectangle(self, x, y, width, height, layer='0', color=256):
        """Add a rectangle using lines"""
        self.add_line(x, y, x + width, y, layer, color)
        self.add_line(x + width, y, x + width, y + height, layer, color)
        self.add_line(x + width, y + height, x, y + height, layer, color)
        self.add_line(x, y + height, x, y, layer, color)

    def save(self, filename):
        """Save to DXF file"""
        # DXF Header
        header = """  0
SECTION
  2
HEADER
  9
$ACADVER
  1
AC1015
  9
$INSBASE
 10
0.0
 20
0.0
 30
0.0
  9
$EXTMIN
 10
-10.0
 20
-15.0
 30
0.0
  9
$EXTMAX
 10
60.0
 20
50.0
 30
0.0
  0
ENDSEC"""

        # Tables section with layers
        tables = """  0
SECTION
  2
TABLES
  0
TABLE
  2
LAYER
 70
7
  0
LAYER
  2
0
 70
0
 62
7
  6
CONTINUOUS
  0
LAYER
  2
WALLS
 70
0
 62
7
  6
CONTINUOUS
  0
LAYER
  2
DOORS
 70
0
 62
4
  6
CONTINUOUS
  0
LAYER
  2
WINDOWS
 70
0
 62
5
  6
CONTINUOUS
  0
LAYER
  2
DIMENSIONS
 70
0
 62
3
  6
CONTINUOUS
  0
LAYER
  2
TEXT
 70
0
 62
2
  6
CONTINUOUS
  0
LAYER
  2
FIXTURES
 70
0
 62
1
  6
CONTINUOUS
  0
ENDTAB
  0
ENDSEC"""

        # Entities section
        entities_section = """  0
SECTION
  2
ENTITIES
""" + "\n".join(self.entities) + """
  0
ENDSEC"""

        # End of file
        eof = """  0
EOF"""

        # Write complete file
        with open(filename, 'w') as f:
            f.write(header + "\n")
            f.write(tables + "\n")
            f.write(entities_section + "\n")
            f.write(eof)

        print(f"DXF file saved: {filename}")
        return filename


class HousePlanGenerator:
    """Generates architectural floor plans in DXF format"""

    def __init__(self, total_sqft=2000, scale=1.0):
        self.total_sqft = total_sqft
        self.scale = scale
        self.dxf = DXFWriter()

        # House dimensions: 50' x 40' = 2000 sqft
        self.width = 50 * scale
        self.height = 40 * scale

    def draw_door(self, x, y, width, swing_direction='right'):
        """Draw a door symbol with swing arc"""
        self.dxf.add_line(x, y, x + width, y, 'DOORS', 4)

        if swing_direction == 'right':
            self.dxf.add_arc(x, y, width, 0, 90, 'DOORS', 4)
            self.dxf.add_line(x, y, x, y + width, 'DOORS', 4)
        else:
            self.dxf.add_arc(x + width, y, width, 90, 180, 'DOORS', 4)
            self.dxf.add_line(x + width, y, x + width, y + width, 'DOORS', 4)

    def draw_window(self, x, y, width):
        """Draw a window symbol"""
        self.dxf.add_line(x, y - 0.25, x, y + 0.25, 'WINDOWS', 5)
        self.dxf.add_line(x + width, y - 0.25, x + width, y + 0.25, 'WINDOWS', 5)
        self.dxf.add_line(x, y, x + width, y, 'WINDOWS', 5)
        self.dxf.add_line(x, y - 0.15, x + width, y - 0.15, 'WINDOWS', 5)
        self.dxf.add_line(x, y + 0.15, x + width, y + 0.15, 'WINDOWS', 5)

    def draw_kitchen_fixtures(self, x, y):
        """Draw kitchen fixtures"""
        # Kitchen island
        self.dxf.add_rectangle(x + 2, y + 5, 8, 3, 'FIXTURES', 1)
        self.dxf.add_text(x + 6, y + 6.5, "ISLAND", 0.35, 'TEXT', 2)

        # Sink
        self.dxf.add_rectangle(x + 1, y + 11, 3, 2, 'FIXTURES', 1)
        self.dxf.add_circle(x + 2.5, y + 12, 0.5, 'FIXTURES', 1)
        self.dxf.add_text(x + 2.5, y + 10.5, "SINK", 0.3, 'TEXT', 2)

        # Stove/Range
        self.dxf.add_rectangle(x + 5, y + 11, 3, 2, 'FIXTURES', 1)
        self.dxf.add_text(x + 6.5, y + 12, "RANGE", 0.3, 'TEXT', 2)

        # Refrigerator
        self.dxf.add_rectangle(x + 9, y + 11, 3, 2.5, 'FIXTURES', 1)
        self.dxf.add_text(x + 10.5, y + 12.25, "REFRIG", 0.3, 'TEXT', 2)

    def draw_bathroom_fixtures(self, x, y, is_master=False):
        """Draw bathroom fixtures"""
        # Toilet
        self.dxf.add_rectangle(x + 0.5, y + 0.5, 1.5, 2.5, 'FIXTURES', 1)
        self.dxf.add_circle(x + 1.25, y + 2, 0.5, 'FIXTURES', 1)

        if is_master:
            # Double vanity
            self.dxf.add_rectangle(x + 3, y + 0.5, 5, 2, 'FIXTURES', 1)
            self.dxf.add_circle(x + 4.5, y + 1.5, 0.4, 'FIXTURES', 1)
            self.dxf.add_circle(x + 6.5, y + 1.5, 0.4, 'FIXTURES', 1)
            # Walk-in shower
            self.dxf.add_rectangle(x + 9, y + 0.5, 4, 4, 'FIXTURES', 1)
            self.dxf.add_text(x + 11, y + 2.5, "SHOWER", 0.3, 'TEXT', 2)
        else:
            # Single vanity
            self.dxf.add_rectangle(x + 3, y + 0.5, 2.5, 1.5, 'FIXTURES', 1)
            self.dxf.add_circle(x + 4.25, y + 1.25, 0.4, 'FIXTURES', 1)
            # Tub
            self.dxf.add_rectangle(x + 0.5, y + 4, 2.5, 5, 'FIXTURES', 1)
            self.dxf.add_text(x + 1.75, y + 6.5, "TUB", 0.3, 'TEXT', 2)

    def add_dimension(self, x1, y1, x2, y2, offset=2):
        """Add dimension line"""
        if abs(y2 - y1) < 0.01:  # Horizontal
            dim_y = y1 + offset
            self.dxf.add_line(x1, y1, x1, dim_y, 'DIMENSIONS', 3)
            self.dxf.add_line(x2, y2, x2, dim_y, 'DIMENSIONS', 3)
            self.dxf.add_line(x1, dim_y, x2, dim_y, 'DIMENSIONS', 3)
            self.dxf.add_text((x1 + x2) / 2, dim_y + 0.5, f"{abs(x2-x1):.0f}'", 0.4, 'DIMENSIONS', 3)
        else:  # Vertical
            dim_x = x1 + offset
            self.dxf.add_line(x1, y1, dim_x, y1, 'DIMENSIONS', 3)
            self.dxf.add_line(x2, y2, dim_x, y2, 'DIMENSIONS', 3)
            self.dxf.add_line(dim_x, y1, dim_x, y2, 'DIMENSIONS', 3)
            self.dxf.add_text(dim_x + 0.5, (y1 + y2) / 2, f"{abs(y2-y1):.0f}'", 0.4, 'DIMENSIONS', 3)

    def generate_floor_plan(self):
        """Generate the complete 3-bedroom house floor plan"""

        # ============================================
        # EXTERIOR WALLS (50' x 40' = 2000 sqft)
        # ============================================
        self.dxf.add_rectangle(0, 0, 50, 40, 'WALLS', 7)

        # ============================================
        # LIVING ROOM (Front left: 16' x 15')
        # ============================================
        self.dxf.add_line(0, 15, 16, 15, 'WALLS', 7)
        self.dxf.add_text(8, 7.5, "LIVING ROOM", 0.6, 'TEXT', 2)
        self.dxf.add_text(8, 6, "16' x 15'", 0.4, 'TEXT', 2)
        self.dxf.add_text(8, 4.5, "240 sqft", 0.35, 'TEXT', 2)
        self.draw_window(4, 0, 8)

        # ============================================
        # OPEN KITCHEN/DINING (Front right: 18' x 15')
        # ============================================
        self.dxf.add_line(16, 0, 16, 10, 'WALLS', 7)
        self.dxf.add_text(34, 7.5, "KITCHEN", 0.6, 'TEXT', 2)
        self.dxf.add_text(34, 6, "18' x 15'", 0.4, 'TEXT', 2)
        self.dxf.add_text(34, 4.5, "270 sqft", 0.35, 'TEXT', 2)
        self.draw_kitchen_fixtures(25, 0)
        self.draw_window(38, 0, 6)
        self.dxf.add_text(22, 12, "DINING", 0.5, 'TEXT', 2)
        self.dxf.add_text(22, 10.5, "AREA", 0.5, 'TEXT', 2)

        # ============================================
        # HALLWAY / CORRIDOR
        # ============================================
        self.dxf.add_line(16, 15, 16, 40, 'WALLS', 7)
        self.dxf.add_line(16, 15, 50, 15, 'WALLS', 7)

        # ============================================
        # MASTER SUITE (Back left: 16' x 14')
        # ============================================
        self.dxf.add_line(0, 26, 16, 26, 'WALLS', 7)
        self.dxf.add_text(8, 33, "MASTER BEDROOM", 0.5, 'TEXT', 2)
        self.dxf.add_text(8, 31.5, "16' x 14'", 0.4, 'TEXT', 2)
        self.dxf.add_text(8, 30, "224 sqft", 0.35, 'TEXT', 2)
        self.draw_window(3, 40, 5)
        self.draw_window(10, 40, 5)

        # Master closet (walk-in: 6' x 5')
        self.dxf.add_line(0, 21, 6, 21, 'WALLS', 7)
        self.dxf.add_line(6, 21, 6, 26, 'WALLS', 7)
        self.dxf.add_text(3, 23.5, "W.I.C.", 0.35, 'TEXT', 2)
        self.draw_door(6, 23, 2.5, 'left')

        # Master bathroom (10' x 6')
        self.dxf.add_line(6, 21, 16, 21, 'WALLS', 7)
        self.dxf.add_text(11, 18, "MASTER BATH", 0.4, 'TEXT', 2)
        self.dxf.add_text(11, 16.5, "10' x 6'", 0.35, 'TEXT', 2)
        self.draw_bathroom_fixtures(6, 15, is_master=True)
        self.draw_door(7, 21, 2.5, 'right')
        self.draw_door(13, 26, 3, 'left')

        # ============================================
        # BEDROOM 2 (Back center: 12' x 12')
        # ============================================
        self.dxf.add_line(16, 28, 28, 28, 'WALLS', 7)
        self.dxf.add_line(28, 28, 28, 40, 'WALLS', 7)
        self.dxf.add_text(22, 34, "BEDROOM 2", 0.5, 'TEXT', 2)
        self.dxf.add_text(22, 32.5, "12' x 12'", 0.4, 'TEXT', 2)
        self.dxf.add_text(22, 31, "144 sqft", 0.35, 'TEXT', 2)
        self.draw_window(19, 40, 6)

        # Bedroom 2 closet
        self.dxf.add_line(16, 28, 16, 33, 'WALLS', 7)
        self.dxf.add_line(16, 33, 20, 33, 'WALLS', 7)
        self.dxf.add_line(20, 33, 20, 28, 'WALLS', 7)
        self.dxf.add_text(18, 30.5, "CL", 0.3, 'TEXT', 2)
        self.draw_door(22, 28, 2.5, 'left')

        # ============================================
        # BEDROOM 3 (Back right: 12' x 12')
        # ============================================
        self.dxf.add_line(28, 28, 40, 28, 'WALLS', 7)
        self.dxf.add_line(40, 28, 40, 40, 'WALLS', 7)
        self.dxf.add_text(34, 34, "BEDROOM 3", 0.5, 'TEXT', 2)
        self.dxf.add_text(34, 32.5, "12' x 12'", 0.4, 'TEXT', 2)
        self.dxf.add_text(34, 31, "144 sqft", 0.35, 'TEXT', 2)
        self.draw_window(31, 40, 6)

        # Bedroom 3 closet
        self.dxf.add_line(28, 28, 28, 33, 'WALLS', 7)
        self.dxf.add_line(28, 33, 32, 33, 'WALLS', 7)
        self.dxf.add_line(32, 33, 32, 28, 'WALLS', 7)
        self.dxf.add_text(30, 30.5, "CL", 0.3, 'TEXT', 2)
        self.draw_door(34, 28, 2.5, 'left')

        # ============================================
        # HALL BATHROOM (10' x 8')
        # ============================================
        self.dxf.add_line(40, 15, 40, 28, 'WALLS', 7)
        self.dxf.add_line(40, 20, 50, 20, 'WALLS', 7)
        self.dxf.add_text(45, 24, "BATHROOM", 0.4, 'TEXT', 2)
        self.dxf.add_text(45, 22.5, "10' x 8'", 0.35, 'TEXT', 2)
        self.draw_bathroom_fixtures(40, 20, is_master=False)
        self.draw_door(42, 20, 2.5, 'left')

        # ============================================
        # LAUNDRY/UTILITY (10' x 5')
        # ============================================
        self.dxf.add_text(45, 17.5, "LAUNDRY", 0.4, 'TEXT', 2)
        self.dxf.add_text(45, 16, "10' x 5'", 0.35, 'TEXT', 2)
        self.dxf.add_rectangle(41, 15.5, 3, 2.5, 'FIXTURES', 1)
        self.dxf.add_rectangle(45, 15.5, 3, 2.5, 'FIXTURES', 1)

        # Side window
        self.draw_window(50, 30, 6)

        # Entry door
        self.draw_door(16, 0, 3, 'right')
        self.dxf.add_text(17.5, -1.5, "ENTRY", 0.4, 'TEXT', 2)

        # ============================================
        # DIMENSIONS
        # ============================================
        self.add_dimension(0, 0, 50, 0, -3)
        self.add_dimension(0, 0, 0, 40, -3)

        # ============================================
        # TITLE BLOCK
        # ============================================
        self.dxf.add_text(25, -6, "3-BEDROOM HOUSE PLAN", 1.0, 'TEXT', 2)
        self.dxf.add_text(25, -8, "2000 SQFT - OPEN KITCHEN - MASTER SUITE", 0.5, 'TEXT', 2)
        self.dxf.add_text(25, -9.5, "SCALE: 1\" = 10'", 0.4, 'TEXT', 2)

        return self

    def save(self, filename):
        """Save the DXF file"""
        return self.dxf.save(filename)


def main():
    """Generate the house plan DXF file"""
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "house_plan_3bed_2000sqft.dxf")

    generator = HousePlanGenerator(total_sqft=2000)
    generator.generate_floor_plan()
    generator.save(output_file)

    print("\n" + "="*50)
    print("HOUSE PLAN GENERATED SUCCESSFULLY")
    print("="*50)
    print(f"\nSpecifications:")
    print(f"  - Total Area: 2000 sqft (50' x 40')")
    print(f"  - Bedrooms: 3")
    print(f"  - Bathrooms: 2 (Master + Hall)")
    print(f"  - Features:")
    print(f"    * Open kitchen with island")
    print(f"    * Master suite with walk-in closet")
    print(f"    * Master bathroom with double vanity and walk-in shower")
    print(f"    * Laundry/utility area")
    print(f"\nOutput file: {output_file}")

    return output_file


if __name__ == "__main__":
    main()
