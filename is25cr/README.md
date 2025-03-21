### Make annotations

1. Set the appropriate paths and OpenAI API key in 'make_annotations.py' and 'make_annotations_for_v5.py'
2. Run

### Assess the annotations
1. Configure the environment (a conda environment with r and python packages "conda install r-base r-glmnet r-tidyverse, r-survival, r-stringdist, r-reticulate, numpy, transformers, torch, scikit-learn, pandas")
2. Set the appropriate paths in compare_with_manual_iscr.R)
3. Run compare_with_manual_iscr.R

### See the annotations (manual, LLMs)
They are in the annotations.zip file
