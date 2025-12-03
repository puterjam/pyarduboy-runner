#!/usr/bin/env python3
"""
LibRetro Core 下载工具

从 https://buildbot.libretro.com/nightly/ 下载预编译的 libretro 核心
支持多平台和多核心选择
"""
import os
import sys
import platform
import argparse
import urllib.request
import zipfile
import gzip
from pathlib import Path
from typing import Optional, Dict


# LibRetro 官方构建服务器
BUILDBOT_URL = "https://buildbot.libretro.com/nightly"

# 支持的核心列表
SUPPORTED_CORES = {
    "arduous": "Arduous (official Arduboy emulator)",
    "ardens": "Ardens (alternative Arduboy emulator)"
}

# 平台映射
PLATFORM_MAP = {
    "Darwin": {
        "name": "apple/osx/x86_64",
        "arch_alt": "apple/osx/arm64",  # Apple Silicon
        "ext": "dylib.zip"
    },
    "Linux": {
        "name": "linux/x86_64",
        "arch_alt": "linux/armv7-neon-hf",  # Raspberry Pi
        "ext": "so.zip"
    },
    "Windows": {
        "name": "windows/x86_64",
        "arch_alt": "windows/x86",
        "ext": "dll.zip"
    }
}


def detect_platform(verbose: bool = True) -> Dict[str, str]:
    """
    检测当前平台

    Args:
        verbose: 是否打印调试信息

    Returns:
        包含平台信息的字典
    """
    system = platform.system()
    machine = platform.machine().lower()

    if verbose:
        print(f"Detected system: {system}, architecture: {machine}")

    if system not in PLATFORM_MAP:
        raise RuntimeError(f"Unsupported OS: {system}")

    platform_info = PLATFORM_MAP[system].copy()

    # 针对特定架构调整
    if system == "Darwin" and machine in ["arm64", "aarch64"]:
        # Apple Silicon
        platform_info["name"] = platform_info["arch_alt"]
        if verbose:
            print(f"Using Apple Silicon build")
    elif system == "Linux":
        if machine in ["armv7l", "armhf"]:
            # Raspberry Pi 32-bit
            platform_info["name"] = platform_info["arch_alt"]
            if verbose:
                print(f"Using Raspberry Pi ARMv7 build")
        elif machine in ["aarch64", "arm64"]:
            # Raspberry Pi 64-bit or other ARM64
            platform_info["name"] = "linux/aarch64"
            if verbose:
                print(f"Using ARM64 (aarch64) build")
        elif verbose:
            print(f"Using x86_64 build")

    return platform_info


def get_core_download_url(core_name: str, platform_info: Dict[str, str]) -> str:
    """
    构建 core 下载 URL

    Args:
        core_name: 核心名称 (arduous/ardens)
        platform_info: 平台信息字典

    Returns:
        下载 URL
    """
    platform_path = platform_info["name"]
    ext = platform_info["ext"]

    # 构建 URL
    # 格式: https://buildbot.libretro.com/nightly/linux/x86_64/latest/arduous_libretro.so.zip
    url = f"{BUILDBOT_URL}/{platform_path}/latest/{core_name}_libretro.{ext}"

    return url


def download_file(url: str, dest_path: Path, show_progress: bool = True) -> bool:
    """
    下载文件

    Args:
        url: 下载 URL
        dest_path: 目标路径
        show_progress: 是否显示进度

    Returns:
        下载成功返回 True
    """
    try:
        print(f"Downloading from: {url}")

        # 创建目标目录
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # 下载文件
        def reporthook(blocknum, blocksize, totalsize):
            if show_progress and totalsize > 0:
                percent = min(blocknum * blocksize / totalsize * 100, 100)
                sys.stdout.write(f"\rProgress: {percent:.1f}%")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest_path, reporthook if show_progress else None)

        if show_progress:
            print()  # 换行

        print(f"Downloaded to: {dest_path}")
        return True

    except Exception as e:
        print(f"Error downloading file: {e}")
        return False


def extract_core(archive_path: Path, output_dir: Path, core_name: str, platform_info: Dict[str, str]) -> Optional[Path]:
    """
    解压核心文件

    Args:
        archive_path: 压缩包路径
        output_dir: 输出目录
        core_name: 核心名称
        platform_info: 平台信息

    Returns:
        解压后的核心文件路径，失败返回 None
    """
    try:
        ext_map = {
            "dylib.zip": "dylib",
            "so.zip": "so",
            "dll.zip": "dll"
        }

        lib_ext = ext_map.get(platform_info["ext"], "so")
        core_filename = f"{core_name}_libretro.{lib_ext}"
        output_path = output_dir / core_filename

        print(f"Extracting {archive_path.name}...")

        # 解压 zip 文件
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # 查找核心文件
            for member in zip_ref.namelist():
                if member.endswith(core_filename):
                    # 提取文件
                    with zip_ref.open(member) as source:
                        with open(output_path, 'wb') as target:
                            target.write(source.read())

                    print(f"Extracted to: {output_path}")

                    # 设置可执行权限 (Unix-like 系统)
                    if platform.system() != "Windows":
                        os.chmod(output_path, 0o755)

                    return output_path

        print(f"Error: Core file not found in archive")
        return None

    except Exception as e:
        print(f"Error extracting archive: {e}")
        return None


def download_core(core_name: str, output_dir: Optional[Path] = None, platform_override: Optional[str] = None) -> Optional[Path]:
    """
    下载并解压 libretro 核心

    Args:
        core_name: 核心名称 (arduous/ardens)
        output_dir: 输出目录（默认为 ./core）
        platform_override: 平台覆盖（用于交叉下载）

    Returns:
        核心文件路径，失败返回 None
    """
    if core_name not in SUPPORTED_CORES:
        print(f"Error: Unknown core '{core_name}'")
        print(f"Supported cores: {', '.join(SUPPORTED_CORES.keys())}")
        return None

    # 设置输出目录
    if output_dir is None:
        output_dir = Path(__file__).parent / "core"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 检测平台
    if platform_override:
        # 手动指定平台
        if platform_override not in PLATFORM_MAP:
            print(f"Error: Unknown platform '{platform_override}'")
            return None
        platform_info = PLATFORM_MAP[platform_override]
    else:
        platform_info = detect_platform()

    print(f"Platform: {platform_info['name']}")
    print(f"Core: {core_name} - {SUPPORTED_CORES[core_name]}")

    # 构建下载 URL
    download_url = get_core_download_url(core_name, platform_info)

    # 下载文件
    archive_path = output_dir / f"{core_name}_libretro.{platform_info['ext']}"

    if not download_file(download_url, archive_path):
        return None

    # 解压文件
    core_path = extract_core(archive_path, output_dir, core_name, platform_info)

    # 清理压缩包
    if core_path and archive_path.exists():
        print(f"Cleaning up: {archive_path}")
        archive_path.unlink()

    if core_path:
        print(f"\nSuccess! Core installed at: {core_path}")

    return core_path


def list_cores():
    """列出支持的核心"""
    print("Supported Arduboy cores:")
    for core, desc in SUPPORTED_CORES.items():
        print(f"  {core:12} - {desc}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Download libretro cores from official buildbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 下载默认的 arduous core
  python download_core.py arduous

  # 下载 ardens core
  python download_core.py ardens

  # 下载到指定目录
  python download_core.py arduous --output /path/to/cores

  # 列出所有支持的核心
  python download_core.py --list
        """
    )

    parser.add_argument(
        "core",
        nargs="?",
        choices=list(SUPPORTED_CORES.keys()),
        help="Core to download"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output directory (default: ./core)"
    )

    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available cores"
    )

    parser.add_argument(
        "--platform",
        choices=list(PLATFORM_MAP.keys()),
        help="Override platform detection"
    )

    args = parser.parse_args()

    # 列出核心
    if args.list:
        list_cores()
        return 0

    # 需要指定核心
    if not args.core:
        parser.print_help()
        return 1

    # 下载核心
    core_path = download_core(args.core, args.output, args.platform)

    return 0 if core_path else 1


if __name__ == "__main__":
    sys.exit(main())
