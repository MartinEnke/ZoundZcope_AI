# Joblib

[Joblib](https://joblib.readthedocs.io/en/latest/) is a set of tools to provide lightweight pipelining in Python.

### Why Joblib?

- **Efficient Serialization:** Speeds up saving/loading of large numpy arrays and machine learning models.
- **Parallel Processing:** Provides simple helpers for parallelizing tasks.
- **Integration:** Commonly used alongside scikit-learn for model persistence.

### How it's used in this project

- May be used to cache or serialize intermediate audio features or AI model outputs.
- Supports performance optimizations in ML workflows if applicable.
