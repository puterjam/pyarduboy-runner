#!/bin/bash
set -e

echo ">>> Updating package lists..."
sudo apt-get update

echo ">>> Installing build dependencies..."
sudo apt-get install -y git cmake build-essential python3-pip libsdl2-dev

echo ">>> Installing Python libraries..."
# libretro.py might not be in standard pip, checking...
# If not, we might need to install from git or a specific source.
# For now, assuming it's available or we use a direct git install for the binding if needed.
# Actually, 'libretro.py' on PyPI is the one we want.
pip3 install libretro.py pillow --break-system-packages

echo ">>> Cloning Arduous (Arduboy Libretro Core)..."
if [ -d "arduous" ]; then
    echo "Directory 'arduous' already exists. Pulling latest changes..."
    cd arduous
    git pull
else
    git clone https://github.com/libretro/arduous.git
    cd arduous
fi

echo ">>> Building Arduous Core with optimizations..."
mkdir -p build
cd build

# Configure with Release mode and performance optimizations
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      -DCMAKE_CXX_FLAGS='-O3 -march=native -mtune=native -ffast-math' \
      ..

# Build with multiple cores (4 cores for better performance)
make -j4

echo ">>> Build complete!"
echo "The core is located at: $(pwd)/arduous_libretro.so"

# Copy to core directory for organized storage
echo ">>> Copying core to core/ directory..."
mkdir -p ../../core
cp arduous_libretro.so ../../core/
echo "Core copied to: $(cd ../..; pwd)/core/arduous_libretro.so"
