# Glyphh plugins

Templates for [Ada](https://glyphh.ai), as Claude plugins. Each template is a plain, handwritten plugin: a skill that
tells Claude the steps, the code those steps run, and the specs of the Ada models that decide. The models are your
own, in your own Ada Cloud account: the template makes them, loads examples into them, and from then on they learn
from your answers.

This repository is a Claude plugin marketplace.

```
/plugin marketplace add glyphh-ai/plugins
```

## Templates

| Template | What it decides |
|---|---|
| Resume Screener (`plugins/resume-screener`, in review) | Whether a job application comes from a real person, from independent signals, then how well it fits the role |

## What a template needs

- An Ada Cloud account and the Glyphh connector in Claude (its `ada_*` tools), or the `glyphh` command
  (`pip install glyphh`).
- Whatever its own README names.

## Licence

MIT, see [LICENSE](LICENSE).

Questions: support@glyphh.ai
