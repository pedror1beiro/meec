"""Restore the pinned, minimal STM32CubeF1 dependency set. Python stdlib only."""

import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "firmware" / "PRUMO"
CUBE = "d12e75247d5bcedc734f829b394517ab4c2726e3"
HAL = "fee494a92b5ad331f92ad21f76c66a5cb83773ee"
DEVICE = "c8e9a4a4f16b6d2cb2a2083cbe5161025280fb22"
MODULES = [
    "hal",
    "hal_cortex",
    "hal_dma",
    "hal_flash",
    "hal_flash_ex",
    "hal_gpio",
    "hal_i2c",
    "hal_pwr",
    "hal_rcc",
    "hal_rcc_ex",
    "hal_spi",
    "hal_uart",
]


def read(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PRUMO-dependency-fetcher"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def tree(repo, ref):
    return json.loads(
        read(f"https://api.github.com/repos/STMicroelectronics/{repo}/git/trees/{ref}?recursive=1")
    )["tree"]


def main():
    files = []

    def add(repo, ref, source, dest):
        files.append(
            (f"https://raw.githubusercontent.com/STMicroelectronics/{repo}/{ref}/{source}", dest)
        )

    for item in tree("STM32CubeF1", CUBE):
        p = item["path"]
        if p.startswith("Drivers/CMSIS/Include/") and item["type"] == "blob":
            add("STM32CubeF1", CUBE, p, p)
        elif p == "Drivers/CMSIS/LICENSE.txt":
            add("STM32CubeF1", CUBE, p, p)
    for item in tree("stm32f1xx_hal_driver", HAL):
        p = item["path"]
        if (
            (p.startswith("Inc/") and p.endswith(".h"))
            or p in [f"Src/stm32f1xx_{m}.c" for m in MODULES]
            or p in ["LICENSE.md", "LICENSE", "LICENSE.txt"]
        ):
            add("stm32f1xx_hal_driver", HAL, p, "Drivers/STM32F1xx_HAL_Driver/" + p)
    for p in [
        "Include/stm32f1xx.h",
        "Include/stm32f103xb.h",
        "Include/system_stm32f1xx.h",
        "Source/Templates/system_stm32f1xx.c",
        "Source/Templates/gcc/startup_stm32f103xb.s",
    ]:
        dest = "Drivers/CMSIS/Device/ST/STM32F1xx/" + p
        if p.endswith("system_stm32f1xx.c"):
            dest = "Core/Src/system_stm32f1xx.c"
        if p.endswith(".s"):
            dest = "Core/Startup/startup_stm32f103xb.s"
        add("cmsis_device_f1", DEVICE, p, dest)
    for item in tree("cmsis_device_f1", DEVICE):
        if item["path"].lower() in ["license.md", "license", "license.txt"]:
            add(
                "cmsis_device_f1",
                DEVICE,
                item["path"],
                "Drivers/CMSIS/Device/ST/STM32F1xx/" + item["path"],
            )

    def download(entry):
        url, dest = entry
        content = read(url)
        p = ROOT / dest
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return {
            "path": dest,
            "url": url,
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        manifest = sorted(pool.map(download, files), key=lambda x: x["path"])
    (ROOT / "vendor-manifest.json").write_text(
        json.dumps(
            {"cube_commit": CUBE, "hal_commit": HAL, "device_commit": DEVICE, "files": manifest},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Pinned STM32CubeF1 dependencies restored: {len(manifest)} files")


if __name__ == "__main__":
    main()
