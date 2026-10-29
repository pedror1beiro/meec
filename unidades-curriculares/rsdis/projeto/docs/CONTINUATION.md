# Continue from GitHub

The project is stored in `pedror1beiro/meec`, under
`unidades-curriculares/rsdis/projeto`.

The initial publication uses the branch `rsdis/lunar-exploration` and a pull
request to `main`, following the repository's contribution workflow. Before that
pull request is merged, fetch this branch on the other PC:

```bash
git clone --branch rsdis/lunar-exploration https://github.com/pedror1beiro/meec.git
cd meec/unidades-curriculares/rsdis/projeto
bash scripts/setup_ubuntu.sh
bash scripts/run_demo.sh
```

After the pull request is merged, use `main` instead of the feature branch.
Always build and launch from the project directory rather than the course root,
which also contains the earlier ROS exercises.

For the first Linux validation, follow `HANDOFF.md`. Run the lightweight sensor
smoke test before trying the optional detailed rover. The report and local checks
explicitly distinguish offline mission rehearsals from actual Gazebo results.
