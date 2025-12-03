#!/bin/bash
set -e

# Detect operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo ">>> Detected OS: $OS"

if [ "$OS" == "linux" ]; then
    echo ">>> Updating package lists..."
    sudo apt-get update

    echo ">>> Installing build dependencies..."
    sudo apt-get install -y git cmake build-essential libsdl2-dev
elif [ "$OS" == "mac" ]; then
    echo ">>> Checking Homebrew installation..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    echo ">>> Installing build dependencies..."
    brew install git cmake sdl2 portaudio
fi

# Setup Python virtual environment
echo ">>> Setting up Python virtual environment..."
bash setup_venv.sh

echo ">>> Cloning Arduous (Arduboy Libretro Core)..."
if [ -d "arduous" ]; then
    echo "Directory 'arduous' already exists. Pulling latest changes..."
    cd arduous
    git pull
else
    git clone https://github.com/libretro/arduous.git
    cd arduous
fi

echo ">>> Cloning simavr dependency..."
if [ -d "simavr/.git" ]; then
    echo "simavr already cloned, checking out specific version..."
    cd simavr
    git fetch --unshallow 2>/dev/null || git fetch origin
    git checkout 2f136762ea1e9d7fdd84413c09503ae9920b42cc
    cd ..
else
    echo "Cloning simavr from GitHub (full clone to get specific commit)..."
    rm -rf simavr
    git clone https://github.com/buserror/simavr.git simavr
    cd simavr
    git checkout 2f136762ea1e9d7fdd84413c09503ae9920b42cc
    cd ..
fi

echo ">>> Building Arduous Core with optimizations..."
mkdir -p build
cd build

# Configure with Release mode and performance optimizations
# Add -DCMAKE_POLICY_VERSION_MINIMUM=3.5 for compatibility with CMake 4.x
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
      -DCMAKE_C_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      -DCMAKE_CXX_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      ..

# Build with multiple cores (4 cores for better performance)
make -j4

echo ">>> Build complete!"

# Determine the library extension based on OS
if [ "$OS" == "mac" ]; then
    LIB_EXT="dylib"
else
    LIB_EXT="so"
fi

echo "The core is located at: $(pwd)/arduous_libretro.$LIB_EXT"

# Copy to core directory for organized storage
echo ">>> Copying core to core/ directory..."
mkdir -p ../../core
cp arduous_libretro.$LIB_EXT ../../core/
echo "Core copied to: $(cd ../..; pwd)/core/arduous_libretro.$LIB_EXT"
