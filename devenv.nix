{ pkgs, lib, ... }:

let
  # ----- Python toolchain ----------------------------------------------------
  python = pkgs.python312;
  inherit (pkgs.stdenv) isLinux isDarwin;
in
{
  # -------------------------------------------------------------------------
  # 1. Languages
  # -------------------------------------------------------------------------
  languages.python = {
    enable = true;
    package = python;
    venv.enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  # -------------------------------------------------------------------------
  # 2. Packages available in the shell
  # -------------------------------------------------------------------------
  packages =
    with pkgs;
    [
      zlib
      pkg-config
    ]
    # Linux-only OpenGL/GLX/X11 bits
    ++ lib.optionals isLinux [
      mesa
      libGL
      libGLU
      glxinfo
      xorg.libX11
      xorg.libXext
      xorg.libXrender
      xorg.libxcb
    ]
    # macOS uses Apple frameworks for OpenGL; no extra packages needed
    ++ lib.optionals isDarwin [ ];

  # -------------------------------------------------------------------------
  # 3. Environment variables
  # -------------------------------------------------------------------------
  env = {
  };

  # -------------------------------------------------------------------------
  # 4. Nice‑to‑have shell banner and sanity checks
  # -------------------------------------------------------------------------
  enterShell = ''
    source .devenv/state/venv/bin/activate

    echo "----------------------------------------------"
    echo "Python 3.12 • uv • OpenGL"
    echo "----------------------------------------------"

    echo "[INFO] Python:"
    python --version
    echo ""

    echo "[INFO] OpenGL Renderer:"
    if command -v glxinfo >/dev/null 2>&1; then
      glxinfo | grep -E "OpenGL (renderer|version)" || echo "!! Could not get OpenGL info via glxinfo"
    elif [ "$(uname -s)" = "Darwin" ]; then
      system_profiler SPDisplaysDataType | awk '/Chipset Model|Vendor|VRAM|Metal|Displays:/{print}'
    else
      echo "!! No GPU info tool available on this platform"
    fi
    echo "----------------------------------------------"
  '';

  # -------------------------------------------------------------------------
  # 5. Helper scripts
  # -------------------------------------------------------------------------
  scripts.start.exec = ''
    uv run python app.py --images .\assets\demo\  --seed_image .\assets\seed.jpeg --sim_w 1024
  '';
}
