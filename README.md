# Arguebuf

Arguebuf is a format for serializing argument graphs and specified using Protobuf.
The complete specification and documentation is available at the [Buf Schema Registry](https://buf.build/recap/arg-services/docs/main:arg_services.graph.v1).
While Protobuf automatically generates native code for all major programming languages (including Python), we created a custom implementation that provides some additional benefits, including:

- The ability to import existing formats like [AIF](http://www.argumentinterchange.org), [SADFace](https://github.com/Open-Argumentation/SADFace), and a few others.
- Export of Arguebuf graphs to AIF, [NetworkX](https://networkx.org), and [Graphviz](https://graphviz.org).
- Integration with the popular NLP library [spaCy](http://spacy.io).
- Various helper methods to programmatically manipulate/create argument graphs.
- More pythonic interfaces than the regular code generated by `protoc`.

You can easily install the library from [PyPI](https://pypi.org/project/arguebuf/) using pip. The documentation is hosted on [ReadTheDocs](https://arguebuf.readthedocs.io/en/latest/)

## Command Line Interface (CLI)

We also offer some tools to simplify dealing with structured argument graphs.
Among others, it is possible to convert graphs between different formats, translate them, and render images using graphviz.
To use it, install the `cli` extras when installing the package.
When using `pip`, this can be accomplished with

`pip install arguebuf[cli]`

Afterwards, you can execute it by calling `arguebuf`, for example:

`arguebuf --help`