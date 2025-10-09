<div align="center">
  <h1>
    🎨 Obamafy 🎨
  </h1>

  <p><i>Fluid Simulation Image Recreation!</i></p>

  ---
  
  <p>
    A real-time, interactive 2D fluid simulation that magically rearranges colored dye to form any target image. This project uses GPU-accelerated fluid dynamics (Navier-Stokes equations) to create mesmerizing, artistic animations from your favorite pictures.
  </p>
  <p>
    <i>The core concept is inspired by the incredible work of @Spu7Nix. Check out the original short that sparked this idea:
    <a href="https://www.youtube.com/shorts/MeFi68a2pP8">Fluid Simulation that Creates Images - YouTube</a></i>
  </p>

  <h2>✨ See it in Action! ✨</h2>
  
  <p>Here's a little glimpse of what the simulation can do:</p>
  <video src="https://github.com/user-attachments/assets/83e2e714-8542-4021-a80e-4aaa4883ef9e"></video>
  <br><br>
</div>

## 🚀 Features

  * **Image to Fluid**: Transforms any image into a dynamic fluid canvas.
  * **Real-Time Simulation**: All calculations are performed on the GPU using `ModernGL` for high performance.
  * **Fully Interactive**: Stir the fluid with your mouse and watch it slowly reform the image.
  * **Image Carousel**: Load multiple images or entire directories and switch between them on the fly.
  * **Auto-Transitions**: Automatically cycle through a list of target images.
  * **Customizable Physics**: Tweak parameters like vorticity and viscosity in real-time.
  * **Debug Views**: Switch between different visual modes to see the underlying physics (velocity, pressure, etc.).
  * **Reproducible Environment**: Uses **Nix** and **devenv** for a hassle-free, one-command setup.

-----

## ⚙️ Getting Started (Recommended: Nix)

This project is designed for a one-command setup using **Nix** and **devenv**, which guarantees a perfectly reproducible environment. This is the recommended method for **Mac** and **Linux** (including **Windows via WSL2**).

> For a traditional Python setup on native **Windows, macOS, or Linux** without installing Nix, please see the **[Alternative Setup Guide](#alternative-setup)** below.

### Prerequisites

You only need to install two tools on your system first.

1.  **Nix Package Manager**: A powerful tool that manages all project dependencies.

      * **Installation Guide**: Follow the official instructions at [**nixos.org/download**](https://nixos.org/download). The recommended "multi-user" installation is best.

2.  **devenv**: A tool that uses Nix to create perfect, isolated development environments.

      * **Installation Guide**: Once Nix is installed, follow the simple steps at [**devenv.sh/getting-started**](https://devenv.sh/getting-started/).

> **Note for Windows Users**: This method requires the Windows Subsystem for Linux (WSL2). Follow [**this official Microsoft guide**](https://learn.microsoft.com/en-us/windows/wsl/install) to install WSL2 and a distribution like Ubuntu. Then, open your Ubuntu terminal and proceed with the Nix and `devenv` installations above.

### Installation & Running

Once the prerequisites are met, setting up and running the project is simple.

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

    The first time you run this, `devenv` will automatically download and install **all** the required tools and libraries. This might take several minutes, but you only have to do it once\!

3.  **Run the Simulation**
    With the environment active, use the built-in script to start:

    ```bash
    devenv run start
    ```

-----

## <a id="alternative-setup"></a> ⚙️ Alternative Setup: Manual Python Environment

If you prefer not to use Nix, you can set up the project on **native Windows, macOS, or Linux** using standard Python tools.

### Prerequisites

1.  **Python 3.12+**: Download from [python.org](https://python.org). During installation on Windows, ensure you check the box **"Add Python to PATH"**.
2.  **Git**: For cloning the repository. You can get it from [git-scm.com](https://git-scm.com/).
3.  **Up-to-date GPU Drivers**: This is essential for OpenGL. Make sure you have the latest drivers from NVIDIA, AMD, or Intel.

### Installation & Running

1.  **Clone the Repository**
    Open your terminal (**PowerShell** or **Command Prompt** on Windows) and run:

    ```bash
    git clone https://github.com/your-username/obamafy.git
    cd obamafy
    ```

2.  **Create and Activate a Virtual Environment**
    This isolates the project's dependencies.

    ```bash
    # Create the environment
    python -m venv .venv
    ```

    Now, activate it. The command differs based on your operating system:

      * On **Windows** (in PowerShell or Command Prompt):
        ```powershell
        .\.venv\Scripts\activate
        ```
      * On **macOS and Linux** (in bash, zsh, etc.):
        ```bash
        source .venv/bin/activate
        ```

    Your terminal prompt should now be prefixed with `(.venv)`.

3.  **Install Dependencies**
    We'll use `pip` to install the `uv` package manager, and then use `uv` to install all the project's dependencies from the `pyproject.toml` file.

    ```bash
    # 1. Install uv
    pip install uv

    # 2. Install all project packages
    uv pip install .
    ```

4.  **Run the Simulation**
    Now you can run the application directly using `python`.

    ```bash
    # Basic usage with the default image
    python app.py --images cropped-image.png
    ```

-----

## 🎮 How to Run (Advanced Usage)

You can customize the simulation by passing arguments directly to the Python script.

**Note**: If you used the **Nix/devenv** setup, prefix commands with `uv run`. If you used the **manual setup**, just use `python`.

  * **Run with a single target image:**

    ```bash
    # Nix/devenv:
    uv run python app.py --images my_picture.jpg
    # Manual setup:
    python app.py --images my_picture.jpg
    ```

  * **Run with multiple images (switch between them with the 'N' key):**

    ```bash
    python app.py --images cat.png dog.png
    ```

  * **Load all images from a directory:**

    ```bash
    # On macOS/Linux:
    python app.py --images ./my_image_folder/
    # On Windows:
    python app.py --images "C:\Path\To\Your\Images\"
    ```

  * **Start with a different initial pattern (seed image):**

    ```bash
    python app.py --images target.png --seed_image abstract_art.png
    ```

  * **Automatically transition to the next image every 10 seconds (10000 ms):**

    ```bash
    python app.py --images ./my_image_folder/ --auto_transition 10000
    ```

### All Available Arguments

| Argument              | Default | Description                                                               |
| ----------------------- | ------- | ------------------------------------------------------------------------- |
| `--images`              | *None* | **(Required)** One or more paths to target images or directories.         |
| `--auto_transition`     | `0`     | Interval in milliseconds to auto-switch images. `0` disables it.          |
| `--seed_image`          | *None* | Path to an image used for the initial dye state. Defaults to a mosaic.    |
| `--scale`               | `1.0`   | Multiplier for the simulation resolution (e.g., `0.5` for half-res).      |
| `--sim_w`               | `768`   | Manually set the simulation width.                                        |
| `--sim_h`               | `0`     | Manually set the simulation height. `0` preserves the aspect ratio.       |
| `--no_vsync`            | `false` | Disable VSync, which may increase FPS.                                    |

-----

## ⌨️ Controls

You can interact with the simulation in real-time.

| Key            | Action                                    |
| -------------- | ----------------------------------------- |
| **Mouse Drag** | Click and drag to stir the fluid.         |
| **`Space`** | Pause or resume the simulation.           |
| **`R`** | Reset the fluid and dye to its initial state. |
| **`N`** | Switch to the next target image.          |
| **`S`** | Save the current view as `output.png`. (buggy, crashes the app 50/50) |
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

This project is open-source and available under the [MIT License](LICENSE).
