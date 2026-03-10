# skills
Custom skills plus synced third-party skills.

- Local skills live in `skills/`
- Third-party skills are stored directly in `third_party/<name>/`
- `third-skills-metadata.json` records each upstream repo, branch, sparse paths, and the latest synced commit
- `third-skills-sync.sh` pulls only the files and directories listed in `sparse`
