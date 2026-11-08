# Continue from GitHub

The project is stored in `pedror1beiro/meec`, under
`unidades-curriculares/rsdis/projeto`.

Use `main` for the integrated project. PR #17 added native energy, communication
and the denser map. The final validation and deliverables follow in PR #18.
Build after pulling because message definitions and the C++ energy package changed.

```bash
git clone https://github.com/pedror1beiro/meec.git
cd meec/unidades-curriculares/rsdis/projeto
bash scripts/setup_ubuntu.sh
bash scripts/run_demo.sh
```

For an existing clone, first save any local work, then:

```bash
git fetch origin
git switch main
git pull --ff-only
cd unidades-curriculares/rsdis/projeto
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
bash scripts/run_demo.sh
```

Open `http://localhost:8765` on the simulation PC. Rebuild after pulling this
update: old installed packages do not have the laser bridge or console files.

Always build and launch from the project directory rather than the course root,
which also contains the earlier ROS exercises.

For the first Linux validation, follow `HANDOFF.md`. Run the lightweight sensor
smoke test before trying the optional detailed rover. The report and local checks
explicitly distinguish offline mission rehearsals from actual Gazebo results.
