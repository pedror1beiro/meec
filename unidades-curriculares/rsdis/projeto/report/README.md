# IEEE paper draft

`main.tex` uses the IEEEtran conference class. The reviewed, two-page draft is
available at `../output/pdf/rsdis_paper_draft.pdf`.

The source describes the implemented prototype, research question, allocation
equations, comparison protocol and limitations. Its Results section is explicitly
pending actual Gazebo experiments. The offline rehearsal values have not been
presented as physical simulation results.

The author block identifies Henrique Correia (1221309), Pedro Ribeiro (1231177)
and Francisco Liquito (1231216). Abstract and keyword labels use colon separators.

Before submission, add measured results,
insert actual Gazebo/RViz screenshots and experimental figures, and update the
conclusions. Follow any paper-length or citation-style instructions supplied by
the lecturers beyond the proposal.

On Ubuntu with a LaTeX toolchain:

```bash
sudo apt-get install latexmk texlive-publishers texlive-latex-recommended texlive-fonts-recommended
cd report
latexmk -pdf main.tex
```

The built-in editor's preview compiler could not start on the Windows authoring
machine. Local MiKTeX successfully compiled the source instead. Both final draft
pages were rendered and visually reviewed; there were no unresolved references,
font substitution warnings or overfull boxes in the final compilation.
