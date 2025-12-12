#!/usr/bin/env python3
"""
Blender 3D House Rendering Script
Creates a 3D model of a 3-bedroom, 2000 sqft house with open kitchen and master suite
Run this script in Blender: blender --background --python blender_3d_render.py

Requirements: Blender 2.80+ with Python API
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector


class House3DGenerator:
    """Generates a 3D house model in Blender"""

    def __init__(self):
        # House dimensions (in meters, scaled from 50' x 40' house)
        # 1 foot = 0.3048 meters
        self.ft_to_m = 0.3048
        self.house_width = 50 * self.ft_to_m  # ~15.24m
        self.house_depth = 40 * self.ft_to_m  # ~12.19m
        self.wall_height = 9 * self.ft_to_m   # 9 feet ceiling
        self.wall_thickness = 0.15            # 15cm walls

        # Material colors
        self.colors = {
            'exterior_wall': (0.85, 0.82, 0.75, 1.0),  # Light beige
            'interior_wall': (0.95, 0.95, 0.92, 1.0),  # Off-white
            'floor': (0.6, 0.45, 0.3, 1.0),            # Wood brown
            'roof': (0.3, 0.25, 0.2, 1.0),             # Dark brown
            'window': (0.7, 0.85, 0.95, 0.3),          # Light blue glass
            'door': (0.45, 0.35, 0.25, 1.0),           # Dark wood
            'kitchen': (0.9, 0.9, 0.9, 1.0),           # White cabinets
            'grass': (0.2, 0.5, 0.2, 1.0),             # Green
        }

    def clear_scene(self):
        """Clear all objects from the scene"""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

    def create_material(self, name, color, metallic=0.0, roughness=0.5):
        """Create a material with specified properties"""
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        if len(color) > 3 and color[3] < 1.0:
            mat.blend_method = 'BLEND'
            bsdf.inputs['Alpha'].default_value = color[3]
        return mat

    def create_box(self, name, location, dimensions, material):
        """Create a box mesh with given parameters"""
        bpy.ops.mesh.primitive_cube_add(location=location)
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = (dimensions[0]/2, dimensions[1]/2, dimensions[2]/2)
        obj.data.materials.append(material)
        return obj

    def create_wall(self, name, start, end, height, thickness, material, has_opening=False,
                    opening_start=0, opening_width=0, opening_height=0, opening_bottom=0):
        """Create a wall segment, optionally with door/window opening"""
        # Calculate wall length and angle
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)
        angle = math.atan2(dy, dx)

        # Center position
        cx = (start[0] + end[0]) / 2
        cy = (start[1] + end[1]) / 2
        cz = height / 2

        if not has_opening:
            # Simple wall
            bpy.ops.mesh.primitive_cube_add(location=(cx, cy, cz))
            wall = bpy.context.active_object
            wall.name = name
            wall.scale = (length/2, thickness/2, height/2)
            wall.rotation_euler.z = angle
            wall.data.materials.append(material)
            return wall
        else:
            # Wall with opening (door or window)
            # Create wall mesh with BMesh for boolean-like effect
            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)
            bpy.context.collection.objects.link(obj)

            bm = bmesh.new()

            # Create outer wall vertices
            # Wall segments: left of opening, above opening, right of opening, below opening (if window)

            # Left section
            if opening_start > 0:
                left_length = opening_start
                left_verts = [
                    bm.verts.new((0, -thickness/2, 0)),
                    bm.verts.new((left_length, -thickness/2, 0)),
                    bm.verts.new((left_length, thickness/2, 0)),
                    bm.verts.new((0, thickness/2, 0)),
                    bm.verts.new((0, -thickness/2, height)),
                    bm.verts.new((left_length, -thickness/2, height)),
                    bm.verts.new((left_length, thickness/2, height)),
                    bm.verts.new((0, thickness/2, height)),
                ]
                # Create faces for left section
                bm.faces.new([left_verts[0], left_verts[1], left_verts[5], left_verts[4]])
                bm.faces.new([left_verts[2], left_verts[3], left_verts[7], left_verts[6]])
                bm.faces.new([left_verts[0], left_verts[3], left_verts[7], left_verts[4]])
                bm.faces.new([left_verts[1], left_verts[2], left_verts[6], left_verts[5]])
                bm.faces.new([left_verts[4], left_verts[5], left_verts[6], left_verts[7]])
                bm.faces.new([left_verts[0], left_verts[1], left_verts[2], left_verts[3]])

            # Right section
            right_start = opening_start + opening_width
            if right_start < length:
                right_verts = [
                    bm.verts.new((right_start, -thickness/2, 0)),
                    bm.verts.new((length, -thickness/2, 0)),
                    bm.verts.new((length, thickness/2, 0)),
                    bm.verts.new((right_start, thickness/2, 0)),
                    bm.verts.new((right_start, -thickness/2, height)),
                    bm.verts.new((length, -thickness/2, height)),
                    bm.verts.new((length, thickness/2, height)),
                    bm.verts.new((right_start, thickness/2, height)),
                ]
                bm.faces.new([right_verts[0], right_verts[1], right_verts[5], right_verts[4]])
                bm.faces.new([right_verts[2], right_verts[3], right_verts[7], right_verts[6]])
                bm.faces.new([right_verts[0], right_verts[3], right_verts[7], right_verts[4]])
                bm.faces.new([right_verts[1], right_verts[2], right_verts[6], right_verts[5]])
                bm.faces.new([right_verts[4], right_verts[5], right_verts[6], right_verts[7]])
                bm.faces.new([right_verts[0], right_verts[1], right_verts[2], right_verts[3]])

            # Above opening
            top_verts = [
                bm.verts.new((opening_start, -thickness/2, opening_bottom + opening_height)),
                bm.verts.new((opening_start + opening_width, -thickness/2, opening_bottom + opening_height)),
                bm.verts.new((opening_start + opening_width, thickness/2, opening_bottom + opening_height)),
                bm.verts.new((opening_start, thickness/2, opening_bottom + opening_height)),
                bm.verts.new((opening_start, -thickness/2, height)),
                bm.verts.new((opening_start + opening_width, -thickness/2, height)),
                bm.verts.new((opening_start + opening_width, thickness/2, height)),
                bm.verts.new((opening_start, thickness/2, height)),
            ]
            bm.faces.new([top_verts[0], top_verts[1], top_verts[5], top_verts[4]])
            bm.faces.new([top_verts[2], top_verts[3], top_verts[7], top_verts[6]])
            bm.faces.new([top_verts[4], top_verts[5], top_verts[6], top_verts[7]])

            # Below opening (if window)
            if opening_bottom > 0:
                bottom_verts = [
                    bm.verts.new((opening_start, -thickness/2, 0)),
                    bm.verts.new((opening_start + opening_width, -thickness/2, 0)),
                    bm.verts.new((opening_start + opening_width, thickness/2, 0)),
                    bm.verts.new((opening_start, thickness/2, 0)),
                    bm.verts.new((opening_start, -thickness/2, opening_bottom)),
                    bm.verts.new((opening_start + opening_width, -thickness/2, opening_bottom)),
                    bm.verts.new((opening_start + opening_width, thickness/2, opening_bottom)),
                    bm.verts.new((opening_start, thickness/2, opening_bottom)),
                ]
                bm.faces.new([bottom_verts[0], bottom_verts[1], bottom_verts[5], bottom_verts[4]])
                bm.faces.new([bottom_verts[2], bottom_verts[3], bottom_verts[7], bottom_verts[6]])
                bm.faces.new([bottom_verts[0], bottom_verts[1], bottom_verts[2], bottom_verts[3]])

            bm.to_mesh(mesh)
            bm.free()

            # Position and rotate
            obj.location = (start[0], start[1], 0)
            obj.rotation_euler.z = angle
            obj.data.materials.append(material)

            return obj

    def create_floor(self):
        """Create the floor of the house"""
        mat = self.create_material('Floor', self.colors['floor'], roughness=0.7)
        floor = self.create_box(
            'Floor',
            (self.house_width/2, self.house_depth/2, -0.05),
            (self.house_width, self.house_depth, 0.1),
            mat
        )
        return floor

    def create_ground(self):
        """Create the ground/lawn around the house"""
        mat = self.create_material('Ground', self.colors['grass'], roughness=0.9)
        ground = self.create_box(
            'Ground',
            (self.house_width/2, self.house_depth/2, -0.15),
            (self.house_width * 2, self.house_depth * 2, 0.1),
            mat
        )
        return ground

    def create_roof(self):
        """Create a simple gable roof"""
        mat = self.create_material('Roof', self.colors['roof'], roughness=0.8)

        # Create roof mesh
        mesh = bpy.data.meshes.new('Roof')
        obj = bpy.data.objects.new('Roof', mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()

        roof_overhang = 0.5  # 50cm overhang
        roof_height = 3.0    # 3m roof peak height
        base_height = self.wall_height

        # Roof vertices
        v0 = bm.verts.new((-roof_overhang, -roof_overhang, base_height))
        v1 = bm.verts.new((self.house_width + roof_overhang, -roof_overhang, base_height))
        v2 = bm.verts.new((self.house_width + roof_overhang, self.house_depth + roof_overhang, base_height))
        v3 = bm.verts.new((-roof_overhang, self.house_depth + roof_overhang, base_height))
        v4 = bm.verts.new((self.house_width/2, -roof_overhang, base_height + roof_height))
        v5 = bm.verts.new((self.house_width/2, self.house_depth + roof_overhang, base_height + roof_height))

        # Roof faces
        bm.faces.new([v0, v1, v4])  # Front left slope
        bm.faces.new([v1, v2, v5, v4])  # Right slope
        bm.faces.new([v2, v3, v5])  # Back right slope
        bm.faces.new([v3, v0, v4, v5])  # Left slope

        # Gable ends (triangles)
        bm.faces.new([v0, v4, v3])
        bm.faces.new([v1, v5, v2])

        bm.to_mesh(mesh)
        bm.free()

        obj.data.materials.append(mat)
        return obj

    def create_exterior_walls(self):
        """Create all exterior walls with windows and doors"""
        ext_mat = self.create_material('Exterior', self.colors['exterior_wall'], roughness=0.6)
        walls = []

        # Front wall (South) - with entry door and windows
        # Entry door at x=16ft (4.88m), width 3ft (0.91m)
        # Living room window at x=4-12ft
        # Kitchen window at x=38-44ft

        # Simple exterior walls for now
        # North wall
        walls.append(self.create_wall(
            'North_Wall',
            (0, self.house_depth), (self.house_width, self.house_depth),
            self.wall_height, self.wall_thickness, ext_mat
        ))

        # South wall (front)
        walls.append(self.create_wall(
            'South_Wall',
            (0, 0), (self.house_width, 0),
            self.wall_height, self.wall_thickness, ext_mat
        ))

        # East wall
        walls.append(self.create_wall(
            'East_Wall',
            (self.house_width, 0), (self.house_width, self.house_depth),
            self.wall_height, self.wall_thickness, ext_mat
        ))

        # West wall
        walls.append(self.create_wall(
            'West_Wall',
            (0, 0), (0, self.house_depth),
            self.wall_height, self.wall_thickness, ext_mat
        ))

        return walls

    def create_interior_walls(self):
        """Create interior walls dividing rooms"""
        int_mat = self.create_material('Interior', self.colors['interior_wall'], roughness=0.4)
        walls = []

        # Main dividing wall at y=15ft (4.57m) - separates living/kitchen from bedrooms
        walls.append(self.create_wall(
            'Main_Divider',
            (0, 15 * self.ft_to_m), (self.house_width, 15 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        # Living room / kitchen partial divider at x=16ft
        walls.append(self.create_wall(
            'LivingKitchen_Divider',
            (16 * self.ft_to_m, 0), (16 * self.ft_to_m, 10 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        # Master suite wall at y=26ft
        walls.append(self.create_wall(
            'Master_Wall',
            (0, 26 * self.ft_to_m), (16 * self.ft_to_m, 26 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        # Master closet wall
        walls.append(self.create_wall(
            'Master_Closet',
            (6 * self.ft_to_m, 21 * self.ft_to_m), (6 * self.ft_to_m, 26 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        # Master bath wall
        walls.append(self.create_wall(
            'Master_Bath',
            (6 * self.ft_to_m, 21 * self.ft_to_m), (16 * self.ft_to_m, 21 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        # Bedroom 2 walls
        walls.append(self.create_wall(
            'Bedroom2_Wall',
            (16 * self.ft_to_m, 28 * self.ft_to_m), (28 * self.ft_to_m, 28 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))
        walls.append(self.create_wall(
            'Bedroom2_Wall2',
            (28 * self.ft_to_m, 28 * self.ft_to_m), (28 * self.ft_to_m, self.house_depth),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        # Bedroom 3 walls
        walls.append(self.create_wall(
            'Bedroom3_Wall',
            (28 * self.ft_to_m, 28 * self.ft_to_m), (40 * self.ft_to_m, 28 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))
        walls.append(self.create_wall(
            'Bedroom3_Wall2',
            (40 * self.ft_to_m, 28 * self.ft_to_m), (40 * self.ft_to_m, self.house_depth),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        # Hall bathroom wall
        walls.append(self.create_wall(
            'HallBath_Wall',
            (40 * self.ft_to_m, 15 * self.ft_to_m), (40 * self.ft_to_m, 28 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))
        walls.append(self.create_wall(
            'HallBath_Wall2',
            (40 * self.ft_to_m, 20 * self.ft_to_m), (self.house_width, 20 * self.ft_to_m),
            self.wall_height, self.wall_thickness/2, int_mat
        ))

        return walls

    def create_kitchen_island(self):
        """Create kitchen island"""
        mat = self.create_material('Kitchen', self.colors['kitchen'], roughness=0.3)

        # Island counter
        island = self.create_box(
            'Kitchen_Island',
            ((27 + 4) * self.ft_to_m, (5 + 1.5) * self.ft_to_m, 0.9),
            (8 * self.ft_to_m, 3 * self.ft_to_m, 0.9),
            mat
        )
        return island

    def create_windows(self):
        """Create window glass panels"""
        mat = self.create_material('Glass', self.colors['window'], roughness=0.1, metallic=0.0)
        windows = []

        window_height = 1.2  # 1.2m tall windows
        window_bottom = 0.9  # 90cm from floor

        # Living room window (front)
        windows.append(self.create_box(
            'Window_LivingRoom',
            (8 * self.ft_to_m, 0, window_bottom + window_height/2),
            (8 * self.ft_to_m, 0.05, window_height),
            mat
        ))

        # Kitchen window (front)
        windows.append(self.create_box(
            'Window_Kitchen',
            (41 * self.ft_to_m, 0, window_bottom + window_height/2),
            (6 * self.ft_to_m, 0.05, window_height),
            mat
        ))

        # Master bedroom windows (back)
        windows.append(self.create_box(
            'Window_Master1',
            (5.5 * self.ft_to_m, self.house_depth, window_bottom + window_height/2),
            (5 * self.ft_to_m, 0.05, window_height),
            mat
        ))
        windows.append(self.create_box(
            'Window_Master2',
            (12.5 * self.ft_to_m, self.house_depth, window_bottom + window_height/2),
            (5 * self.ft_to_m, 0.05, window_height),
            mat
        ))

        # Bedroom 2 window
        windows.append(self.create_box(
            'Window_Bed2',
            (22 * self.ft_to_m, self.house_depth, window_bottom + window_height/2),
            (6 * self.ft_to_m, 0.05, window_height),
            mat
        ))

        # Bedroom 3 window
        windows.append(self.create_box(
            'Window_Bed3',
            (34 * self.ft_to_m, self.house_depth, window_bottom + window_height/2),
            (6 * self.ft_to_m, 0.05, window_height),
            mat
        ))

        return windows

    def setup_camera(self):
        """Setup camera for rendering"""
        # Create camera
        bpy.ops.object.camera_add(
            location=(self.house_width * 1.5, -self.house_depth * 0.8, self.wall_height * 2)
        )
        camera = bpy.context.active_object
        camera.name = 'RenderCamera'

        # Point camera at house center
        direction = Vector((self.house_width/2, self.house_depth/2, self.wall_height/2)) - camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()

        # Set as active camera
        bpy.context.scene.camera = camera

        return camera

    def setup_lighting(self):
        """Setup lighting for the scene"""
        # Sun light
        bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
        sun = bpy.context.active_object
        sun.name = 'Sun'
        sun.data.energy = 3.0
        sun.rotation_euler = (math.radians(45), math.radians(30), math.radians(45))

        # Add ambient light (area light)
        bpy.ops.object.light_add(type='AREA', location=(self.house_width/2, self.house_depth/2, 15))
        area = bpy.context.active_object
        area.name = 'AmbientLight'
        area.data.energy = 500
        area.data.size = 20

        return sun, area

    def setup_render_settings(self, output_path):
        """Configure render settings"""
        scene = bpy.context.scene

        # Render engine
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'  # Use 'GPU' if available
        scene.cycles.samples = 128

        # Output settings
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
        scene.render.resolution_percentage = 100
        scene.render.filepath = output_path
        scene.render.image_settings.file_format = 'PNG'

        # World background
        world = bpy.data.worlds.new('Sky')
        scene.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes['Background']
        bg.inputs['Color'].default_value = (0.5, 0.7, 1.0, 1.0)  # Light blue sky
        bg.inputs['Strength'].default_value = 0.5

    def generate_house(self):
        """Generate the complete 3D house model"""
        print("Generating 3D house model...")

        # Clear existing scene
        self.clear_scene()

        # Create all elements
        self.create_ground()
        self.create_floor()
        self.create_exterior_walls()
        self.create_interior_walls()
        self.create_kitchen_island()
        self.create_windows()
        self.create_roof()

        # Setup scene
        self.setup_camera()
        self.setup_lighting()

        print("3D house model generated successfully!")

    def render(self, output_path):
        """Render the scene to an image"""
        self.setup_render_settings(output_path)
        print(f"Rendering to: {output_path}")
        bpy.ops.render.render(write_still=True)
        print("Render complete!")

    def save_blend_file(self, filepath):
        """Save the Blender file"""
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        print(f"Blender file saved to: {filepath}")


def main():
    """Main function to generate and render the house"""
    # Get output directory
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
    output_dir = script_dir

    # Create generator
    generator = House3DGenerator()

    # Generate house
    generator.generate_house()

    # Save blend file
    blend_path = os.path.join(output_dir, "house_3d_model.blend")
    generator.save_blend_file(blend_path)

    # Render image
    render_path = os.path.join(output_dir, "house_3d_render.png")
    generator.render(render_path)

    print("\n" + "="*50)
    print("3D HOUSE MODEL COMPLETED")
    print("="*50)
    print(f"\nFiles created:")
    print(f"  - Blender file: {blend_path}")
    print(f"  - Rendered image: {render_path}")
    print(f"\nHouse specifications:")
    print(f"  - 3 Bedrooms (Master + 2 additional)")
    print(f"  - 2 Bathrooms")
    print(f"  - Open kitchen with island")
    print(f"  - Master suite with walk-in closet")
    print(f"  - Total area: ~2000 sqft")


if __name__ == "__main__":
    main()
