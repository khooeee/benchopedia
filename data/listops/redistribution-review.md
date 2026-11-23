# ListOps redistribution review

## Scope

Benchopedia republishes the 10,000 test examples in the `test_d20s.tsv` file
from the authors' original ListOps release at
`1e2805c7b0b327db5d9d78e9b7792ad31678edfa`. Each example contains an expression
of operators and digits and a digit label. The expressions and labels are
synthetic outputs of the project's generator.
[Pinned test file](https://github.com/NYU-MLL/spinn/blob/1e2805c7b0b327db5d9d78e9b7792ad31678edfa/python/spinn/data/listops/test_d20s.tsv) ·
[Generator](https://github.com/NYU-MLL/spinn/blob/1e2805c7b0b327db5d9d78e9b7792ad31678edfa/python/spinn/data/listops/make_data.py)

## Terms

The test data is committed in the authors' repository under New York
University's MIT-style grant. Its public source files require no account or
approval. The grant permits copying and publishing with the copyright and
permission notices intact.
[Pinned license](https://github.com/NYU-MLL/spinn/blob/1e2805c7b0b327db5d9d78e9b7792ad31678edfa/LICENSE.txt) ·
[Paper linking the release](https://aclanthology.org/N18-4013/)

## Changes

Benchopedia drops the binary-tree parentheses, adds operator instructions
and stable keys, and stores the original digit labels as reference answers.
The notices below accompany the tasks on the website and in `LICENSE.txt`.

## Notices

ListOps by Nikita Nangia and Samuel R. Bowman.

```
Copyright 2018, New York University

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


```
