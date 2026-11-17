# SQuAD 2.0 redistribution review

## Scope

The snapshot contains all 11,873 questions in dataset/dev-v2.0.json at commit `eee5fdbf62f8613a7812b03419e6b29617b74fd1` of rajpurkar/SQuAD-explorer, the SQuAD 2.0 development set. For each question it includes the question, the title of its Wikipedia article, the paragraph from that article, and the reference or plausible answers, all English text. The training set, the hidden test set, the website code, and the model predictions in the repository are not included. Both the public repository and the website publish this content. No code or images are copied. [Dataset folder](https://github.com/rajpurkar/SQuAD-explorer/tree/eee5fdbf62f8613a7812b03419e6b29617b74fd1/dataset)

## Terms

The SQuAD website at the pinned commit offers the dataset for download "distributed under the CC BY-SA 4.0 license", and the SQuAD 2.0 paper says the authors release SQuAD 2.0, as with previous versions, under the Creative Commons Attribution-ShareAlike 4.0 license. That license permits copying, redistribution, public display, and adaptation when the work is credited, a link to the license is given, notices are kept, changes are indicated, and adaptations are shared under the same terms. The repository's LICENSE file, added in 2020, is the MIT License, which permits copying and redistribution when its notice is kept. This snapshot follows the dataset's CC BY-SA 4.0 terms and also keeps the MIT notice, beside this review as LICENSE and below. The dataset has no access gate. [Website source](https://github.com/rajpurkar/SQuAD-explorer/blob/eee5fdbf62f8613a7812b03419e6b29617b74fd1/views/index.pug), [SQuAD 2.0 paper](https://arxiv.org/abs/1806.03822), and [LICENSE](https://github.com/rajpurkar/SQuAD-explorer/blob/eee5fdbf62f8613a7812b03419e6b29617b74fd1/LICENSE)

The paragraphs are text from English Wikipedia articles, and the questions and answers were written by crowdworkers hired by the authors. Wikipedia text is shared under CC BY-SA, and Wikipedia's reuse guidance accepts a link to the article as credit to its contributors. Earlier CC BY-SA versions allow adaptations under version 4.0, so publishing the paragraphs under CC BY-SA 4.0 is consistent with Wikipedia's terms. Every record names its source article, and each task prompt keeps that title. SQuAD does not record the article revisions the paragraphs were taken from, so the articles are credited by title and current link; four titles, such as Huguenot, now redirect to renamed articles. No other third-party content was found. [SQuAD 1.1 paper](https://arxiv.org/abs/1606.05250) and [Wikipedia's reuse terms](https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content)

## Changes

Benchopedia assembles each task prompt from the question, a line naming the source article, and the paragraph. For answerable questions it lists each distinct reference answer once, without character offsets. For unanswerable questions it writes Unanswerable and labels the plausible answer as incorrect. It uses the upstream question IDs and adds source links. Question, paragraph, and answer text is unchanged.

## Notices

SQuAD 2.0 is from "Know What You Don't Know: Unanswerable Questions for SQuAD" by Pranav Rajpurkar, Robin Jia, and Percy Liang. Its answerable questions and paragraphs are from "SQuAD: 100,000+ Questions for Machine Comprehension of Text" by Pranav Rajpurkar, Jian Zhang, Konstantin Lopyrev, and Percy Liang. The questions and answers were written by crowdworkers.

The paragraphs are from these English Wikipedia articles by Wikipedia contributors: [Normans](https://en.wikipedia.org/wiki/Normans), [Computational complexity theory](https://en.wikipedia.org/wiki/Computational_complexity_theory), [Southern California](https://en.wikipedia.org/wiki/Southern_California), [Sky (United Kingdom)](https://en.wikipedia.org/wiki/Sky_%28United_Kingdom%29), [Victoria (Australia)](https://en.wikipedia.org/wiki/Victoria_%28Australia%29), [Huguenot](https://en.wikipedia.org/wiki/Huguenot), [Steam engine](https://en.wikipedia.org/wiki/Steam_engine), [Oxygen](https://en.wikipedia.org/wiki/Oxygen), [1973 oil crisis](https://en.wikipedia.org/wiki/1973_oil_crisis), [European Union law](https://en.wikipedia.org/wiki/European_Union_law), [Amazon rainforest](https://en.wikipedia.org/wiki/Amazon_rainforest), [Ctenophora](https://en.wikipedia.org/wiki/Ctenophora), [Fresno, California](https://en.wikipedia.org/wiki/Fresno,_California), [Packet switching](https://en.wikipedia.org/wiki/Packet_switching), [Black Death](https://en.wikipedia.org/wiki/Black_Death), [Geology](https://en.wikipedia.org/wiki/Geology), [Pharmacy](https://en.wikipedia.org/wiki/Pharmacy), [Civil disobedience](https://en.wikipedia.org/wiki/Civil_disobedience), [Construction](https://en.wikipedia.org/wiki/Construction), [Private school](https://en.wikipedia.org/wiki/Private_school), [Harvard University](https://en.wikipedia.org/wiki/Harvard_University), [Jacksonville, Florida](https://en.wikipedia.org/wiki/Jacksonville,_Florida), [Economic inequality](https://en.wikipedia.org/wiki/Economic_inequality), [University of Chicago](https://en.wikipedia.org/wiki/University_of_Chicago), [Yuan dynasty](https://en.wikipedia.org/wiki/Yuan_dynasty), [Immune system](https://en.wikipedia.org/wiki/Immune_system), [Intergovernmental Panel on Climate Change](https://en.wikipedia.org/wiki/Intergovernmental_Panel_on_Climate_Change), [Prime number](https://en.wikipedia.org/wiki/Prime_number), [Rhine](https://en.wikipedia.org/wiki/Rhine), [Scottish Parliament](https://en.wikipedia.org/wiki/Scottish_Parliament), [Islamism](https://en.wikipedia.org/wiki/Islamism), [Imperialism](https://en.wikipedia.org/wiki/Imperialism), [Warsaw](https://en.wikipedia.org/wiki/Warsaw), [French and Indian War](https://en.wikipedia.org/wiki/French_and_Indian_War), and [Force](https://en.wikipedia.org/wiki/Force).

This material is shared under the [Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Adaptations of these questions, paragraphs, and answers must remain under those terms. Benchopedia's MIT license does not replace them.

The repository's license notice is reproduced below.

```text
MIT License

Copyright (c) 2020 Pranav Rajpurkar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
