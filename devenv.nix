{ pkgs, ... }:

let
  # ----- Python toolchain ----------------------------------------------------
  python = pkgs.python312;
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
  packages = with pkgs; [
    # OpenGL / Mesa drivers for hardware acceleration
    mesa
    libGL
    libGLU
    glxinfo

    # X11 libraries (needed for OpenGL contexts)
    xorg.libX11
    xorg.libXext
    xorg.libXrender
    xorg.libxcb

    zlib
  ];

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
      glxinfo | grep "OpenGL renderer" || echo "!! Could not get OpenGL info"
      glxinfo | grep "OpenGL version" || true
    else
      echo "!! glxinfo not available"
    fi
    echo "----------------------------------------------"
  '';

  # -------------------------------------------------------------------------
  # 5. Helper scripts
  # -------------------------------------------------------------------------
  scripts.start.exec = ''
    uv run python .\app.py --images .\assets\demo\  --seed_image .\assets\seed.jpeg --sim_w 1024
  '';
}
