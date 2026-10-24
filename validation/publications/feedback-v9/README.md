# v9 portable publication amendment

The first v9 commit `2138d50d` passed all tool tests, historical replays, original
business evidence replay and metric/table/gallery recomputation. Its final inventory
check failed on Linux: an intentionally out-of-source-root negative-control **file
symlink** retained an absolute author-machine target. The original inventory treated
every link as an active portable namespace and resolved that target.

The original link, original `ARTIFACTS.json`, tools, designs, production sources,
gates, captures, judgments and scores remain unchanged. The failed run is
[40124485122](https://github.com/KamisamaJin/native-ui-agent/actions/runs/40124485122).
The failure excerpt and exact original root README/workflow are archived here.

The amended verifier hashes an archived file link's **raw target bytes**, without
opening its target or requiring it to exist on the current machine. Directory links
used as live `Sources`/`app` namespaces must still be relative, resolve internally,
and exist. Every original file/link and all sealed dependencies are checked against
the original manifest and literal Git-index blob bytes. Original root files changed
for this amendment are checked through their byte-exact archived copies; current
root files and all amendment files have a separate manifest.

Run the portable publication check with:

```sh
python3 -B validation/publications/feedback-v9/verify.py
```

The original R9 replay and metric commands remain unchanged. This repairs packaging
validation, not a component defect or experimental outcome. CI success confirms
integrity; all four original component self-verification gates remain not accepted.
