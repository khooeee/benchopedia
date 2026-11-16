# ARC-AGI-2 redistribution review

## Scope

The snapshot contains all 120 tasks in the ARC-AGI-2 public evaluation set at commit `f3283f727488ad98fe575ea6a5ac981e4a188e49` of arcprize/ARC-AGI-2: every demonstration pair, test input, and test output grid. The public training tasks are not included, and the semi-private and private sets are not published upstream. Both the public repository and the website publish these grids as digits. No code or images are copied. [Public evaluation tasks](https://github.com/arcprize/ARC-AGI-2/tree/f3283f727488ad98fe575ea6a5ac981e4a188e49/data/evaluation)

## Terms

The repository, which contains the task data, carries the Apache License 2.0 with the notice "Copyright 2019 ARC Prize Foundation." Apache 2.0 permits reproduction, redistribution, and public display when recipients receive a copy of the license, copyright notices are retained, and modified files carry notices of the changes. The repository has no NOTICE file. The README asks people developing systems not to look at or tune against the evaluation tasks, to keep evaluations fair; it places no restriction on publishing them, and the repository itself is public. [License](https://github.com/arcprize/ARC-AGI-2/blob/f3283f727488ad98fe575ea6a5ac981e4a188e49/LICENSE) and [README](https://github.com/arcprize/ARC-AGI-2/blob/f3283f727488ad98fe575ea6a5ac981e4a188e49/readme.md)

The technical report describes ARC-AGI-2 tasks as, to the authors' knowledge, entirely novel, and says that tasks already public before ARC-AGI-2 stayed in its public sets. No third-party source for the grids is identified. [Technical report](https://arxiv.org/abs/2505.11831)

## Changes

Benchopedia renders each task's JSON grids as text: demonstration pairs and test inputs as the prompt, and test outputs as the reference answer, each grid as one line of digits per row with its size. It uses upstream task IDs and adds source links. No cell value is changed.

## Notices

The upstream license accompanies this snapshot as LICENSE. Its copyright notice is reproduced below.

```text
Copyright 2019 ARC Prize Foundation.
```
