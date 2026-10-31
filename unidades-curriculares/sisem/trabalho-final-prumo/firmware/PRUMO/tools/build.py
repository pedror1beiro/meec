"""Portable independent build, useful before importing into STM32CubeIDE."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDES = [
    "Core/Inc",
    "App",
    "Components",
    "UI",
    "Drivers/STM32F1xx_HAL_Driver/Inc",
    "Drivers/CMSIS/Include",
    "Drivers/CMSIS/Device/ST/STM32F1xx/Include",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toolchain", help="Directory containing arm-none-eabi-gcc")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    prefix = Path(args.toolchain) if args.toolchain else None

    def tool(name):
        command = "arm-none-eabi-" + name + (".exe" if os.name == "nt" else "")
        found = str(prefix / command) if prefix else shutil.which(command)
        if not found or not Path(found).is_file():
            parser.error(
                f"{command} not found: add its bin directory to PATH "
                "or use --toolchain /path/to/bin"
            )
        return found

    gcc, objcopy, size = (tool(n) for n in ["gcc", "objcopy", "size"])
    mode = "Release" if args.release else "Debug"
    out = ROOT / mode
    out.mkdir(exist_ok=True)

    def run(command):
        result = subprocess.run(
            command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.returncode:
            raise SystemExit(result.returncode)
        return result.stdout

    version = run([gcc, "--version"]).splitlines()[0]
    common = [
        "-mcpu=cortex-m3",
        "-mthumb",
        "-mfloat-abi=soft",
        "-g3",
        "-Os" if args.release else "-Og",
        "-ffunction-sections",
        "-fdata-sections",
        "-fno-common",
        "-DSTM32F103xB",
        "-DUSE_HAL_DRIVER",
    ]
    common += ["-I" + p for p in INCLUDES]
    sources = []
    for folder in ["Core/Src", "App", "Components", "UI", "Drivers/STM32F1xx_HAL_Driver/Src"]:
        sources += sorted((ROOT / folder).glob("*.c"))
    objects = []
    for source in sources:
        rel = source.relative_to(ROOT)
        obj = out / rel.with_suffix(".o")
        obj.parent.mkdir(parents=True, exist_ok=True)
        flags = ["-Wall", "-Wextra", "-std=c11", "-fstack-usage"]
        if "Drivers" not in rel.parts and source.name != "system_stm32f1xx.c":
            flags += ["-Werror"]
        run([gcc, *common, *flags, "-c", rel.as_posix(), "-o", str(obj)])
        objects.append(str(obj))
    source = ROOT / "Core/Startup/startup_stm32f103xb.s"
    obj = out / "startup.o"
    run([gcc, *common, "-x", "assembler-with-cpp", "-c", str(source), "-o", str(obj)])
    objects.append(str(obj))
    elf = out / "PRUMO.elf"
    run(
        [
            gcc,
            *common,
            *objects,
            "-TSTM32F103RBTX_FLASH.ld",
            "--specs=nano.specs",
            "--specs=nosys.specs",
            "-Wl,--gc-sections",
            "-Wl,--print-memory-usage",
            "-Wl,-Map=" + str(out / "PRUMO.map"),
            "-Wl,--start-group",
            "-lc",
            "-lm",
            "-lnosys",
            "-Wl,--end-group",
            "-o",
            str(elf),
        ]
    )
    run([objcopy, "-O", "ihex", str(elf), str(out / "PRUMO.hex")])
    run([objcopy, "-O", "binary", str(elf), str(out / "PRUMO.bin")])
    summary = run([size, str(elf)])
    report = {
        "compiler": version,
        "mode": mode,
        "mcu": "STM32F103RBT6",
        "size_output": summary,
        "hardware_tested": False,
        "note": "Compile/link check only. Hardware and debug still require board validation.",
    }
    (out / "build-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Build complete:", elf)


if __name__ == "__main__":
    main()
