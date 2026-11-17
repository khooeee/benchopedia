# BoolQ redistribution review

## Scope

The snapshot contains all 3,270 labeled development questions, passages, and yes/no answers from google/boolq at revision `35b264d03638db9f4ce671b711558bf7ff0f80d5`. Training examples are excluded. The unlabeled test split is not in this mirror and is not included. Both the public repository and the website publish this development split. [Dataset card](https://huggingface.co/datasets/google/boolq/blob/35b264d03638db9f4ce671b711558bf7ff0f80d5/README.md)

## Terms

The authors' notes release BoolQ under the Creative Commons Attribution-ShareAlike 3.0 license. The pinned dataset card declares the same terms. That grant allows copying and public distribution when attribution is kept, changes are indicated, and the questions and passages remain under the same terms. The authors' storage links require a Google login; anonymous requests did not return the files. This snapshot uses the public mirror, whose development and training counts match the authors' notes. [Authors' notes](https://github.com/google-research-datasets/boolean-questions/blob/90af34107399cc7a446b373dc4ee35b8001da7c2/README.md) and [legal code](https://creativecommons.org/licenses/by-sa/3.0/legalcode)

## Changes

Question and passage text is unchanged. Each prompt places the question before the passage. Boolean answers are stored as yes or no. Row-order IDs and source links were added. The optional page title is not present in the pinned mirror.

## Notices

BoolQ questions, passages, and answers are included from the Google Research release described by Clark, Lee, Chang, Kwiatkowski, Collins, and Toutanova.

This material is shared under the Creative Commons Attribution-ShareAlike 3.0 Unported terms. Adaptations of these examples must remain under those terms. Benchopedia's MIT text does not replace them.

https://creativecommons.org/licenses/by-sa/3.0/
