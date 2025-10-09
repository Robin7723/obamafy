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
  # 3. Environment variables / WSL quirks
  # -------------------------------------------------------------------------
  env = {
    LD_LIBRARY_PATH = "/usr/lib/wsl/lib";
    CUDA_PATH = "/usr/lib/wsl/lib";
  };

  # -------------------------------------------------------------------------
  # 4. Nice‑to‑have shell banner and sanity checks
  # -------------------------------------------------------------------------
  enterShell = ''
    source .devenv/state/venv/bin/activate

    echo "----------------------------------------------"
    echo "Python 3.12 • uv • PyTorch - CUDA devenv (WSL)"
    echo "----------------------------------------------"

    echo "[INFO] Python:"
    python --version
    echo ""

    echo "[INFO] Checking NVIDIA in WSL…"
    if nvidia-smi >/dev/null 2>&1; then
      nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    else
      echo "!! nvidia-smi not found - CUDA is unlikely to work"
    fi
    echo ""

    echo "[INFO] OpenGL Renderer:"
    if command -v glxinfo >/dev/null 2>&1; then
      glxinfo | grep "OpenGL renderer" || echo "!! Could not get OpenGL info"
      glxinfo | grep "OpenGL version" || true
    else
      echo "!! glxinfo not available"
    fi
    echo ""

    echo "[INFO] Verifying PyTorch:"
    python - <<'PY'
    import torch, sys
    print("torch", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
    PY
        echo "----------------------------------------------"
  '';

  # -------------------------------------------------------------------------
  # 5. Helper scripts
  # -------------------------------------------------------------------------
  scripts.start.exec = ''
    uv run python app.py --image cropped-image.png
  '';
}
