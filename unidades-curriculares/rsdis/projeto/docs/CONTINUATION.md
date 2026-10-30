# Continue from GitHub

The project is stored in `pedror1beiro/meec`, under
`unidades-curriculares/rsdis/projeto`.

The initial project was merged through PR #13. The navigation, enlarged map and
mission console update is on `rsdis/navigation-world-improvements`. Fetch this
branch on the other PC before its PR is merged:

```bash
git clone --branch rsdis/navigation-world-improvements https://github.com/pedror1beiro/meec.git
cd meec/unidades-curriculares/rsdis/projeto
bash scripts/setup_ubuntu.sh
bash scripts/run_demo.sh
```

For an existing clone, first save any local work, then:

```bash
git fetch origin
git switch --track origin/rsdis/navigation-world-improvements
cd unidades-curriculares/rsdis/projeto
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
bash scripts/run_demo.sh
```

Open `http://localhost:8765` on the simulation PC. Rebuild after pulling this
update: old installed packages do not have the laser bridge or console files.

After the pull request is merged, use `main` instead of the feature branch.
Always build and launch from the project directory rather than the course root,
which also contains the earlier ROS exercises.

For the first Linux validation, follow `HANDOFF.md`. Run the lightweight sensor
smoke test before trying the optional detailed rover. The report and local checks
explicitly distinguish offline mission rehearsals from actual Gazebo results.
