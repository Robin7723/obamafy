import math
import pathlib
import argparse
from dataclasses import dataclass
from scipy.ndimage import gaussian_filter
from scipy.spatial import KDTree
from scipy import ndimage

import numpy as np
from PIL import Image

import moderngl
import moderngl_window
from moderngl_window import geometry
from moderngl_window.context.base import BaseWindow


@dataclass
class SimParams:
    dt: float = 1/25.0
    viscosity: float = 0.01
    vorticity: float = 0.15
    convergence_force: float = 100.0
    dye_dissipation: float = 1.0
    vel_dissipation: float = 1.0
    pressure_iterations: int = 5
    mouse_radius: float = 0.1
    turbulence_strength: float = 0.2
    settling_strength: float = 0.0
    unmix_strength: float = 100.0


class FluidApp(moderngl_window.WindowConfig):
    title = "Fluid → Image (ModernGL)"
    resource_dir = '.'
    aspect_ratio = None
    gl_version = (3, 3)
    samples = 0
    srgb = True

    # --- CLI args
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        parser.add_argument('--images', type=str, nargs='+', required=True, help='One or more target image paths or directories')
        parser.add_argument('--auto_transition', type=int, default=0, help='Interval in milliseconds to automatically switch to the next target image. 0 disables it.')
        parser.add_argument('--seed_image', type=str, default=None, help='Optional starting image for the dye field')
        parser.add_argument('--scale', type=float, default=1.0, help='Scale the sim relative to image size')
        parser.add_argument('--sim_w', type=int, default=768, help='Simulation width (overrides image if provided)')
        parser.add_argument('--sim_h', type=int, default=0, help='Simulation height (0 = preserve aspect from image/sim_w)')
        parser.add_argument('--no_vsync', action='store_true', help='Disable vsync')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Parse args
        args = self.argv

        image_paths_to_load = []
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
        for p in args.images:
            path = pathlib.Path(p)
            if not path.exists():
                raise FileNotFoundError(f"Provided path does not exist: {path}")
            if path.is_dir():
                # Add all valid image files from the directory
                dir_files = sorted([f for f in path.iterdir() if f.suffix.lower() in valid_extensions])
                image_paths_to_load.extend(dir_files)
                print(f"✓ Found {len(dir_files)} images in directory: {path.name}")
            elif path.is_file():
                # Add a single file
                image_paths_to_load.append(path)

        if not image_paths_to_load:
            raise ValueError("No valid target images found in the specified paths.")

        self.target_image_paths = image_paths_to_load

        # --- AUTO TRANSITION STATE ---
        self.transition_interval_s = args.auto_transition / 1000.0 if args.auto_transition > 0 else 0
        self.transition_timer = 0.0

        self.params = SimParams()

        # --- LOAD ALL TARGET IMAGES ---
        # Get simulation dimensions from the *first* image
        first_img_pil = Image.open(self.target_image_paths[0]).convert('RGB')
        img_w, img_h = first_img_pil.size

        if args.sim_h <= 0:
            sim_w = args.sim_w
            sim_h = int(sim_w * (img_h / img_w))
        else:
            sim_w, sim_h = args.sim_w, args.sim_h

        sim_w = max(64, int(sim_w * args.scale))
        sim_h = max(64, int(sim_h * args.scale))
        self.sim_size = (sim_w, sim_h)

        # Create a list to hold the processed image data
        self.target_images_np = []
        print(f"✓ Loading {len(self.target_image_paths)} target images...")
        for i, path in enumerate(self.target_image_paths):
            pil_img = Image.open(path).convert('RGB')
            # Resize each image to the simulation resolution
            pil_img = pil_img.resize(self.sim_size, Image.LANCZOS)
            pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
            np_img = np.asarray(pil_img, dtype=np.uint8)
            self.target_images_np.append(np_img)
            print(f"  > Loaded target {i+1}: {path.name}")

        # Keep track of the current target
        self.current_target_index = 0
        # For initializing the dye field, use the first target image
        self.target_np = self.target_images_np[self.current_target_index] 

        self.seed_np = None
        if args.seed_image:
            seed_path = pathlib.Path(args.seed_image)
            if not seed_path.exists():
                raise FileNotFoundError(f"Seed image not found: {seed_path}")
            print(f"✓ Loading seed image from: {seed_path}")
            seed_pil = Image.open(seed_path).convert('RGB')
            seed_pil = seed_pil.resize((sim_w, sim_h), Image.LANCZOS)
            seed_pil = seed_pil.transpose(Image.FLIP_TOP_BOTTOM)
            self.seed_np = np.asarray(seed_pil, dtype=np.uint8)

        self.sim_size = (sim_w, sim_h)
        self.quad = geometry.quad_2d(size=(2.0, 2.0))

        # Textures (floating point RGBA)
        tex_args = dict(
            components=4,
            dtype='f4'
        )
        self.tex_velocity = self.ctx.texture(self.sim_size, **tex_args)
        self.tex_velocity_prev = self.ctx.texture(self.sim_size, **tex_args)
        self.tex_dye = self.ctx.texture(self.sim_size, **tex_args)
        self.tex_dye_prev = self.ctx.texture(self.sim_size, **tex_args)
        self.tex_pressure = self.ctx.texture(self.sim_size, **tex_args)
        self.tex_pressure_prev = self.ctx.texture(self.sim_size, **tex_args)
        self.tex_divergence = self.ctx.texture(self.sim_size, **tex_args)
        self.tex_target = self.ctx.texture(self.sim_size, components=3, dtype='f1')
        
        # Static noise texture for turbulence
        self.tex_noise = self.ctx.texture(self.sim_size, components=4, dtype='f1')

        # Upload target image
        self.tex_target.write(self.target_images_np[self.current_target_index].tobytes())

        # Upload noise texture
        noise_data = (np.random.rand(sim_h, sim_w, 4) * 255).astype('uint8')
        self.tex_noise.write(noise_data.tobytes())
        self.tex_noise.use(0)
        self.tex_noise.build_mipmaps()
        print("✓ Noise texture generated with mipmaps")

        # Initialize fields
        self.clear_fields()

        # Sampler
        self.sampler_linear = self.ctx.sampler(filter=(moderngl.LINEAR, moderngl.LINEAR), repeat_x=True, repeat_y=True)
        self.sampler_nearest = self.ctx.sampler(filter=(moderngl.NEAREST, moderngl.NEAREST), repeat_x=True, repeat_y=True)
        self.sampler_mipmap = self.ctx.sampler(filter=(moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR), repeat_x=True, repeat_y=True)

        # Framebuffers
        self.fbo_velocity = self.ctx.framebuffer(self.tex_velocity)
        self.fbo_velocity_prev = self.ctx.framebuffer(self.tex_velocity_prev)
        self.fbo_dye = self.ctx.framebuffer(self.tex_dye)
        self.fbo_dye_prev = self.ctx.framebuffer(self.tex_dye_prev)
        self.fbo_pressure = self.ctx.framebuffer(self.tex_pressure)
        self.fbo_pressure_prev = self.ctx.framebuffer(self.tex_pressure_prev)
        self.fbo_divergence = self.ctx.framebuffer(self.tex_divergence)

        # Programs (shaders)
        shader_dir = pathlib.Path(__file__).parent / "shaders"
        self.prog_advect = self.load_program(shader_dir / "fullscreen.vert", shader_dir / "advect.frag")
        self.prog_divergence = self.load_program(shader_dir / "fullscreen.vert", shader_dir / "divergence.frag")
        self.prog_jacobi = self.load_program(shader_dir / "fullscreen.vert", shader_dir / "jacobi.frag")
        self.prog_projection = self.load_program(shader_dir / "fullscreen.vert", shader_dir / "projection.frag")
        self.prog_apply_forces = self.load_program(shader_dir / "fullscreen.vert", shader_dir / "apply_forces.frag")
        self.prog_render = self.load_program(shader_dir / "fullscreen.vert", shader_dir / "render.frag")
        # REMOVED: self.prog_color_inject

        # Uniforms constant across frames
        for prog in (self.prog_advect, self.prog_divergence, self.prog_jacobi,
                     self.prog_projection, self.prog_apply_forces,
                     self.prog_render):
            if 'resolution' in prog:
                prog['resolution'].value = self.sim_size

        # State
        self.time = 0.0
        self.paused = True
        self.view_mode = 1

        # Make window match aspect of sim
        w, h = self.window_size
        sim_w, sim_h = self.sim_size
        if h == 720:  # default case
            new_w = int(720 * sim_w / sim_h)
            self.wnd.size = (new_w, 720)

        if self.argv.no_vsync:
            self.wnd.vsync = False

        self.setup_sampler_uniforms()

    def setup_sampler_uniforms(self):
        """Set sampler uniforms to correct texture units"""
        self.prog_advect['Texture0'].value = 0
        self.prog_advect['Texture1'].value = 1
        self.prog_divergence['Texture0'].value = 0
        self.prog_jacobi['Texture0'].value = 0
        self.prog_jacobi['Texture1'].value = 1
        self.prog_projection['Texture0'].value = 0
        self.prog_projection['Texture1'].value = 1
        
        # apply_forces now needs 4 textures
        self.prog_apply_forces['Texture0'].value = 0 # Velocity
        self.prog_apply_forces['Texture1'].value = 1 # Dye
        self.prog_apply_forces['Texture2'].value = 2 # Target
        self.prog_apply_forces['Texture3'].value = 3 # Noise
        
        self.prog_render['Texture0'].value = 0
        self.prog_render['Texture1'].value = 1
        self.prog_render['Texture2'].value = 2
        self.prog_render['Texture3'].value = 3
        self.prog_render['Texture4'].value = 4
        print("✓ Sampler uniforms configured")

    def load_program(self, vert_path, frag_path):
        """Load shader with error handling"""
        try:
            vert_code = vert_path.read_text()
            frag_code = frag_path.read_text()
            print(f"✓ Loaded {vert_path.name} and {frag_path.name}")
            prog = self.ctx.program(
                vertex_shader=vert_code,
                fragment_shader=frag_code,
            )
            return prog
        except Exception as e:
            print(f"✗ Shader error in {frag_path.name}:")
            print(e)
            raise   

    def switch_to_next_target(self):
        """Switches the simulation target to the next image in the list."""
        if len(self.target_images_np) > 1:
            self.current_target_index = (self.current_target_index + 1) % len(self.target_images_np)
            print(f"Switching to target image {self.current_target_index + 1}/{len(self.target_images_np)}")
            new_target_data = self.target_images_np[self.current_target_index]
            self.tex_target.write(new_target_data.tobytes())

    def clear_fields(self):
        w, h = self.sim_size
        
        # --- VELOCITY INITIALIZATION (VECTORIZED) ---
        vel = np.zeros((h, w, 4), dtype=np.float32)
        
        # 1. Add initial random noise to the velocity field
        # This replaces the first nested loop by performing all calculations on the entire array at once.
        angles = np.random.uniform(0, 2 * np.pi, (h, w))
        mags = np.random.uniform(0, 3.0, (h, w))
        vel[:, :, 0] = np.cos(angles) * mags
        vel[:, :, 1] = np.sin(angles) * mags
        
        # 2. Add several large-scale vortices
        # This replaces the second, very slow, nested loop structure.
        num_vortices = 5
        # Create coordinate grids that store the x and y coordinate for each pixel
        Y, X = np.mgrid[0:h, 0:w]

        for _ in range(num_vortices):
            # Random vortex properties
            cx, cy = np.random.uniform(0, w), np.random.uniform(0, h)
            strength = np.random.uniform(-6.0, 6.0)
            radius = min(w, h) * 0.3
            falloff_scale = min(w, h) * 0.15

            # Calculate vectors from each pixel to the vortex center (all at once)
            dx = X - cx
            dy = Y - cy

            # Calculate distance for all pixels at once
            dist = np.sqrt(dx*dx + dy*dy) + 1e-5

            # Create a boolean "mask" for pixels within the vortex radius
            mask = dist < radius

            # Get distances and vectors for only the pixels inside the mask
            dist_masked = dist[mask]
            dx_masked = dx[mask]
            dy_masked = dy[mask]

            # Calculate falloff for the masked pixels
            falloff = np.exp(-dist_masked / falloff_scale)

            # Apply the vortex force to the velocity field using the mask.
            # This updates only the relevant pixels in a single operation.
            vel[mask, 0] += -dy_masked / dist_masked * strength * falloff
            vel[mask, 1] += dx_masked / dist_masked * strength * falloff
        
        self.tex_velocity.write(vel.tobytes())
        self.tex_velocity_prev.write(vel.tobytes())
        print("✓ Velocity field initialized.")
        
        # Zero pressure and divergence
        zeros = np.zeros((h, w, 4), dtype=np.float32)
        self.tex_pressure.write(zeros.tobytes())
        self.tex_pressure_prev.write(zeros.tobytes())
        self.tex_divergence.write(zeros.tobytes())

        # --- DYE INITIALIZATION LOGIC ---
        if self.seed_np is not None:
            # If a seed image was provided, use it directly.
            print("✓ Initializing dye field from seed image.")
            srgb_float = self.seed_np.astype(np.float32) / 255.0
            dye = np.power(srgb_float, 2.2)
        else:
            # Otherwise, use the original swirling logic.
            print("✓ Initializing dye field with Voronoi mosaic.")
            target_float = self.target_np.astype(np.float32) / 255.0

            # 1. Define the number of cells for the mosaic
            num_cells = max(100, int(w * h / 2000))
            print(f"  > Generating {num_cells} Voronoi cells...")

            # 2. Scatter random points (cell centers)
            points = np.random.rand(num_cells, 2) * np.array([h, w])
        
            # 3. Use KDTree for efficient nearest-neighbor search
            kdtree = KDTree(points)

            # 4. Create a grid of all pixel coordinates
            y_coords, x_coords = np.mgrid[0:h, 0:w]
            grid_points = np.vstack([y_coords.ravel(), x_coords.ravel()]).T

            # 5. Find the closest cell center for each pixel
            _, labels = kdtree.query(grid_points, k=1)
            labels = labels.reshape(h, w)

            # 6. Calculate the average color for each cell (this part is already efficient)
            avg_colors = np.zeros((num_cells, 3), dtype=np.float32)
            avg_colors[:, 0] = ndimage.mean(target_float[:,:,0], labels=labels, index=range(num_cells))
            avg_colors[:, 1] = ndimage.mean(target_float[:,:,1], labels=labels, index=range(num_cells))
            avg_colors[:, 2] = ndimage.mean(target_float[:,:,2], labels=labels, index=range(num_cells))
            
            # 7. Create the final dye image by mapping labels to average colors
            shuffled_colors = avg_colors[np.random.permutation(num_cells)]
            dye = shuffled_colors[labels]

        print(f"Dye initialized: range [{dye.min():.3f}, {dye.max():.3f}], mean {dye.mean():.3f}")

        # Add alpha channel and write to GPU textures
        a = np.ones((h, w, 1), dtype=np.float32)
        dye_rgba = np.concatenate([dye, a], axis=2).astype(np.float32)
        self.tex_dye.write(dye_rgba.tobytes())
        self.tex_dye_prev.write(dye_rgba.tobytes())

    # --- Input handling
    def on_key_event(self, key, action, modifiers):
        keys = self.wnd.keys
        if action == keys.ACTION_PRESS:
            if key == keys.SPACE:
                self.paused = not self.paused
            elif key == keys.R:
                self.clear_fields()
            elif key == keys.NUMBER_1:
                self.view_mode = 1
            elif key == keys.NUMBER_2:
                self.view_mode = 2
            elif key == keys.NUMBER_3:
                self.view_mode = 3
            elif key == keys.NUMBER_4:
                self.view_mode = 4
            elif key == keys.NUMBER_5:
                self.view_mode = 5
            elif key == keys.S:
                self.save_frame()
            elif key == keys.LEFT_BRACKET:
                self.params.vorticity = max(0.0, self.params.vorticity - 0.05)
                print("vorticity:", self.params.vorticity)
            elif key == keys.RIGHT_BRACKET:
                self.params.vorticity = min(3.0, self.params.vorticity + 0.05)
                print("vorticity:", self.params.vorticity)
            elif key == keys.COMMA:
                self.params.viscosity = max(0.0, self.params.viscosity * 0.8)
                print("viscosity:", self.params.viscosity)
            elif key == keys.PERIOD:
                self.params.viscosity = min(0.01, self.params.viscosity * 1.25)
                print("viscosity:", self.params.viscosity)
            elif key == keys.N:
                self.switch_to_next_target()

    def on_mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        self.apply_mouse_stir(x, y, dx, dy)

    def apply_mouse_stir(self, x, y, dx, dy):
        # Convert mouse to [0,1] UV
        w, h = self.wnd.size
        u = x / w
        v = 1.0 - y / h
        # Write uniforms for apply_forces shader
        self.prog_apply_forces['has_mouse'].value = 1
        self.prog_apply_forces['mouse_uv'].value = (u, v)
        self.prog_apply_forces['mouse_vel'].value = (dx / w, -dy / h)

    def on_render(self, time: float, frame_time: float):
        if not self.paused:
            self.time += frame_time

            # --- AUTO TRANSITION LOGIC ---
            if self.transition_interval_s > 0:
                self.transition_timer += frame_time
                if self.transition_timer >= self.transition_interval_s:
                    self.switch_to_next_target()
                    self.transition_timer = 0.0 # Reset timer

            dt = self.params.dt

            # 1) Advect velocity
            self.fbo_velocity_prev.use()
            self.tex_velocity.use(0)
            self.sampler_linear.use(location=0)
            self.prog_advect['Texture0'].value = 0
            self.prog_advect['dt'].value = dt
            self.prog_advect['dissipation'].value = self.params.vel_dissipation * (1.0 - self.params.viscosity)
            self.prog_advect['is_dye'].value = 0
            self.quad.render(self.prog_advect)
            self.tex_velocity, self.tex_velocity_prev = self.tex_velocity_prev, self.tex_velocity
            self.fbo_velocity, self.fbo_velocity_prev = self.fbo_velocity_prev, self.fbo_velocity
            
            # 2) Compute divergence
            self.fbo_divergence.use()
            self.tex_velocity.use(0)
            self.sampler_linear.use(0)
            self.quad.render(self.prog_divergence)

            # 3) Pressure solve
            self.fbo_pressure.clear(0, 0, 0, 0)
            self.fbo_pressure_prev.clear(0, 0, 0, 0)
            for _ in range(self.params.pressure_iterations):
                self.fbo_pressure_prev.use()
                self.tex_pressure.use(0)
                self.tex_divergence.use(1)
                self.sampler_linear.use(0)
                self.sampler_nearest.use(1)
                self.quad.render(self.prog_jacobi)
                self.tex_pressure, self.tex_pressure_prev = self.tex_pressure_prev, self.tex_pressure
                self.fbo_pressure, self.fbo_pressure_prev = self.fbo_pressure_prev, self.fbo_pressure

            # 4) Projection
            self.fbo_velocity_prev.use()
            self.tex_velocity.use(0)
            self.tex_pressure.use(1)
            self.sampler_linear.use(0)
            self.sampler_linear.use(1)
            self.quad.render(self.prog_projection)
            self.tex_velocity, self.tex_velocity_prev = self.tex_velocity_prev, self.tex_velocity
            self.fbo_velocity, self.fbo_velocity_prev = self.fbo_velocity_prev, self.fbo_velocity

            # 5) Apply forces (Convergence + Damping + Turbulence + Mouse)
            convergence_progress = min(1.0, self.time / 30.0)
            current_force = self.params.convergence_force * (1.5 - 0.5 * convergence_progress)
            
            self.fbo_velocity_prev.use()
            self.tex_velocity.use(0)
            self.tex_dye.use(1)
            self.tex_target.use(2)
            self.tex_noise.use(3) # Bind noise texture
            
            self.sampler_linear.use(0)
            self.sampler_linear.use(1)
            self.sampler_linear.use(2)
            self.sampler_mipmap.use(3) # Use mipmap sampler for noise
            
            self.prog_apply_forces['dt'].value = dt
            self.prog_apply_forces['time'].value = self.time
            self.prog_apply_forces['vorticity_eps'].value = self.params.vorticity
            self.prog_apply_forces['convergence_force'].value = current_force
            self.prog_apply_forces['settling_strength'].value = self.params.settling_strength
            self.prog_apply_forces['turbulence_strength'].value = self.params.turbulence_strength
            self.prog_apply_forces['mouse_radius'].value = self.params.mouse_radius
            self.prog_apply_forces['unmix_strength'].value = self.params.unmix_strength
            self.quad.render(self.prog_apply_forces)
            self.prog_apply_forces['has_mouse'].value = 0

            self.tex_velocity, self.tex_velocity_prev = self.tex_velocity_prev, self.tex_velocity
            self.fbo_velocity, self.fbo_velocity_prev = self.fbo_velocity_prev, self.fbo_velocity

            # 6) Advect dye
            self.fbo_dye_prev.use()
            self.tex_dye.use(0)
            self.tex_velocity.use(1)
            self.sampler_linear.use(0)
            self.sampler_linear.use(1)
            self.prog_advect['dt'].value = dt
            self.prog_advect['dissipation'].value = self.params.dye_dissipation
            self.prog_advect['is_dye'].value = 1
            self.quad.render(self.prog_advect)
            self.tex_dye, self.tex_dye_prev = self.tex_dye_prev, self.tex_dye
            self.fbo_dye, self.fbo_dye_prev = self.fbo_dye_prev, self.fbo_dye

        # Render to screen
        self.ctx.screen.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

        self.tex_dye.use(0)
        self.tex_velocity.use(1)
        self.tex_pressure.use(2)
        self.tex_divergence.use(3)
        self.tex_target.use(4)
        self.sampler_linear.use(0)
        self.sampler_linear.use(1)
        self.sampler_linear.use(2)
        self.sampler_linear.use(3)
        self.sampler_linear.use(4)
        self.prog_render['view_mode'].value = self.view_mode
        self.quad.render(self.prog_render)

    def save_frame(self):
        # Read from the default framebuffer
        w, h = self.wnd.buffer_size
        data = self.ctx.screen.read(components=3, dtype='f1')
        img = Image.frombytes('RGB', (w, h), data).transpose(Image.FLIP_TOP_BOTTOM)
        out = pathlib.Path('output.png')
        img.save(out)
        print(f"Saved {out.resolve()}")


if __name__ == '__main__':
    moderngl_window.run_window_config(FluidApp)
