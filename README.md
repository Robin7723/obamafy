# Obamafy: Fluid Simulation Image Recreation 🎨

A real-time, interactive 2D fluid simulation that magically rearranges colored dye to form any target image. This project uses GPU-accelerated fluid dynamics (Navier-Stokes equations) to create mesmerizing, artistic animations from your favorite pictures.

The core concept is inspired by the incredible work of **@Spu7Nix**. Check out the original short that sparked this idea:
[**Fluid Simulation that Creates Images - YouTube**](https://www.youtube.com/shorts/MeFi68a2pP8)

## ✨ Demos

\<table\>
\<tr\>
\<td align="center"\>\<b\>Time-lapse Convergence\</b\>\</td\>
\<td align="center"\>\<b\>Interactive Features\</b\>\</td\>
\</tr\>
\<tr\>
\<td\>\<img src="https" alt="Demo video showing the fluid converging into an image" width="400"/\>
\</td\>
\<td\>\<img src="https" alt="Demo video showing interactive stirring and image switching" width="400"/\>
\</td\>
\</tr\>
\</table\>

## 🚀 Features

  * **Image to Fluid**: Transforms any image into a dynamic fluid canvas.
  * **Real-Time Simulation**: All calculations are performed on the GPU using `ModernGL` for high performance.
  * **Fully Interactive**: Stir the fluid with your mouse and watch it slowly reform the image.
  * **Image Carousel**: Load multiple images or entire directories and switch between them on the fly.
  * **Auto-Transitions**: Automatically cycle through a list of target images.
  * **Customizable Physics**: Tweak parameters like vorticity and viscosity in real-time.
  * **Debug Views**: Switch between different visual modes to see the underlying physics (velocity, pressure, etc.).
  * **Reproducible Environment**: Uses **Nix** and **devenv** to ensure a hassle-free, one-command setup. No need to manually install Python packages or system libraries\!

-----

## ⚙️ Getting Started

This project is designed to be set up with a single command, even if you have no programming experience. The setup is primarily tested on **Mac** and **Windows (via WSL2)**.

### Prerequisites

You only need to install two tools on your system first.

1.  **Nix Package Manager**: A powerful tool that manages all project dependencies.

      * **Installation Guide**: Follow the official instructions at [**nixos.org/download**](https://nixos.org/download). The recommended "multi-user" installation is best.

2.  **devenv**: A tool that uses Nix to create perfect, isolated development environments.

      * **Installation Guide**: Once Nix is installed, follow the simple steps at [**devenv.sh/getting-started**](https://devenv.sh/getting-started/).

> **Note for Windows Users**: You must first set up the Windows Subsystem for Linux (WSL2). Follow [**this official Microsoft guide**](https://learn.microsoft.com/en-us/windows/wsl/install) to install WSL2 and a distribution like Ubuntu. Then, open your Ubuntu terminal and proceed with the Nix and `devenv` installations above.

### Installation & Setup

Once the prerequisites are met, setting up the project is as easy as 1-2-3.

1.  **Clone the Repository**
    Open your terminal and run this command to download the project files:

    ```bash
    git clone https://github.com/your-username/obamafy.git
    cd obamafy
    ```

2.  **Activate the Environment**
    Run the following command in the project directory:

    ```bash
    devenv shell
    ```

    The first time you run this, `devenv` will automatically download and install **all** the required tools, Python packages, and system libraries. This might take several minutes, but you only have to do it once\! Subsequent runs will be almost instant.

You are now inside the project's environment, ready to go\!

-----

## 🎮 How to Run

You can run the simulation using a simple command. Make sure you have at least one image file (e.g., `.png`, `.jpg`) in the project directory.

### Basic Usage

The easiest way to start is with the built-in script. This command will start the simulation using an image named `cropped-image.png`.

```bash
devenv run start
```

To use your own image, simply change the filename in the `devenv.nix` file under `scripts.start.exec`, or use the full command-line options below.

### Advanced Usage (Command-Line Arguments)

You can customize the simulation by passing arguments directly to the Python script. Here are some examples:

  * **Run with a single target image:**

    ```bash
    uv run python app.py --images my_picture.jpg
    ```

  * **Run with multiple images (switch between them with the 'N' key):**

    ```bash
    uv run python app.py --images cat.png dog.png
    ```

  * **Load all images from a directory:**

    ```bash
    uv run python app.py --images ./my_image_folder/
    ```

  * **Start with a different initial pattern (seed image):**

    ```bash
    uv run python app.py --images target.png --seed_image abstract_art.png
    ```

  * **Automatically transition to the next image every 10 seconds (10000 ms):**

    ```bash
    uv run python app.py --images ./my_image_folder/ --auto_transition 10000
    ```

### All Available Arguments

| Argument                | Default | Description                                                               |
| ----------------------- | ------- | ------------------------------------------------------------------------- |
| `--images`              | *None* | **(Required)** One or more paths to target images or directories.         |
| `--auto_transition`     | `0`     | Interval in milliseconds to auto-switch images. `0` disables it.          |
| `--seed_image`          | *None* | Path to an image used for the initial dye state. Defaults to a mosaic.    |
| `--scale`               | `1.0`   | Multiplier for the simulation resolution (e.g., `0.5` for half-res).       |
| `--sim_w`               | `768`   | Manually set the simulation width.                                        |
| `--sim_h`               | `0`     | Manually set the simulation height. `0` preserves the aspect ratio.       |
| `--no_vsync`            | `false` | Disable VSync, which may increase FPS.                                    |

-----

## ⌨️ Controls

You can interact with the simulation in real-time.

| Key                 | Action                                    |
| ------------------- | ----------------------------------------- |
| **Mouse Drag** | Click and drag to stir the fluid.         |
| **`Space`** | Pause or resume the simulation.           |
| **`R`** | Reset the fluid and dye to its initial state. |
| **`N`** | Switch to the next target image.          |
| **`S`** | Save the current view as `output.png`. (buggy, crashes the app 50/50)    |
| **`1`** | **View Mode**: Final Dye (default)        |
| **`2`** | **View Mode**: Velocity Field             |
| **`3`** | **View Mode**: Pressure Field             |
| **`4`** | **View Mode**: Divergence Field           |
| **`5`** | **View Mode**: Target Image               |

-----

## 🔬 How It Works

The simulation is built on the principles of computational fluid dynamics (CFD), specifically solving a simplified version of the **Navier-Stokes equations** on a 2D grid.

1.  **Grid-Based Solver**: The simulation space is a grid where each cell holds physical quantities like velocity and pressure.
2.  **Advection**: In each step, the dye and velocity values are moved (advected) along the velocity field.
3.  **Pressure & Projection**: The simulation calculates pressure differences to ensure the fluid is incompressible (doesn't bunch up or thin out). This step "projects" the velocity field to make it divergence-free.
4.  **Force Application**: Several forces are added to the velocity field:
      * **Convergence Force**: The core magic. This force pushes dye toward the correct color regions of the target image by calculating a "color error" gradient.
      * **Vorticity Confinement**: Amplifies small vortices to create more detailed and swirling motion.
      * **User Interaction**: Forces are added based on your mouse movements to stir the fluid.
5.  **GPU Acceleration**: All of these steps are written as **GLSL shaders** and executed in parallel on the GPU via `ModernGL`, allowing for high-resolution, real-time performance.

## 📄 License

This project is open-source and available under the [MIT License]().

-----