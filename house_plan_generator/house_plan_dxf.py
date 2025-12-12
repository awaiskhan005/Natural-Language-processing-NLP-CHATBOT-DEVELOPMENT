#!/usr/bin/env python3
"""
House Plan DXF Generator
Creates a 3-bedroom, 2000 sqft house plan with open kitchen and master suite
Outputs as DXF file for CAD software compatibility
"""

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
import math
import os


class HousePlanGenerator:
    """Generates architectural floor plans in DXF format"""

    def __init__(self, total_sqft=2000, scale=1.0):
        """
        Initialize the house plan generator

        Args:
            total_sqft: Target square footage for the house
            scale: Drawing scale factor (1 unit = 1 foot)
        """
        self.total_sqft = total_sqft
        self.scale = scale
        self.doc = ezdxf.new('R2010')
        self.msp = self.doc.modelspace()

        # Define layers for different elements
        self._setup_layers()

        # Calculate optimal dimensions for 2000 sqft
        # Using a rectangular layout approximately 50' x 40'
        self.width = 50 * scale  # 50 feet wide
        self.height = 40 * scale  # 40 feet deep

        # Room dimensions (all in feet, scaled)
        self.wall_thickness = 0.5 * scale

    def _setup_layers(self):
        """Setup DXF layers for different architectural elements"""
        layers = [
            ('WALLS', colors.WHITE),
            ('DOORS', colors.CYAN),
            ('WINDOWS', colors.BLUE),
            ('DIMENSIONS', colors.GREEN),
            ('TEXT', colors.YELLOW),
            ('FURNITURE', colors.MAGENTA),
            ('FIXTURES', colors.RED),
        ]

        for layer_name, color in layers:
            self.doc.layers.add(layer_name, color=color)

    def draw_rectangle(self, x, y, width, height, layer='WALLS'):
        """Draw a rectangle at specified position"""
        points = [
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height),
            (x, y)
        ]
        self.msp.add_lwpolyline(points, dxfattribs={'layer': layer})

    def draw_wall(self, x1, y1, x2, y2, thickness=None, layer='WALLS'):
        """Draw a wall segment with thickness"""
        if thickness is None:
            thickness = self.wall_thickness

        # Calculate perpendicular offset for wall thickness
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)

        if length > 0:
            # Normalized perpendicular vector
            px = -dy / length * thickness / 2
            py = dx / length * thickness / 2

            # Create wall as closed polyline
            points = [
                (x1 + px, y1 + py),
                (x2 + px, y2 + py),
                (x2 - px, y2 - py),
                (x1 - px, y1 - py),
                (x1 + px, y1 + py)
            ]
            self.msp.add_lwpolyline(points, dxfattribs={'layer': layer})

    def draw_door(self, x, y, width, swing_direction='right', layer='DOORS'):
        """Draw a door symbol with swing arc"""
        # Door opening
        self.msp.add_line((x, y), (x + width, y), dxfattribs={'layer': layer})

        # Door swing arc
        if swing_direction == 'right':
            self.msp.add_arc(
                center=(x, y),
                radius=width,
                start_angle=0,
                end_angle=90,
                dxfattribs={'layer': layer}
            )
            # Door panel line
            self.msp.add_line((x, y), (x, y + width), dxfattribs={'layer': layer})
        else:
            self.msp.add_arc(
                center=(x + width, y),
                radius=width,
                start_angle=90,
                end_angle=180,
                dxfattribs={'layer': layer}
            )
            self.msp.add_line((x + width, y), (x + width, y + width), dxfattribs={'layer': layer})

    def draw_window(self, x, y, width, layer='WINDOWS'):
        """Draw a window symbol"""
        # Window frame
        self.msp.add_line((x, y - 0.25), (x, y + 0.25), dxfattribs={'layer': layer})
        self.msp.add_line((x + width, y - 0.25), (x + width, y + 0.25), dxfattribs={'layer': layer})
        self.msp.add_line((x, y), (x + width, y), dxfattribs={'layer': layer})
        # Window panes
        self.msp.add_line((x, y - 0.15), (x + width, y - 0.15), dxfattribs={'layer': layer})
        self.msp.add_line((x, y + 0.15), (x + width, y + 0.15), dxfattribs={'layer': layer})

    def add_text(self, x, y, text, height=0.5, layer='TEXT'):
        """Add text annotation"""
        self.msp.add_text(
            text,
            dxfattribs={
                'layer': layer,
                'height': height,
                'style': 'Standard'
            }
        ).set_placement((x, y), align=TextEntityAlignment.CENTER)

    def add_dimension(self, x1, y1, x2, y2, offset=2, layer='DIMENSIONS'):
        """Add a linear dimension"""
        # Calculate dimension location
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)

        # Simple dimension line
        if abs(dy) < 0.01:  # Horizontal
            dim_y = y1 + offset
            self.msp.add_line((x1, y1), (x1, dim_y), dxfattribs={'layer': layer})
            self.msp.add_line((x2, y2), (x2, dim_y), dxfattribs={'layer': layer})
            self.msp.add_line((x1, dim_y), (x2, dim_y), dxfattribs={'layer': layer})
            self.add_text((x1 + x2) / 2, dim_y + 0.5, f"{abs(x2-x1):.0f}'", 0.4, layer)
        else:  # Vertical
            dim_x = x1 + offset
            self.msp.add_line((x1, y1), (dim_x, y1), dxfattribs={'layer': layer})
            self.msp.add_line((x2, y2), (dim_x, y2), dxfattribs={'layer': layer})
            self.msp.add_line((dim_x, y1), (dim_x, y2), dxfattribs={'layer': layer})
            self.add_text(dim_x + 0.5, (y1 + y2) / 2, f"{abs(y2-y1):.0f}'", 0.4, layer)

    def draw_kitchen_fixtures(self, x, y):
        """Draw kitchen fixtures (sink, stove, refrigerator)"""
        # Kitchen island/counter
        self.draw_rectangle(x + 2, y + 5, 8, 3, 'FIXTURES')
        self.add_text(x + 6, y + 6.5, "ISLAND", 0.35, 'TEXT')

        # Sink
        self.draw_rectangle(x + 1, y + 11, 3, 2, 'FIXTURES')
        self.msp.add_circle((x + 2.5, y + 12), 0.5, dxfattribs={'layer': 'FIXTURES'})
        self.add_text(x + 2.5, y + 10.5, "SINK", 0.3, 'TEXT')

        # Stove/Range
        self.draw_rectangle(x + 5, y + 11, 3, 2, 'FIXTURES')
        self.add_text(x + 6.5, y + 12, "RANGE", 0.3, 'TEXT')

        # Refrigerator
        self.draw_rectangle(x + 9, y + 11, 3, 2.5, 'FIXTURES')
        self.add_text(x + 10.5, y + 12.25, "REFRIG", 0.3, 'TEXT')

    def draw_bathroom_fixtures(self, x, y, is_master=False):
        """Draw bathroom fixtures"""
        # Toilet
        self.draw_rectangle(x + 0.5, y + 0.5, 1.5, 2.5, 'FIXTURES')
        self.msp.add_circle((x + 1.25, y + 2), 0.5, dxfattribs={'layer': 'FIXTURES'})

        # Sink/Vanity
        if is_master:
            # Double vanity for master
            self.draw_rectangle(x + 3, y + 0.5, 5, 2, 'FIXTURES')
            self.msp.add_circle((x + 4.5, y + 1.5), 0.4, dxfattribs={'layer': 'FIXTURES'})
            self.msp.add_circle((x + 6.5, y + 1.5), 0.4, dxfattribs={'layer': 'FIXTURES'})
        else:
            # Single vanity
            self.draw_rectangle(x + 3, y + 0.5, 2.5, 1.5, 'FIXTURES')
            self.msp.add_circle((x + 4.25, y + 1.25), 0.4, dxfattribs={'layer': 'FIXTURES'})

        # Shower/Tub
        if is_master:
            # Walk-in shower
            self.draw_rectangle(x + 9, y + 0.5, 4, 4, 'FIXTURES')
            self.add_text(x + 11, y + 2.5, "SHOWER", 0.3, 'TEXT')
        else:
            # Tub/shower combo
            self.draw_rectangle(x + 0.5, y + 4, 2.5, 5, 'FIXTURES')
            self.add_text(x + 1.75, y + 6.5, "TUB", 0.3, 'TEXT')

    def draw_closet(self, x, y, width, height):
        """Draw a closet with shelf indication"""
        self.draw_rectangle(x, y, width, height, 'WALLS')
        # Shelf line
        self.msp.add_line((x + 0.5, y + height - 1), (x + width - 0.5, y + height - 1),
                          dxfattribs={'layer': 'FIXTURES'})
        # Rod indication (dashed line below shelf)
        self.msp.add_line((x + 0.5, y + height - 1.5), (x + width - 0.5, y + height - 1.5),
                          dxfattribs={'layer': 'FIXTURES'})

    def generate_floor_plan(self):
        """Generate the complete 3-bedroom house floor plan"""

        # ============================================
        # EXTERIOR WALLS (50' x 40' = 2000 sqft)
        # ============================================
        self.draw_rectangle(0, 0, 50, 40, 'WALLS')

        # ============================================
        # ROOM LAYOUT
        # ============================================

        # --- LIVING ROOM (Front left: 16' x 15') ---
        # South wall of living room
        self.msp.add_line((0, 15), (16, 15), dxfattribs={'layer': 'WALLS'})
        self.add_text(8, 7.5, "LIVING ROOM", 0.6, 'TEXT')
        self.add_text(8, 6, "16' x 15'", 0.4, 'TEXT')
        self.add_text(8, 4.5, "240 sqft", 0.35, 'TEXT')

        # Living room window (front)
        self.draw_window(4, 0, 8, 'WINDOWS')

        # --- OPEN KITCHEN/DINING (Front right: 18' x 15') ---
        # Divider wall (partial)
        self.msp.add_line((16, 0), (16, 10), dxfattribs={'layer': 'WALLS'})

        # Kitchen area (18' x 15')
        self.add_text(34, 7.5, "KITCHEN", 0.6, 'TEXT')
        self.add_text(34, 6, "18' x 15'", 0.4, 'TEXT')
        self.add_text(34, 4.5, "270 sqft", 0.35, 'TEXT')
        self.draw_kitchen_fixtures(25, 0)

        # Kitchen windows
        self.draw_window(38, 0, 6, 'WINDOWS')

        # Dining area label (open to kitchen)
        self.add_text(22, 12, "DINING", 0.5, 'TEXT')
        self.add_text(22, 10.5, "AREA", 0.5, 'TEXT')

        # --- HALLWAY (Center: 5' wide) ---
        # North hallway wall
        self.msp.add_line((0, 15), (0, 40), dxfattribs={'layer': 'WALLS'})  # Already exterior
        self.msp.add_line((16, 15), (16, 40), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((16, 15), (50, 15), dxfattribs={'layer': 'WALLS'})

        # --- MASTER SUITE (Back left: 16' x 14') ---
        self.msp.add_line((0, 26), (16, 26), dxfattribs={'layer': 'WALLS'})
        self.add_text(8, 33, "MASTER BEDROOM", 0.5, 'TEXT')
        self.add_text(8, 31.5, "16' x 14'", 0.4, 'TEXT')
        self.add_text(8, 30, "224 sqft", 0.35, 'TEXT')

        # Master bedroom windows
        self.draw_window(3, 40, 5, 'WINDOWS')
        self.draw_window(10, 40, 5, 'WINDOWS')

        # Master closet (walk-in: 6' x 5')
        self.msp.add_line((0, 21), (6, 21), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((6, 21), (6, 26), dxfattribs={'layer': 'WALLS'})
        self.add_text(3, 23.5, "W.I.C.", 0.35, 'TEXT')
        self.draw_door(6, 23, 2.5, 'left', 'DOORS')

        # Master bathroom (10' x 5')
        self.msp.add_line((6, 21), (16, 21), dxfattribs={'layer': 'WALLS'})
        self.add_text(11, 18, "MASTER BATH", 0.4, 'TEXT')
        self.add_text(11, 16.5, "10' x 6'", 0.35, 'TEXT')
        self.draw_bathroom_fixtures(6, 15, is_master=True)

        # Master bath door
        self.draw_door(7, 21, 2.5, 'right', 'DOORS')

        # Master bedroom door
        self.draw_door(13, 26, 3, 'left', 'DOORS')

        # --- BEDROOM 2 (Back center: 12' x 12') ---
        self.msp.add_line((16, 28), (28, 28), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((28, 28), (28, 40), dxfattribs={'layer': 'WALLS'})
        self.add_text(22, 34, "BEDROOM 2", 0.5, 'TEXT')
        self.add_text(22, 32.5, "12' x 12'", 0.4, 'TEXT')
        self.add_text(22, 31, "144 sqft", 0.35, 'TEXT')

        # Bedroom 2 window
        self.draw_window(19, 40, 6, 'WINDOWS')

        # Bedroom 2 closet
        self.msp.add_line((16, 28), (16, 33), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((16, 33), (20, 33), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((20, 33), (20, 28), dxfattribs={'layer': 'WALLS'})
        self.add_text(18, 30.5, "CL", 0.3, 'TEXT')

        # Bedroom 2 door
        self.draw_door(22, 28, 2.5, 'left', 'DOORS')

        # --- BEDROOM 3 (Back right: 12' x 12') ---
        self.msp.add_line((28, 28), (40, 28), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((40, 28), (40, 40), dxfattribs={'layer': 'WALLS'})
        self.add_text(34, 34, "BEDROOM 3", 0.5, 'TEXT')
        self.add_text(34, 32.5, "12' x 12'", 0.4, 'TEXT')
        self.add_text(34, 31, "144 sqft", 0.35, 'TEXT')

        # Bedroom 3 window
        self.draw_window(31, 40, 6, 'WINDOWS')

        # Bedroom 3 closet
        self.msp.add_line((28, 28), (28, 33), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((28, 33), (32, 33), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((32, 33), (32, 28), dxfattribs={'layer': 'WALLS'})
        self.add_text(30, 30.5, "CL", 0.3, 'TEXT')

        # Bedroom 3 door
        self.draw_door(34, 28, 2.5, 'left', 'DOORS')

        # --- HALL BATHROOM (10' x 8') ---
        self.msp.add_line((40, 15), (40, 28), dxfattribs={'layer': 'WALLS'})
        self.msp.add_line((40, 20), (50, 20), dxfattribs={'layer': 'WALLS'})
        self.add_text(45, 24, "BATHROOM", 0.4, 'TEXT')
        self.add_text(45, 22.5, "10' x 8'", 0.35, 'TEXT')
        self.draw_bathroom_fixtures(40, 20, is_master=False)

        # Hall bathroom door
        self.draw_door(42, 20, 2.5, 'left', 'DOORS')

        # --- LAUNDRY/UTILITY (10' x 5') ---
        self.add_text(45, 17.5, "LAUNDRY", 0.4, 'TEXT')
        self.add_text(45, 16, "10' x 5'", 0.35, 'TEXT')

        # Laundry appliances
        self.draw_rectangle(41, 15.5, 3, 2.5, 'FIXTURES')  # Washer
        self.draw_rectangle(45, 15.5, 3, 2.5, 'FIXTURES')  # Dryer

        # --- GARAGE DOOR (if needed) or SIDE ENTRY ---
        # Side window
        self.draw_window(50, 30, 6, 'WINDOWS')

        # Front entry door
        self.draw_door(16, 0, 3, 'right', 'DOORS')
        self.add_text(17.5, -1.5, "ENTRY", 0.4, 'TEXT')

        # ============================================
        # DIMENSIONS
        # ============================================
        # Overall dimensions
        self.add_dimension(0, 0, 50, 0, -3, 'DIMENSIONS')
        self.add_dimension(0, 0, 0, 40, -3, 'DIMENSIONS')

        # ============================================
        # TITLE BLOCK
        # ============================================
        self.add_text(25, -6, "3-BEDROOM HOUSE PLAN", 1.0, 'TEXT')
        self.add_text(25, -8, "2000 SQFT - OPEN KITCHEN - MASTER SUITE", 0.5, 'TEXT')
        self.add_text(25, -9.5, "SCALE: 1\" = 10'", 0.4, 'TEXT')

        return self

    def save(self, filename):
        """Save the DXF file"""
        self.doc.saveas(filename)
        print(f"House plan saved to: {filename}")
        return filename


def main():
    """Generate the house plan DXF file"""
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "house_plan_3bed_2000sqft.dxf")

    # Generate the floor plan
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
